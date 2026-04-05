"""
ML Prediction Endpoint
"""
from fastapi import APIRouter, HTTPException
import pickle
import json
import pandas as pd
from pathlib import Path
from backend.config import MODEL_PATH, MODEL_CARD_PATH
from backend.schemas import PredictRequest, PredictResponse

router = APIRouter(prefix="/api", tags=["predict"])

# Load model and model card at startup
model = None
model_card = None

def load_model():
    global model, model_card
    if model is None:
        model_path = Path(MODEL_PATH)
        card_path = Path(MODEL_CARD_PATH)

        if not model_path.exists():
            raise FileNotFoundError(f"Model not found at {MODEL_PATH}")
        if not card_path.exists():
            raise FileNotFoundError(f"Model card not found at {MODEL_CARD_PATH}")

        with open(model_path, "rb") as f:
            model = pickle.load(f)

        with open(card_path, "r") as f:
            model_card = json.load(f)

@router.post("/predict", response_model=PredictResponse)
async def predict_outcome(request: PredictRequest):
    """
    Predict appeal outcome using trained ML model
    """
    load_model()

    # Prepare input data
    year = request.order_date.year if request.order_date else 2024

    input_data = pd.DataFrame([{
        'ministry': request.ministry,
        'section_cited': request.section_cited,
        'appeal_level': request.appeal_level,
        'year': year,
        'raw_text': request.raw_text
    }])

    try:
        # Get prediction and probability
        prediction = model.predict(input_data)[0]
        probabilities = model.predict_proba(input_data)[0]

        # Map prediction to outcome
        outcome = "allowed" if prediction == 1 else "denied"
        probability = float(probabilities[1] if prediction == 1 else probabilities[0])

        # Determine confidence level
        if probability >= 0.8:
            confidence = "high"
        elif probability >= 0.6:
            confidence = "medium"
        else:
            confidence = "low"

        # Check if ministry has low training data
        from sqlalchemy import create_engine, text
        from backend.config import DATABASE_URL

        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            ministry_count = conn.execute(
                text("SELECT COUNT(*) FROM cases WHERE ministry_id = (SELECT id FROM ministries WHERE name = :ministry)"),
                {"ministry": request.ministry}
            ).scalar() or 0

        low_data_threshold = model_card.get("low_data_threshold", 10)
        low_data_warning = ministry_count < low_data_threshold

        return PredictResponse(
            prediction=outcome,
            probability=probability,
            confidence=confidence,
            disclaimer=model_card.get("disclaimer", "This prediction is based on historical data and is not legal advice."),
            low_data_warning=low_data_warning,
            model_card=model_card
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")
