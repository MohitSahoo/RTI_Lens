"""
Pickle file integrity verification for security
Prevents arbitrary code execution from tampered pickle files
"""
import hashlib
import pickle
from pathlib import Path
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class PickleIntegrityError(Exception):
    """Raised when pickle file integrity check fails"""
    pass


def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA256 hash of a file

    Args:
        file_path: Path to file

    Returns:
        Hex string of SHA256 hash
    """
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def load_pickle_with_verification(
    file_path: Path,
    expected_hash: Optional[str] = None,
    hash_file: Optional[Path] = None
) -> Any:
    """
    Load pickle file with integrity verification

    Args:
        file_path: Path to pickle file
        expected_hash: Expected SHA256 hash (hex string)
        hash_file: Path to file containing expected hash

    Returns:
        Unpickled object

    Raises:
        FileNotFoundError: If pickle file doesn't exist
        PickleIntegrityError: If hash verification fails
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Pickle file not found: {file_path}")

    # Get expected hash from file if provided
    if hash_file and hash_file.exists():
        with open(hash_file, 'r') as f:
            expected_hash = f.read().strip()

    # Compute actual hash
    actual_hash = compute_file_hash(file_path)

    # Verify if expected hash provided
    if expected_hash:
        if actual_hash != expected_hash:
            logger.error(
                f"Pickle integrity check failed for {file_path}\n"
                f"Expected: {expected_hash}\n"
                f"Actual: {actual_hash}"
            )
            raise PickleIntegrityError(
                f"Pickle file integrity check failed: {file_path.name}. "
                f"File may have been tampered with. "
                f"Run scripts to regenerate the file."
            )
        logger.info(f"Pickle integrity verified: {file_path.name}")
    else:
        logger.warning(
            f"Loading pickle without integrity check: {file_path.name}. "
            f"Hash: {actual_hash}"
        )

    # Load pickle file
    with open(file_path, 'rb') as f:
        return pickle.load(f)


def save_pickle_with_hash(
    obj: Any,
    file_path: Path,
    hash_file: Optional[Path] = None
) -> str:
    """
    Save object as pickle and generate hash file

    Args:
        obj: Object to pickle
        file_path: Path to save pickle file
        hash_file: Path to save hash file (defaults to {file_path}.sha256)

    Returns:
        SHA256 hash of saved file
    """
    # Save pickle
    with open(file_path, 'wb') as f:
        pickle.dump(obj, f)

    # Compute hash
    file_hash = compute_file_hash(file_path)

    # Save hash file
    if hash_file is None:
        hash_file = Path(str(file_path) + '.sha256')

    with open(hash_file, 'w') as f:
        f.write(file_hash)

    logger.info(f"Saved pickle with hash: {file_path.name} ({file_hash[:16]}...)")

    return file_hash


def verify_all_pickle_files(pickle_dir: Path) -> Dict[str, bool]:
    """
    Verify integrity of all pickle files in directory

    Args:
        pickle_dir: Directory containing pickle files

    Returns:
        Dict mapping filename to verification status (True = verified, False = failed)
    """
    results = {}

    for pickle_file in pickle_dir.glob("*.pkl"):
        hash_file = Path(str(pickle_file) + '.sha256')

        if not hash_file.exists():
            logger.warning(f"No hash file for {pickle_file.name}")
            results[pickle_file.name] = False
            continue

        try:
            load_pickle_with_verification(pickle_file, hash_file=hash_file)
            results[pickle_file.name] = True
        except PickleIntegrityError:
            results[pickle_file.name] = False

    return results
