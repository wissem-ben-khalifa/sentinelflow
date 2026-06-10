"""
SentinelFlow - MinIO Client
Handles all interactions with MinIO (S3-compatible data lake).
Uploads raw data, processed data, and model artifacts.
"""

import os
from pathlib import Path
from minio import Minio
from minio.error import S3Error
from config.settings import (
    MINIO_ENDPOINT,
    MINIO_ACCESS_KEY,
    MINIO_SECRET_KEY,
    MINIO_BUCKET_NAME
)
from config.logging_config import get_logger

logger = get_logger(__name__)


def get_client() -> Minio:
    """Create and return a MinIO client."""
    return Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False
    )


def ensure_bucket_exists(client: Minio, bucket_name: str) -> None:
    """Create bucket if it does not exist."""
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
        logger.info(f"Created bucket: {bucket_name}")
    else:
        logger.info(f"Bucket already exists: {bucket_name}")


def upload_file(
    local_path: Path,
    object_name: str,
    bucket_name: str = None
) -> bool:
    """
    Upload a local file to MinIO.
    object_name is the path inside the bucket.
    Returns True if successful.
    """
    bucket = bucket_name or MINIO_BUCKET_NAME

    try:
        client = get_client()
        ensure_bucket_exists(client, bucket)

        client.fput_object(
            bucket,
            object_name,
            str(local_path)
        )

        logger.info(f"Uploaded {local_path} to s3://{bucket}/{object_name}")
        return True

    except S3Error as e:
        logger.error(f"MinIO upload failed: {e}")
        return False


def download_file(
    object_name: str,
    local_path: Path,
    bucket_name: str = None
) -> bool:
    """
    Download a file from MinIO to local disk.
    Returns True if successful.
    """
    bucket = bucket_name or MINIO_BUCKET_NAME

    try:
        client = get_client()
        client.fget_object(bucket, object_name, str(local_path))
        logger.info(f"Downloaded s3://{bucket}/{object_name} to {local_path}")
        return True

    except S3Error as e:
        logger.error(f"MinIO download failed: {e}")
        return False


def list_objects(prefix: str = "", bucket_name: str = None) -> list:
    """List all objects in the bucket with an optional prefix."""
    bucket = bucket_name or MINIO_BUCKET_NAME

    try:
        client = get_client()
        objects = client.list_objects(bucket, prefix=prefix, recursive=True)
        result = []
        for obj in objects:
            result.append({
                "name": obj.object_name,
                "size": obj.size,
                "last_modified": obj.last_modified
            })
        logger.info(f"Listed {len(result)} objects in s3://{bucket}/{prefix}")
        return result

    except S3Error as e:
        logger.error(f"MinIO list failed: {e}")
        return []


def upload_dataset(dataset_name: str, local_path: Path) -> bool:
    """Upload a dataset CSV to the raw data layer in MinIO."""
    object_name = f"raw/{dataset_name}/{local_path.name}"
    return upload_file(local_path, object_name)


def upload_model(model_name: str, local_path: Path) -> bool:
    """Upload a trained model artifact to MinIO."""
    object_name = f"models/{model_name}/{local_path.name}"
    return upload_file(local_path, object_name)


def upload_processed(dataset_name: str, local_path: Path) -> bool:
    """Upload a processed dataset to the processed layer in MinIO."""
    object_name = f"processed/{dataset_name}/{local_path.name}"
    return upload_file(local_path, object_name)


def get_storage_summary() -> dict:
    """Get a summary of all objects stored in MinIO."""
    raw_objects = list_objects(prefix="raw/")
    model_objects = list_objects(prefix="models/")
    processed_objects = list_objects(prefix="processed/")

    total_size = sum(
        obj["size"] for obj in raw_objects + model_objects + processed_objects
    )

    return {
        "raw_files": len(raw_objects),
        "model_files": len(model_objects),
        "processed_files": len(processed_objects),
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / 1024 / 1024, 2)
    }