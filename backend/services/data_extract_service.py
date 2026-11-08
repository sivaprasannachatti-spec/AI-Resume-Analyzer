import sys
import io
import requests

from typing import List
from sqlmodel import Session, select
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import DocumentStream
from src.exception import CustomException

def extract_file_bytes(file_url: str) -> bytes:
    try:
        response = requests.get(file_url, timeout=30)
        response.raise_for_status()
        return response.content
    except Exception as e:
        raise CustomException(e, sys)

async def extract_markdown_from_bytes(file_bytes: bytes, filename: str = "resume.pdf") -> str:
    """Extracts markdown layout directly from in-memory PDF bytes using Docling."""
    try:
        file_stream = io.BytesIO(file_bytes)
        document_stream = DocumentStream(stream=file_stream, name=filename)
        converter = DocumentConverter()
        result = converter.convert(source=document_stream)
        return result.document.export_to_markdown()
    except Exception as e:
        raise CustomException(e, sys)

def extract_data(file_urls: List[str]):
    try:
        file_mds = []
        for url in file_urls:
            file_bytes = extract_file_bytes(url)
            file_stream = io.BytesIO(file_bytes)
            document_stream = DocumentStream(stream=file_stream, name=url.split("/")[-1])
            converter = DocumentConverter()
            result = converter.convert(source=document_stream)
            file_mds.append(result.document.export_to_markdown())
        return file_mds
    except Exception as e: 
        raise CustomException(e, sys)