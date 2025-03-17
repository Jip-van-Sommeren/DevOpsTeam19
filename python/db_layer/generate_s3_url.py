import boto3


def generate_presigned_url(bucket_name, object_key, expiration=3600):
    """
    Generate a pre-signed URL to share an S3 object

    :param bucket_name: Name of the S3 bucket.
    :param object_key: Key of the S3 object.
    :param expiration: Time in seconds for the pre-signed URL to remain valid.
    :return: Pre-signed URL as string. If error, returns None.
    """
    if object_key is None:
        return None
    s3_client = boto3.client("s3")
    try:
        response = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": object_key},
            ExpiresIn=expiration,
        )
        return response
    except Exception as e:
        print("Error generating pre-signed URL:", str(e))
        return None


# Example usage:
bucket = "your-bucket-name"
key = "path/to/your/image.jpg"
url = generate_presigned_url(bucket, key, expiration=3600)
print("Pre-signed URL:", url)
