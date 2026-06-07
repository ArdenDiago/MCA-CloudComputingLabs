import logging
import boto3


def get_client(region="us-east-1"):
    return boto3.client("s3", region_name=region)


def create_bucket(bucket_name, region="us-east-1", allow_public=False):
    try:
        s3 = get_client(region)
        # us-east-1 must NOT have LocationConstraint — all other regions must
        if region == "us-east-1":
            s3.create_bucket(Bucket=bucket_name)
        else:
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={"LocationConstraint": region},
            )

        # BucketOwnerPreferred allows ACLs (disabled by default since 2023)
        s3.put_bucket_ownership_controls(
            Bucket=bucket_name,
            OwnershipControls={"Rules": [{"ObjectOwnership": "BucketOwnerPreferred"}]},
        )

        if allow_public:
            s3.put_public_access_block(
                Bucket=bucket_name,
                PublicAccessBlockConfiguration={
                    "BlockPublicAcls": False,
                    "IgnorePublicAcls": False,
                    "BlockPublicPolicy": False,
                    "RestrictPublicBuckets": False,
                },
            )

        return True, None
    except Exception as e:
        logging.error(e)
        return False, str(e)


def list_buckets():
    try:
        s3 = get_client()
        response = s3.list_buckets()
        return [b["Name"] for b in response.get("Buckets", [])], None
    except Exception as e:
        logging.error(e)
        return [], str(e)


def upload_file(file_bytes, bucket_name, object_name, acl="private", content_type="application/octet-stream"):
    try:
        s3 = get_client()
        s3.put_object(
            Bucket=bucket_name,
            Key=object_name,
            Body=file_bytes,
            ACL=acl,
            ContentType=content_type,
        )
        location = s3.get_bucket_location(Bucket=bucket_name)["LocationConstraint"] or "us-east-1"
        if acl == "public-read":
            url = f"https://{bucket_name}.s3.{location}.amazonaws.com/{object_name}"
        else:
            url = f"s3://{bucket_name}/{object_name}"
        return True, url, None
    except Exception as e:
        logging.error(e)
        return False, None, str(e)


def list_objects(bucket_name):
    try:
        s3 = get_client()
        response = s3.list_objects_v2(Bucket=bucket_name)
        return [obj["Key"] for obj in response.get("Contents", [])], None
    except Exception as e:
        logging.error(e)
        return [], str(e)


def delete_object(bucket_name, object_key):
    try:
        s3 = get_client()
        s3.delete_object(Bucket=bucket_name, Key=object_key)
        return True, None
    except Exception as e:
        logging.error(e)
        return False, str(e)
