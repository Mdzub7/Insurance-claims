import json
import urllib.parse
import boto3
import os

# Initialize clients outside the handler (Best Practice: Connection Reuse)
sqs = boto3.client('sqs')


def parse_records(event):
    """Parse S3 event records.

    Parameters:
    - event: AWS Lambda event from S3

    Returns:
    - iterable of dicts with bucket, key, timestamp
    """
    for record in event.get('Records', []):
        yield {
            'bucket': record['s3']['bucket']['name'],
            'key': urllib.parse.unquote_plus(record['s3']['object']['key'], encoding='utf-8'),
            'timestamp': record['eventTime']
        }


def send_to_sqs(queue_url: str, payload: dict) -> str:
    """Send message to SQS.

    Parameters:
    - queue_url: SQS queue URL
    - payload: message body dict

    Returns:
    - MessageId
    """
    resp = sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(payload))
    return resp['MessageId']

def lambda_handler(event, context):
    """S3-triggered handler: enqueue claim analysis requests to SQS.

    Future integration point: invoke Bedrock to pre-analyze PDF and attach metadata.
    """
    queue_url = os.environ['SQS_QUEUE_URL']
    for r in parse_records(event):
        payload = {"bucket": r['bucket'], "key": r['key'], "action": "ANALYZE_CLAIM", "timestamp": r['timestamp']}
        send_to_sqs(queue_url, payload)
    return {'statusCode': 200, 'body': json.dumps('File processed successfully')}
