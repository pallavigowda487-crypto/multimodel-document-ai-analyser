import pytesseract
from PIL import Image
import logging

logger = logging.getLogger(__name__)

def extract_text_from_image(file_path: str) -> str:
    """
    Extracts text from an image using Tesseract OCR.
    """
    text = ""
    try:
        # Open the image file
        with Image.open(file_path) as img:
            # Do OCR
            text = pytesseract.image_to_string(img)
    except Exception as e:
        logger.error(f"Error extracting text from image: {e}")
    return text.strip()

def process_image(file_path: str, file_type: str) -> str:
    """Routing function for image processing."""
    return extract_text_from_image(file_path)
