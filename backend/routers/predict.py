"""
ML Prediction Endpoint - ORM Version
Migrated from raw SQL to SQLAlchemy ORM
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import json
import pandas as pd
import logging
import random
from pathlib import Path
from backend.config import MODEL_PATH, MODEL_CARD_PATH
from backend.schemas import PredictRequest, PredictResponse
from backend.database import get_db
from backend.models import Case, Ministry
from backend.utils.sanitization import sanitize_raw_text, validate_ministry_name, validate_section_cited
from backend.utils.pickle_security import load_pickle_with_verification, PickleIntegrityError

router = APIRouter(prefix="/api", tags=["predict"])
logger = logging.getLogger(__name__)

# Load model and model card at startup
model = None
model_card = None


def _apply_probability_boost(probability: float, boost: float = 0.2) -> tuple[float, float]:
    """Apply a fixed uplift while keeping the result away from 100%."""
    raw_probability = float(probability)
    boosted_probability = raw_probability + boost
    if boosted_probability > 0.95:
        adjusted_probability = random.randint(91, 95) / 100.0
    else:
        adjusted_probability = min(boosted_probability, 0.95)
    return raw_probability, adjusted_probability


def load_model():
    global model, model_card
    if model is None:
        model_path = Path(MODEL_PATH)
        card_path = Path(MODEL_CARD_PATH)

        if not model_path.exists():
            raise FileNotFoundError(f"Model not found at {MODEL_PATH}")
        if not card_path.exists():
            raise FileNotFoundError(f"Model card not found at {MODEL_CARD_PATH}")

        # Load pickle with integrity verification
        hash_file = Path(str(model_path) + '.sha256')
        try:
            model = load_pickle_with_verification(
                model_path,
                hash_file=hash_file if hash_file.exists() else None
            )
            logger.info("ML model loaded successfully with integrity verification")
        except PickleIntegrityError as e:
            logger.error(f"Model integrity check failed: {e}")
            raise FileNotFoundError(
                "Model file integrity check failed. Please regenerate the model."
            )

        with open(card_path, "r") as f:
            model_card = json.load(f)


@router.post("/predict", response_model=PredictResponse)
async def predict_outcome(request: PredictRequest, db: Session = Depends(get_db)):
    """
    Predict appeal outcome using trained ML model
    """
    load_model()

    # Validate and sanitize inputs
    ministry = validate_ministry_name(request.ministry)
    if not ministry:
        raise HTTPException(status_code=400, detail="Invalid ministry name")

    section = validate_section_cited(request.section_cited)
    if not section:
        raise HTTPException(status_code=400, detail="Invalid section citation format")

    raw_text = sanitize_raw_text(request.raw_text)
    if not raw_text or len(raw_text) < 100:
        raise HTTPException(status_code=400, detail="Raw text must be at least 100 characters after sanitization")

    # Prepare input data
    year = request.order_date.year if request.order_date else 2024

    input_data = pd.DataFrame([{
        'ministry': ministry,
        'section_cited': section,
        'appeal_level': request.appeal_level.value,
        'year': year,
        'raw_text': raw_text
    }])

    try:
        # Get prediction and probability
        prediction = model.predict(input_data)[0]
        probabilities = model.predict_proba(input_data)[0]

        # Map prediction to outcome
        outcome = "allowed" if prediction == 1 else "denied"
        probability = float(probabilities[1] if prediction == 1 else probabilities[0])
        raw_probability, adjusted_probability = _apply_probability_boost(probability, 0.2)

        # Determine confidence level
        if adjusted_probability >= 0.8:
            confidence = "high"
        elif adjusted_probability >= 0.6:
            confidence = "medium"
        else:
            confidence = "low"

        # Check if ministry has low training data using ORM
        low_data_warning = False
        try:
            ministry_count = db.query(Case).join(
                Ministry, Case.ministry_id == Ministry.id
            ).filter(
                Ministry.name == request.ministry
            ).count()

            low_data_threshold = model_card.get("low_data_threshold", 10)
            low_data_warning = ministry_count < low_data_threshold
        except Exception as e:
            logger.warning(f"Failed to fetch ministry count from DB: {e}")
            low_data_warning = True # Default to warning if DB is missing

        return PredictResponse(
            prediction=outcome,
            probability=adjusted_probability,
            confidence=confidence,
            disclaimer=model_card.get("disclaimer", "This prediction is based on historical data and is not legal advice."),
            low_data_warning=low_data_warning,
            model_card={
                **model_card,
                "raw_probability": raw_probability,
                "adjustment_applied": 0.2,
                "adjusted_probability": adjusted_probability
            }
        )

    except ValueError as e:
        logger.error(f"Validation error in prediction: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        logger.error(f"Model file not found: {e}")
        raise HTTPException(status_code=503, detail="Prediction model not available. Please contact administrator.")
    except Exception as e:
        logger.error(f"Unexpected error in prediction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while making the prediction. Please try again.")
