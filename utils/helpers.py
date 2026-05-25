import os
import shutil
import logging
from typing import List

# Setup simple logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TEMP_DIR = "temp"
MAX_FILE_SIZE_MB = 200 # 200 MB limit

def setup_directories():
    """Ensure necessary directories exist."""
    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs("uploads", exist_ok=True)

def cleanup_temp_files():
    """Removes all files in the temporary directory."""
    try:
        if os.path.exists(TEMP_DIR):
            for filename in os.listdir(TEMP_DIR):
                filepath = os.path.join(TEMP_DIR, filename)
                if os.path.isfile(filepath) or os.path.islink(filepath):
                    os.unlink(filepath)
                elif os.path.isdir(filepath):
                    shutil.rmtree(filepath)
        logger.info("Temporary files cleaned up.")
    except Exception as e:
        logger.error(f"Error during temp cleanup: {e}")

def validate_file_size(file_size_bytes: int) -> bool:
    """Check if file size is within limits."""
    size_mb = file_size_bytes / (1024 * 1024)
    return size_mb <= MAX_FILE_SIZE_MB

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Splits text into overlapping chunks for large context processing.
    """
    if not text:
        return []
        
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
        
    return chunks
