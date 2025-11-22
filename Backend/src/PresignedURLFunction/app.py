import json
import logging
import boto3
import os
from botocore.exceptions import NoCredentialsError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    # Parse the incoming request body (expecting fileName and fileType)
    try:
        body = json.loads(event['body'])
        logger.info(f"Received body: {body}")
        file_name = body['fileName'].replace(" ", "-")
        file_type = body['fileType']
    except (KeyError, json.JSONDecodeError):
        logger.error("Invalid input: fileName and fileType are required")
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Invalid input, fileName and fileType are required'})
        }

    # S3 bucket and the file key (path where the file will be uploaded)
    bucket_name = os.getenv('BUCKET_NAME')
    file_key = f'photoDump/{file_name}'  # Example: uploads/1632157600_filename.jpg
    
    # Generate a pre-signed URL to upload the file to S3
    s3_client = boto3.client('s3')

    try:
        # Get the pre-signed URL with 'putObject' permission for uploading
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={'Bucket': bucket_name, 'Key': file_key, 'ContentType': file_type},
            ExpiresIn=3600  # URL is valid for 1 hour (3600 seconds)
        )
        
        logger.info(f"Generated presigned URL: {presigned_url}")
        # The URL for accessing the uploaded file after it's uploaded to S3
        file_url = f'https://{bucket_name}.s3.amazonaws.com/{file_key}'
        logger.info(json.dumps({'uploadUrl': presigned_url, 'fileUrl': file_url}))
        return {
            'statusCode': 200,
            'body': json.dumps({'uploadUrl': presigned_url, 'fileUrl': file_url}),
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "*"
            }
        }

    except NoCredentialsError:
        logger.error("No valid AWS credentials found")
        return {
            'statusCode': 403,
            'body': json.dumps({'message': 'No valid AWS credentials found'})
        }
    except Exception as e:
        logger.error(f"Error generating presigned URL: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': str(e)})
        }