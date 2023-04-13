import json

def lambda_handler(event, context):
    try:
        username = event['params']['querystring']['username']
        # TODO: query database for all trips with this username
        # TODO: divide them by future and past trips
        # TODO: send the json object with two values, future and past trips
        return {
            'statusCode': 200,
            'body': json.dumps('Hello from Lambda!'),
            'event' : event
        }

    except:
        # TODO do other parameters check?
        print('username is not a parameter')

    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!'),
        'event' : event
    }
