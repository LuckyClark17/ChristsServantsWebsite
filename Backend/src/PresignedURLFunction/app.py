import json
import logging
import boto3
import os
import uuid
from botocore.exceptions import NoCredentialsError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        queryParams = event.get('queryStringParameters')
        logger.info(f"Received body: {queryParams}")
        file_name = queryParams['fileName'].replace(" ", "-")
        file_type = queryParams['fileType']
        ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf']

        if file_type not in ALLOWED_TYPES:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Invalid file type.'})
            }
    except:
        logger.error("Invalid input: fileName and fileType are required")
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Invalid input, fileName and fileType are required'})
        }

    bucket_name = os.getenv('BUCKET_NAME')
    file_ext = os.path.splitext(file_name)[1]
    file_key = f'photoDump/{uuid.uuid4()}{file_ext}'
    
    s3_client = boto3.client('s3')

    try:
        # Get the pre-signed URL
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={'Bucket': bucket_name, 'Key': file_key, 'ContentType': file_type},
            ExpiresIn=60
        )

        logger.info(f"Generated presigned URL: {presigned_url}")
        file_url = f'https://{bucket_name}.s3.amazonaws.com/{file_key}'
        logger.info(json.dumps({'uploadUrl': presigned_url, 'fileUrl': file_url}))
        return {
            'statusCode': 200,
            'body': json.dumps({'uploadUrl': presigned_url, 'fileUrl': file_url}),
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "*"
            }
        }
    except Exception as e:
        logger.error(f"Error generating presigned URL: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': str(e)})
        }