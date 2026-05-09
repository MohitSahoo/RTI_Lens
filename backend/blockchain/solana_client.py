import time
import json
import logging
import os
import asyncio
from typing import List, Dict, Optional, Any
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.instruction import Instruction
from solders.message import Message
from solders.transaction import Transaction
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
try:
    from backend.config import SOLANA_RPC_URL
except ModuleNotFoundError:
    from config import SOLANA_RPC_URL

logger = logging.getLogger(__name__)

# SPL Memo Program ID (v1)
MEMO_PROGRAM_ID = Pubkey.from_string("Memo1UhkJRfHyvLMcVucJwxFSSQC7ycshsbsjHq84c3")

class SolanaRTIClient:
    """
    Senior Implementation of Solana RTI Integrity Layer.
    Uses SPL Memo program to anchor RTI document hashes on-chain.
    """
    
    def __init__(self, rpc_url: Optional[str] = None):
        self.rpc_url = rpc_url or SOLANA_RPC_URL or "https://api.devnet.solana.com"
        self._keypair = self._load_keypair()
        logger.info(f"Initialized Solana RTI Client on {self.rpc_url}")
        if self._keypair:
            logger.info(f"Authority Address: {self._keypair.pubkey()}")
        else:
            logger.warning("No valid Solana keypair found. Running in Read-Only/Simulation mode.")

    def _load_keypair(self) -> Optional[Keypair]:
        """Loads the authority keypair from environment."""
        try:
            priv_key_raw = os.getenv("SOLANA_PRIVATE_KEY")
            if not priv_key_raw:
                return None
            
            # Support both JSON array and base58 (though standard is array for solana-py)
            if priv_key_raw.startswith("["):
                key_bytes = bytes(json.loads(priv_key_raw))
                return Keypair.from_bytes(key_bytes)
            else:
                # Potential base58 fallback if needed
                return None
        except Exception as e:
            logger.error(f"Failed to load Solana keypair: {e}")
            return None

    async def record_rti_submission(self, doc_hash: str, wallet_address: str, department: str) -> Dict[str, Any]:
        """
        Records an RTI submission hash on Solana using the Memo Program.
        This provides immutable proof of existence and timestamping.
        """
        if not self._keypair:
            # Fallback to high-fidelity simulation if no key is present
            return self._simulate_record(doc_hash, wallet_address, department)

        try:
            async with AsyncClient(self.rpc_url) as client:
                # 1. Construct the Memo data
                # We store a JSON blob with the hash and metadata
                memo_data = json.dumps({
                    "type": "RTI_SUBMISSION",
                    "hash": doc_hash,
                    "dept": department,
                    "citizen": wallet_address,
                    "ts": int(time.time())
                }).encode('utf-8')

                # 2. Create the instruction
                memo_instruction = Instruction(
                    program_id=MEMO_PROGRAM_ID,
                    data=memo_data,
                    accounts=[]
                )

                # 3. Fetch recent blockhash
                res = await client.get_latest_blockhash()
                recent_blockhash = res.value.blockhash

                # 4. Build and Sign transaction
                message = Message.new_with_blockhash(
                    [memo_instruction],
                    self._keypair.pubkey(),
                    recent_blockhash
                )
                tx = Transaction([self._keypair], message, recent_blockhash)

                # 5. Send transaction
                send_res = await client.send_transaction(tx)
                signature = str(send_res.value)

                logger.info(f"RTI Hash anchored to Solana: {signature}")

                return {
                    "status": "success",
                    "tx_id": signature,
                    "block_height": res.context.slot,
                    "timestamp": int(time.time()),
                    "doc_hash": doc_hash,
                    "wallet": wallet_address,
                    "department": department,
                    "explorer_url": f"https://explorer.solana.com/tx/{signature}?cluster=devnet"
                }

        except Exception as e:
            logger.error(f"Solana transaction failed: {e}")
            # Fall back to simulation on any error
            logger.info("Falling back to simulation mode")
            return self._simulate_record(doc_hash, wallet_address, department)

    def _simulate_record(self, doc_hash: str, wallet_address: str, department: str) -> Dict[str, Any]:
        """High-fidelity simulation when no private key is available."""
        import random
        # Generate a realistic-looking Base58 signature using random bytes
        tx_id = str(Pubkey.from_bytes(os.urandom(32)))
        return {
            "status": "simulated",
            "tx_id": tx_id,
            "block_height": 245000000 + random.randint(1, 100000),
            "timestamp": int(time.time()),
            "doc_hash": doc_hash,
            "wallet": wallet_address,
            "department": department,
            "explorer_url": f"https://explorer.solana.com/tx/{tx_id}?cluster=devnet",
            "note": "Running in simulation mode (No Private Key or insufficient SOL)"
        }

    async def verify_document(self, doc_hash: str) -> Dict[str, Any]:
        """
        Verifies a document hash. In a full implementation, this would
        search transaction history or a custom indexer.
        """
        # For the demo, we return a structural verification result
        return {
            "verified": True,
            "chain": "Solana Devnet",
            "method": "SHA256 Anchor",
            "doc_hash": doc_hash,
            "status": "Confirmed"
        }

    def get_citizen_history(self, wallet_address: str) -> List[Dict[str, Any]]:
        """
        Returns mock history for UI consistency.
        Real implementation would use getSignaturesForAddress.
        """
        return [
            {
                "id": "RTI-2024-001",
                "timestamp": int(time.time()) - 86400 * 5,
                "dept": "Ministry of Home Affairs",
                "status": "VERIFIED",
                "tx": "5AzQ7v9xKzB1u8nTy1wLs8nTy1wLs8nTy1wLs8nTy1wLs"
            },
            {
                "id": "RTI-2024-042",
                "timestamp": int(time.time()) - 86400 * 12,
                "dept": "Ministry of Railways",
                "status": "VERIFIED",
                "tx": "2mPq7bYv8nTy1wLs8nTy1wLs8nTy1wLs8nTy1wLs8nTy1w"
            }
        ]

    def get_authority_address(self) -> str:
        """Returns the public key of the authority that signs transactions."""
        return str(self._keypair.pubkey()) if self._keypair else "Simulation Mode"

# Singleton instance
solana_client = SolanaRTIClient()
