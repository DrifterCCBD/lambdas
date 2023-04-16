import json
import datetime
import psycopg
import os



def lambda_handler(event, context):
    username = ''

    try:
        username = event['params']['querystring']['username']
    except:
        print('username not present')
    
    if username != '':
        # TODO: query database for all trips with this username
        # TODO: divide them by future and past trips
        # TODO: send the json object with two values, future and past trips

        db_host = os.environ.get("POSTGRES_HOSTNAME")
        db_port = os.environ.get("POSTGRES_PORT")
        db_name = os.environ.get("POSTGRES_DB")
        db_user = os.environ.get("POSTGRES_USER")
        db_pass = os.environ.get("POSTGRES_PASS")
        postgres_connect_string = "host='{}' port='{}' sslmode=verify-full sslrootcert=/opt/global-bundle.pem dbname='{}' user='{}' password='{}'".format(
            db_host,
            db_port,
            db_name,
            db_user,
            db_pass
            )
    

        with psycopg.connect(postgres_connect_string) as db:
            with db.cursor() as cur:
                cur.execute("SELECT * FROM my_trip join users on driver_id = user_id WHERE username = '" + username + "';")
                query_result = cur.fetchall()

        print(query_result)
        
        past_trips = []
        future_trips = []
        
        for data in query_result:
            if datetime.datetime.strptime(data['start-date'], "%d/%m/%Y").date() < datetime.now():
                past_trips.append(data)
            else:
                future_trips.append(data)
        
        return_json = {
            'future_trips': future_trips,
            'past_trips': past_trips
        }

        return {
            'statusCode': 200,
            'body': json.dumps({'results': return_json}),
            'event' : event
        }
    
    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!'),
        'event' : event
    }
