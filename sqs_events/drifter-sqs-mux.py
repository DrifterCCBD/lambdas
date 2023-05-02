import json
import boto3

lambda_client = boto3.client('lambda')

def process_message(msg):
    msg_type =  msg.get("type","")
    if msg_type == "background-check":
        dst_fn = "drifter-process-background-check"
    elif msg_type == "notification":
        print("Processing notification")
        dst_fn = "drifter-process-notification"
    else:
        return
    lambda_client.invoke(
        FunctionName=dst_fn,
        InvocationType='Event',
        Payload=json.dumps(msg)
    )

def lambda_handler(event, context):
    if "Records" in event:
        for record in event["Records"]:
            print(record)
            body = json.loads(record["body"])
            process_message(body)
    elif event.get("eventSource", "") == "aws:sqs":
        body = json.loads(event["body"])
        process_message(body)
    print(event)
    return { 'statusCode': 200 }
