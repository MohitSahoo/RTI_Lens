import hashlib
import os

def calculate_sha256(file_path):
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def calculate_text_hash(text):
    """Calculate SHA256 hash of a text string."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()
