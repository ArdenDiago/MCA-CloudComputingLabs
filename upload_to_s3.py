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
