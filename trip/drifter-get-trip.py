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
                query = "SELECT my_trip.trip_id, my_trip.driver_id, my_trip.origin, my_trip.destination,\
                    my_trip.start_date, my_trip.start_time, GROUP_CONCAT(users.first_name SEPARATOR ', ') AS rider_firstnames\
                        FROM my_trip\
                        LEFT JOIN rider_trip ON my_trip.trip_id = rider_trip.trip_id\
                        LEFT JOIN riders ON rider_trip.rider_id = riders.rider_id\
                        LEFT JOIN users ON riders.user_id = users.user_id\
                        WHERE my_trip.driver_id = (\
                        SELECT driver_id\
                        FROM users\
                        WHERE username = '" + username + "'\
                        )\
                        GROUP BY my_trip.trip_id"
                cur.execute(query)
                query_result = cur.fetchall()

        print(query_result)
        
        past_trips = []
        future_trips = []
        
        
        for data in query_result:
            return_data = {}
            return_data['trip_id'] = data[0]
            return_data['driver_id'] = data[1]
            return_data['origin'] = data[2]
            return_data['destination'] = data[3]
            return_data['date_time'] = data[4] + ' ' + data[5]
            return_data['rider_firstnames'] = data[6]

            input_datetime = datetime.strptime(return_data['date_time'], '%Y-%m-%d %H:%M:%S')

            if input_datetime < datetime.now():
                past_trips.append(return_data)
            else:
                future_trips.append(return_data)
        
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
