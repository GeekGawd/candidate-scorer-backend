import base64
import io
from typing import Tuple, Optional
import logging
from pypdf import PdfReader
from docx import Document
import re
from fastapi import UploadFile

logger = logging.getLogger(__name__)

class FileProcessor:
    """Service for processing uploaded resume files"""
    
    @staticmethod
    async def extract_text_from_pdf(file_content: bytes) -> str:
        """Extract text from PDF file"""
        try:
            pdf_stream = io.BytesIO(file_content)
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
    async def extract_text_from_docx(file_content: bytes) -> str:
        """Extract text from Word document"""
        try:
            doc_stream = io.BytesIO(file_content)
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
    async def process_resume_file(cls, upload_file: UploadFile) -> Tuple[str, bytes]:
        """
        Process uploaded resume file and extract text
        
        Args:
            upload_file: FastAPI UploadFile object
        
        Returns:
            Tuple of (extracted_text, original_file_bytes)
        """
        # Validate file type
        if not upload_file.filename:
            raise ValueError("No filename provided")
        
        file_extension = upload_file.filename.lower().split('.')[-1]
        if file_extension not in ['pdf', 'docx']:
            raise ValueError("Unsupported file type. Only PDF and DOCX are supported.")
        
        # Read file content
        try:
            file_content = await upload_file.read()
            if not file_content:
                raise ValueError("Empty file uploaded")
        except Exception as e:
            logger.error(f"Failed to read uploaded file: {e}")
            raise ValueError("Failed to read uploaded file")
        
        # Extract text based on file type
        try:
            if file_extension == 'pdf':
                text = await cls.extract_text_from_pdf(file_content)
            elif file_extension == 'docx':
                text = await cls.extract_text_from_docx(file_content)
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
        except Exception as e:
            logger.error(f"Failed to extract text from {file_extension}: {e}")
            raise ValueError(f"Failed to process {file_extension} file: {e}")
        
        # Clean the extracted text
        cleaned_text = cls.clean_text(text)
        
        if not cleaned_text:
            raise ValueError("No text could be extracted from the file")
        
        logger.info(f"Successfully extracted {len(cleaned_text)} characters from {file_extension} file: {upload_file.filename}")
        
        return cleaned_text, file_content
    
    @staticmethod
    def validate_file_size(upload_file: UploadFile, max_size_mb: int = 10) -> bool:
        """Validate file size (this needs to be called before reading the file)"""
        if hasattr(upload_file, 'size') and upload_file.size:
            max_size_bytes = max_size_mb * 1024 * 1024
            if upload_file.size > max_size_bytes:
                raise ValueError(f"File size exceeds {max_size_mb}MB limit")
        return True 