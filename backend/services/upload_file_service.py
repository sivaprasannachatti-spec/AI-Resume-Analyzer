import boto3
import logging
import sys
import time
from urllib.parse import urlsplit

from sqlmodel import Session, select, insert
from concurrent.futures import ThreadPoolExecutor
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError
from typing import BinaryIO, List

from backend.models.schemas import Users, Resumes, ResumeAnalysis
from src.exception import CustomException
from backend.models.database import engine
from config import KEY_ID, APPLICATION_KEY, ENDPOINT_URL, BUCKET_NAME

logger = logging.getLogger(__name__)


def _storage_endpoint_host() -> str:
    if not ENDPOINT_URL:
        return "not configured"
    try:
        parsed_endpoint = urlsplit(ENDPOINT_URL)
        hostname = parsed_endpoint.hostname
        port = parsed_endpoint.port
    except ValueError:
        return "invalid endpoint URL"
    if not hostname:
        return "invalid endpoint URL"
    return f"{hostname}:{port}" if port else hostname


def create_client():
    try:
        if not ENDPOINT_URL:
            raise ValueError("ENDPOINT_URL is not configured")
        if not BUCKET_NAME:
            raise ValueError("BUCKET_NAME is not configured")
        if not KEY_ID or not APPLICATION_KEY:
            raise ValueError("Backblaze credentials are not configured")

        client = boto3.client(
            service_name="s3",
            endpoint_url=ENDPOINT_URL,
            aws_access_key_id=KEY_ID,
            aws_secret_access_key=APPLICATION_KEY,
            config=Config(
            signature_version="s3v4",
            request_checksum_calculation="when_required",
            response_checksum_validation="when_required",
            retries={"max_attempts": 10, "mode": "adaptive"},
            connect_timeout=10,
            read_timeout=60
            )
        )
        return client
    except Exception as e:
        logger.exception(
            "Failed to initialize the S3-compatible storage client (endpoint=%s, bucket=%s)",
            _storage_endpoint_host(),
            BUCKET_NAME,
        )
        raise CustomException(e, sys)


def sync_file_upload(file_obj: BinaryIO, file_name: str, content_type: str = "application/pdf"):
    started_at = time.perf_counter()
    logger.info(
        "Starting object storage upload (endpoint=%s, bucket=%s, content_type=%s)",
        _storage_endpoint_host(),
        BUCKET_NAME,
        content_type,
    )
    try:
        client = create_client()
        client.upload_fileobj(
            Fileobj=file_obj,
            Bucket=BUCKET_NAME,
            Key=file_name,
            ExtraArgs={"ContentType": content_type}
        )
        logger.info(
            "Object storage upload completed (bucket=%s, duration_seconds=%.2f)",
            BUCKET_NAME,
            time.perf_counter() - started_at,
        )
        return f"{ENDPOINT_URL}/{BUCKET_NAME}/{file_name}"
    except ClientError as e:
        error = e.response.get("Error", {})
        metadata = e.response.get("ResponseMetadata", {})
        logger.exception(
            "Object storage rejected upload (bucket=%s, error_code=%s, "
            "error_message=%s, http_status=%s, request_id=%s)",
            BUCKET_NAME,
            error.get("Code"),
            error.get("Message"),
            metadata.get("HTTPStatusCode"),
            metadata.get("RequestId"),
        )
        raise CustomException(e, sys)
    except BotoCoreError as e:
        logger.exception(
            "Storage client/network failure during upload (endpoint=%s, bucket=%s, "
            "duration_seconds=%.2f, error_type=%s)",
            _storage_endpoint_host(),
            BUCKET_NAME,
            time.perf_counter() - started_at,
            type(e).__name__,
        )
        raise CustomException(e, sys)
    except Exception as e:
        logger.exception(
            "Unexpected failure during object storage upload (bucket=%s, "
            "duration_seconds=%.2f, error_type=%s)",
            BUCKET_NAME,
            time.perf_counter() - started_at,
            type(e).__name__,
        )
        raise CustomException(e, sys)


def upload_file(file_objs: List[BinaryIO], user_ids: List[str], file_name: List[str], content_type: str = "application/pdf"):
    try:
        num_workers = max(1, min(len(file_objs), 10))
        logger.info("Uploading %d file(s) with %d worker(s)", len(file_objs), num_workers)
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            content_types = [content_type] * len(file_objs)
            urls = list(executor.map(sync_file_upload, file_objs, file_name, content_types))

        with Session(engine) as session:
            for user_id, url in zip(user_ids, urls):
                resume = Resumes(user_id=user_id, resume_url=url)
                session.add(resume)
            session.commit()
        logger.info("Uploaded %d file(s) and saved their resume records", len(urls))
        return urls
    except Exception as e:
        logger.exception("Batch file upload or resume-record persistence failed")
        raise CustomException(e, sys)