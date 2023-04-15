import json

def lambda_handler(event, context):
    # TODO: delete this funciton
    # no longer necessary now that
    # user pool creates user
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!'),
        'event' : event
    }
