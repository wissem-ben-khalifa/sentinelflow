from storage.minio_client import upload_dataset, get_storage_summary
from config.settings import RAW_DATA_DIR

for dataset in ["users", "products", "orders"]:
    upload_dataset(dataset, RAW_DATA_DIR / f"{dataset}.csv")

summary = get_storage_summary()
print(f"Raw files: {summary['raw_files']}")
print(f"Total size: {summary['total_size_mb']} MB")