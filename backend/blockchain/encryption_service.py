"""
RTI Hybrid Encryption Service (RSA-2048 + AES-256-GCM)
======================================================
Industry-standard hybrid encryption for arbitrary-length RTI documents.

Flow:
  1. Citizen generates a random AES-256 session key.
  2. Document is encrypted with AES-256-GCM (no size limit, authenticated).
  3. The AES session key is encrypted with Government's RSA-2048 public key.
  4. Both encrypted_key + encrypted_document are bundled and sent.

  5. Government decrypts the AES session key using their RSA private key.
  6. Government decrypts the full document using the recovered AES key.
"""

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import base64
import json
import os


class RTIEncryptionService:
    """
    Hybrid RSA+AES encryption service for secure RTI document transfer.
    Supports arbitrary-length documents (PDFs, text, any binary).
    """

    def __init__(self):
        self._gov_private_key = None
        self._gov_public_key = None
        self.generate_gov_keys()

    def generate_gov_keys(self):
        """Generate a new RSA-2048 key pair for the Government simulation."""
        self._gov_private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self._gov_public_key = self._gov_private_key.public_key()

    def get_public_key_pem(self) -> str:
        """Returns the Government's public key in PEM format."""
        return self._gov_public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')

    def encrypt_for_government(self, message: str) -> str:
        """
        Hybrid Encryption (Citizen → Government):
          1. Generate random AES-256 key (32 bytes) + nonce (12 bytes)
          2. Encrypt the full message with AES-256-GCM
          3. Encrypt the AES key with RSA-OAEP
          4. Bundle everything as a base64-encoded JSON envelope
        """
        # Step 1: Generate ephemeral AES-256 key
        aes_key = os.urandom(32)  # 256-bit key
        nonce = os.urandom(12)     # 96-bit nonce for GCM

        # Step 2: Encrypt the document with AES-256-GCM (no size limit)
        aesgcm = AESGCM(aes_key)
        encrypted_document = aesgcm.encrypt(nonce, message.encode('utf-8'), None)

        # Step 3: Encrypt the AES key with RSA-OAEP (only 32 bytes → fits easily)
        encrypted_aes_key = self._gov_public_key.encrypt(
            aes_key,
            asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        # Step 4: Create a secure envelope
        envelope = {
            "v": 2,  # Envelope version (hybrid)
            "encrypted_key": base64.b64encode(encrypted_aes_key).decode('utf-8'),
            "nonce": base64.b64encode(nonce).decode('utf-8'),
            "ciphertext": base64.b64encode(encrypted_document).decode('utf-8'),
        }

        return base64.b64encode(json.dumps(envelope).encode('utf-8')).decode('utf-8')

    def decrypt_as_government(self, encrypted_bundle: str) -> str:
        """
        Hybrid Decryption (Government):
          1. Decode the envelope
          2. Decrypt the AES key using RSA private key
          3. Decrypt the full document using AES-256-GCM
        """
        # Step 1: Decode the outer envelope
        envelope_json = base64.b64decode(encrypted_bundle)
        envelope = json.loads(envelope_json)

        # Version check
        if envelope.get("v") != 2:
            raise ValueError("Unsupported encryption envelope version")

        # Step 2: Decrypt the AES session key with RSA
        encrypted_aes_key = base64.b64decode(envelope["encrypted_key"])
        aes_key = self._gov_private_key.decrypt(
            encrypted_aes_key,
            asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        # Step 3: Decrypt the full document with AES-256-GCM
        nonce = base64.b64decode(envelope["nonce"])
        ciphertext = base64.b64decode(envelope["ciphertext"])

        aesgcm = AESGCM(aes_key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)

        return plaintext.decode('utf-8')


# Singleton instance for simulation
encryption_service = RTIEncryptionService()
