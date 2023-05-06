import json
import datetime
import psycopg
import os



def lambda_handler(event, context):
    # We're sending parameters with the request from the frontend
    # The parameters differ based on what is needed from the frontend
    # If username is present, we're being asked for trips beloning
    # either to a driver or a rider. The rider parameter gives us which.
    # If available is present then we're being asked for all available
    # trips for riders to select.

    username = ''
    available = ''
    rider = ''

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

    try:
        username = event['params']['querystring']['username']
        rider = event['params']['querystring']['rider']
    except:
        print('username not present')

    try:
        available = event['params']['querystring']['available']
    except:
        print('available not present')

    if username != '':
        if rider == 'true':
            query = "SELECT mt.trip_id, mt.origin, mt.destination, u.username AS driver_username, mt.start_date, mt.start_time\
                FROM my_trip mt\
                INNER JOIN driver d ON mt.driver_id = d.driver_id\
                INNER JOIN users u ON d.user_id = u.user_id\
                INNER JOIN rider_trip rt ON mt.trip_id = rt.trip_id\
                INNER JOIN riders r ON rt.rider_id = r.rider_id\
                INNER JOIN users ru ON r.user_id = ru.user_id\
                WHERE ru.username = '" + username + "'"

            with psycopg.connect(postgres_connect_string) as db:
                with db.cursor() as cur:
                    cur.execute(query)
                    query_result = cur.fetchall()

            print(query_result)

            past_trips = []
            future_trips = []


            for data in query_result:
                return_data = {}
                return_data['trip_id'] = data[0]
                return_data['origin'] = data[1]
                return_data['destination'] = data[2]
                return_data['driver_username'] = data[3]

                return_data['date_time'] = str(datetime.datetime.combine(data[4], data[5]))



                if datetime.datetime.combine(data[4], data[5]) < datetime.datetime.now():
                    past_trips.append(return_data)
                else:
                    future_trips.append(return_data)

        else:
            query = "SELECT my_trip.trip_id, my_trip.driver_id, my_trip.origin, my_trip.destination,\
            my_trip.start_date, my_trip.start_time, string_agg(users.username, ', ') AS rider_usernames,\
            my_trip.max_capacity, my_trip.price, count(rider_trip.rider_id) as curr_capacity\
            FROM my_trip\
            LEFT JOIN rider_trip ON my_trip.trip_id = rider_trip.trip_id\
            LEFT JOIN riders ON rider_trip.rider_id = riders.rider_id\
            LEFT JOIN users ON riders.user_id = users.user_id\
            WHERE my_trip.driver_id = (\
            SELECT driver_id\
            FROM users\
            WHERE username = %s\
            )\
            GROUP BY my_trip.trip_id"

            with psycopg.connect(postgres_connect_string) as db:
                with db.cursor() as cur:
                    cur.execute(query, (username,))
                    query_result = cur.fetchall()

            print(query_result)
            past_trips = []
            future_trips = []


            for data in query_result:
                print(data)
                return_data = {}
                return_data['trip_id'] = data[0]
                return_data['origin'] = data[2]
                return_data['destination'] = data[3]
                return_data['rider_usernames'] = data[6]

                return_data['date_time'] = str(datetime.datetime.combine(data[4], data[5]))
                return_data['max_capacity'] = data[7]
                return_data['curr_capacity'] = data[9]
                return_data['price'] = data[8]



                if datetime.datetime.combine(data[4], data[5]) < datetime.datetime.now():
                    past_trips.append(return_data)
                else:
                    future_trips.append(return_data)

        return_json = {
            'future_trips': future_trips,
            'past_trips': past_trips
        }

        print('hello', return_json)

        return {
            'statusCode': 200,
            'body': json.dumps({'results': return_json}),
            'event' : event
        }

    elif available != '':
        # Returns all trips that are in the future and don't have full capacity

        with psycopg.connect(postgres_connect_string) as db:
            with db.cursor() as cur:
                query = "SELECT t.trip_id, u.username AS driver_username, t.origin,\
                t.destination, t.start_date, t.start_time\
                FROM my_trip t\
                INNER JOIN driver d ON t.driver_id = d.driver_id\
                INNER JOIN users u ON d.user_id = u.user_id\
                WHERE t.curr_capacity < t.max_capacity"
                cur.execute(query)
                query_result = cur.fetchall()

        print(query_result)

        past_trips = []
        future_trips = []


        for data in query_result:
            return_data = {}
            return_data['date_time'] = str(datetime.datetime.combine(data[4], data[5]))
            return_data['origin'] = data[2]
            return_data['destination'] = data[3]
            return_data['driver_username'] = data[1]

            if datetime.datetime.combine(data[4], data[5]) < datetime.datetime.now():
                past_trips.append(return_data)
            else:
                future_trips.append(return_data)

        return_json = {
            'future_trips': future_trips,
            'past_trips': past_trips
        }

        print(return_json)


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
