import json
import datetime

def lambda_handler(event, context):
    try:
        username = event['params']['querystring']['username']
        # TODO: query database for all trips with this username
        # TODO: divide them by future and past trips
        # TODO: send the json object with two values, future and past trips
        
        
        #TODO FIX:
        # query_result = #query database
        
        past_trips = []
        future_trips = []
        
        for data in query_result:
            if datetime.datetime.strptime(data['start-date'], "%d/%m/%Y").date() < datetime.now():
                past_trips.add(data)
            else:
                future_trips.add(data)
        
        return_json = {
            future_trips: future_trips,
            past_trips: past_trips
        }

        return {
            'statusCode': 200,
            'body': json.dumps({'results': return_json}),
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
