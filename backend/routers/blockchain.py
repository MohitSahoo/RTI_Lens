from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
import os
from ..blockchain.solana_client import solana_client
from ..blockchain.hash_service import calculate_sha256, calculate_text_hash
from ..blockchain.encryption_service import encryption_service
import time

router = APIRouter(prefix="/api/blockchain", tags=["blockchain"])

class BlockchainRecord(BaseModel):
    id: str
    timestamp: int
    dept: str
    status: str
    tx: str

class VerificationResponse(BaseModel):
    verified: bool
    tx_id: str
    timestamp: int
    doc_hash: str
    department: str

@router.post("/submit")
async def submit_to_blockchain(
    wallet: str = Form(...),
    department: str = Form(...),
    content: str = Form(None),
    file: UploadFile = File(None)
):
    """
    Submits an RTI document hash to the Solana blockchain.
    """
    try:
        if file:
            # Save temporary file to calculate hash
            temp_path = f"temp_{file.filename}"
            with open(temp_path, "wb") as f:
                f.write(await file.read())
            doc_hash = calculate_sha256(temp_path)
            os.remove(temp_path)
        elif content:
            doc_hash = calculate_text_hash(content)
        else:
            raise HTTPException(status_code=400, detail="No content or file provided")

        result = await solana_client.record_rti_submission(doc_hash, wallet, department)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{wallet}", response_model=List[BlockchainRecord])
async def get_history(wallet: str):
    """
    Returns the immutable history of RTI filings for a specific wallet.
    """
    return solana_client.get_citizen_history(wallet)

@router.get("/verify/{doc_hash}")
async def verify_doc(doc_hash: str):
    """
    Verifies a document hash against the blockchain records.
    """
    return await solana_client.verify_document(doc_hash)

@router.get("/authority-key")
async def get_authority_key():
    """Returns the public key of the Solana authority signing the RTI memos."""
    return {"public_key": solana_client.get_authority_address()}

# --- Encryption & Simulation Endpoints ---

@router.get("/gov/public-key")
async def get_gov_public_key():
    """Returns the Government's public key for citizens to use."""
    return {"public_key": encryption_service.get_public_key_pem()}

@router.post("/gov/encrypt")
async def encrypt_data(data: str = Form(...)):
    """Simulates the citizen encrypting data for the government."""
    encrypted = encryption_service.encrypt_for_government(data)
    return {"encrypted_data": encrypted}

@router.post("/gov/decrypt")
async def decrypt_data(encrypted_data: str = Form(...)):
    """Simulates the government decrypting the data using their private key."""
    try:
        decrypted = encryption_service.decrypt_as_government(encrypted_data)
        return {"decrypted_data": decrypted}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Decryption failed. Invalid key or data.")

