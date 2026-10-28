import boto3
import sys

from sqlmodel import Session, select, insert
from concurrent.futures import ThreadPoolExecutor
from botocore.client import Config
from typing import BinaryIO, List

from backend.models.schemas import Users, Resumes, ResumeAnalysis, CVS
from src.exception import CustomException
from backend.models.database import engine
from config import KEY_ID, APPLICATION_KEY, ENDPOINT_URL, BUCKET_NAME

def create_client():
    try:
        client = boto3.client(
            service_name="s3",
            endpoint_url=ENDPOINT_URL,
            aws_access_key_id=KEY_ID,
            aws_secret_access_key=APPLICATION_KEY,
            config=Config(signature_version="s3v4")
        )
        return client
    except Exception as e:
        raise CustomException(e, sys)

def sync_file_upload(file_obj: BinaryIO, file_name: str, content_type: str = "application/pdf"):
    try:
        # create the boto3 client
        client = create_client()
        # send the file_obj to the blackblaze bucket
        client.upload_fileobj(
            Fileobj=file_obj,
            Bucket=BUCKET_NAME,
            Key=file_name,
            ExtraArgs={"ContentType": content_type}
        )
        return f"{ENDPOINT_URL}/{BUCKET_NAME}/{file_name}"
    except Exception as e:
        raise CustomException(e, sys)

def upload_file(file_objs: List[BinaryIO], user_ids: List[str], file_name: List[str], content_type: str = "application/pdf"):
    try:
        # initialize the thread pool executor with the number of workers equal to the number of files
        num_workers = max(1, min(len(file_objs), 10))
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            # submit the upload tasks to the executor
            content_types = [content_type] * len(file_objs)
            urls = list(executor.map(sync_file_upload, file_objs, file_name, content_types))

        with Session(engine) as session:
            for user_id, url in zip(user_ids, urls):
                resume = Resumes(user_id=user_id, resume_url=url)
                session.add(resume)
            session.commit()
        return urls
    except Exception as e:
        raise CustomException(e, sys)