import os
import boto3
from botocore.config import Config


class R2Uploader:
    def __init__(
        self,
        access_key_id: str,
        secret_access_key: str,
        endpoint: str,
        bucket_name: str,
        public_url: str,
    ):
        """
        Initialize R2Uploader with credentials and configuration

        Args:
            access_key_id: R2 access key ID
            secret_access_key: R2 secret access key
            account_id: R2 account ID
            bucket_name: R2 bucket name
            public_url: Public URL prefix for the bucket
        """
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.account_id = account_id
        self.bucket_name = bucket_name
        self.public_url = public_url

        if not all(
            [
                self.access_key_id,
                self.secret_access_key,
                self.account_id,
                self.bucket_name,
                self.public_url,
            ]
        ):
            raise ValueError("All parameters are required")

        # Configure boto3 client for Cloudflare R2
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            region_name="auto",  # Cloudflare R2 specific
            config=Config(
                s3={"addressing_style": "virtual"},
                region_name="auto",  # Cloudflare R2 specific
            ),
        )

    def upload_file(self, file_path: str, key: str = None) -> str:
        """
        Upload a file to R2 and return its public URL

        Args:
            file_path: Path to the local file
            key: Optional key (path) in the bucket. If not provided, will use filename

        Returns:
            Public URL of the uploaded file
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # If no key provided, use the filename
        if key is None:
            key = os.path.basename(file_path)

        try:
            # Upload the file
            self.s3_client.upload_file(
                Filename=file_path, Bucket=self.bucket_name, Key=key
            )

            # Return the public URL
            return f"{self.public_url.rstrip('/')}/{key}"
        except Exception as e:
            raise Exception(f"Failed to upload {file_path} to {key}: {str(e)}")
