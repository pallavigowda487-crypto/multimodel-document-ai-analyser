import PyPDF2
import docx
import logging

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_path: str) -> str:
    """Extracts text from a PDF file."""
    text = ""
    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
    return text.strip()

def extract_text_from_docx(file_path: str) -> str:
    """Extracts text from a Word document."""
    text = ""
    try:
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {e}")
    return text.strip()

def extract_text_from_txt(file_path: str) -> str:
    """Extracts text from a plain text file."""
    text = ""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        logger.error(f"Error extracting text from TXT: {e}")
    return text.strip()

def process_document(file_path: str, file_type: str) -> str:
    """Routing function for document processing."""
    file_type = file_type.lower()
    if file_type == "pdf":
        return extract_text_from_pdf(file_path)
    elif file_type == "docx" or file_type == "vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_text_from_docx(file_path)
    elif file_type == "txt" or file_type == "plain":
        return extract_text_from_txt(file_path)
    else:
        logger.warning(f"Unsupported document type: {file_type}")
        return ""
