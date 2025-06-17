import base64
import io
from typing import Tuple, Optional
import logging
from pypdf import PdfReader
from docx import Document
import re

logger = logging.getLogger(__name__)

class FileProcessor:
    """Service for processing uploaded resume files"""
    
    @staticmethod
    def decode_base64_file(file_content: str, file_type: str) -> bytes:
        """Decode base64 file content to bytes"""
        try:
            return base64.b64decode(file_content)
        except Exception as e:
            logger.error(f"Failed to decode base64 content: {e}")
            raise ValueError("Invalid base64 file content")
    
    @staticmethod
    def extract_text_from_pdf(file_bytes: bytes) -> str:
        """Extract text from PDF file"""
        try:
            pdf_stream = io.BytesIO(file_bytes)
            reader = PdfReader(pdf_stream)
            
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            
            return text.strip()
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            raise ValueError("Failed to process PDF file")
    
    @staticmethod
    def extract_text_from_docx(file_bytes: bytes) -> str:
        """Extract text from Word document"""
        try:
            doc_stream = io.BytesIO(file_bytes)
            doc = Document(doc_stream)
            
            text = ""
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text += paragraph.text + "\n"
            
            # Also extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            text += cell.text + "\n"
            
            return text.strip()
        except Exception as e:
            logger.error(f"Failed to extract text from DOCX: {e}")
            raise ValueError("Failed to process Word document")
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize extracted text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\-\.\,\(\)\@\:\;]', ' ', text)
        
        # Remove excessive newlines
        text = re.sub(r'\n+', '\n', text)
        
        return text.strip()
    
    @classmethod
    def process_resume_file(cls, file_content: str, file_type: str, filename: Optional[str] = None) -> Tuple[str, bytes]:
        """
        Process uploaded resume file and extract text
        
        Args:
            file_content: Base64 encoded file content
            file_type: File type ('pdf' or 'docx')
            filename: Original filename (optional)
        
        Returns:
            Tuple of (extracted_text, original_file_bytes)
        """
        if file_type.lower() not in ['pdf', 'docx']:
            raise ValueError("Unsupported file type. Only PDF and DOCX are supported.")
        
        # Decode file
        file_bytes = cls.decode_base64_file(file_content, file_type)
        
        # Extract text based on file type
        if file_type.lower() == 'pdf':
            text = cls.extract_text_from_pdf(file_bytes)
        elif file_type.lower() == 'docx':
            text = cls.extract_text_from_docx(file_bytes)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        # Clean the extracted text
        cleaned_text = cls.clean_text(text)
        
        if not cleaned_text:
            raise ValueError("No text could be extracted from the file")
        
        logger.info(f"Successfully extracted {len(cleaned_text)} characters from {file_type} file")
        
        return cleaned_text, file_bytes 