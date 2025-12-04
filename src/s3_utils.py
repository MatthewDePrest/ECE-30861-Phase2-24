import boto3
import json
import uuid
import os

s3 = boto3.client("s3")

def save_result_to_s3(result: dict, bucket: str) -> str:

    # File name:
    model_name = result.get("name") or f"model-{uuid.uuid4()}"
    key = f"results/{model_name}.json"

    # S3 Uploading
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(result),
        ContentType="application/json"
    )

    # Return presigned download link
    url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=3600,  # 1 hour
    )

    return url
