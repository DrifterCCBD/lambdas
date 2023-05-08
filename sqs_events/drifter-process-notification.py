import json
import boto3
from botocore.config import Config


REGION = 'us-east-1'
FROM_EMAIL = "drifter-no-reply@jianmin.dev"


def get_awsclient(service, region=REGION):
    #cred = boto3.Session().get_credentials()
    my_config = Config(
        region_name = region
    )
    return boto3.client(service, config=my_config)

def send_email(dst, msg, subject):
    ses_client = get_awsclient('ses', 'us-east-2')
    body_html = """<html>
        <head></head>
        <body>
          <p>{}</p>
          If you would like to never receive messages from this bot again,
          please reply to this message with the text, "unsubscribe" in the message body.
        </body>
        </html>""".format(msg)
    email_message = {
        'Body': {
            'Html': {
                'Charset': 'utf-8',
                'Data': body_html,
            },
        },
        'Subject': {
            'Charset': 'utf-8',
            'Data': subject,
        },
    }
    try:
        ses_response = ses_client.send_email(
            Destination={
                'ToAddresses': [dst],
            },
            Message=email_message,
            Source=FROM_EMAIL,
        )
        print(ses_response)
    except Exception as e:
        print(e)

def lambda_handler(event, context):
    msg = event.get("msg",False)
    dst = event.get("dst",False)
    subject = event.get("subject","Drifter Notification")
    if msg and dst:
        send_email(dst, msg, subject)
    return {
        'statusCode': 200,
    }
