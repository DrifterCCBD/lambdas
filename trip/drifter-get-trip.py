import json
import datetime
import psycopg
import os
from psycopg.rows import dict_row


def connect_to_db():
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
    return psycopg.connect(postgres_connect_string, row_factory=dict_row)

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
    except:
        raise Exception('username not present')

    rider = event['params']['querystring'].get('rider', '')
    available = event['params']['querystring'].get('available','')
    driver_pending = event['params']['querystring'].get('driver_pending','')
    show_pending = event['params']['querystring'].get('show_pending','')


    if rider == 'true':
        """query = "SELECT mt.trip_id, mt.origin, mt.destination, u.username AS driver_username, mt.start_date, mt.start_time\
            FROM my_trip mt\
            INNER JOIN driver d ON mt.driver_id = d.driver_id\
            INNER JOIN users u ON d.user_id = u.user_id\
            INNER JOIN rider_trip rt ON mt.trip_id = rt.trip_id\
            INNER JOIN riders r ON rt.rider_id = r.rider_id\
            INNER JOIN users ru ON r.user_id = ru.user_id\
            WHERE ru.username = %s"""

        query = "SELECT my_trip.trip_id, my_trip.driver_id, my_trip.origin, my_trip.destination,\
        my_trip.start_date, my_trip.start_time, string_agg(users.username, ', ') AS rider_usernames,\
        my_trip.max_capacity, my_trip.price, sum(capacity.accepted::int) as curr_capacity, rt.accepted,\
        du.username as driver_username\
        FROM my_trip\
        LEFT JOIN rider_trip rt ON my_trip.trip_id = rt.trip_id\
        LEFT JOIN riders ON rt.rider_id = riders.rider_id\
        LEFT JOIN rider_trip capacity ON capacity.trip_id = my_trip.trip_id\
        LEFT JOIN users ON riders.user_id = users.user_id\
        LEFT JOIN driver ON driver.driver_id = my_trip.driver_id\
        LEFT JOIN users du ON driver.user_id = du.user_id\
        WHERE users.username = %s\
        GROUP BY my_trip.trip_id, capacity.trip_id, rt.rider_id, rt.trip_id, rt.accepted, du.username"

        with psycopg.connect(postgres_connect_string) as db:
            with db.cursor() as cur:
                cur.execute(query, (username,))
                query_result = cur.fetchall()

        print(query_result)

        past_trips = []
        future_trips = []
        pending_trips = []


        for data in query_result:
            return_data = {}
            return_data['trip_id'] = data[0]
            return_data['origin'] = data[2]
            return_data['destination'] = data[3]
            return_data['rider_usernames'] = data[6]

            return_data['date_time'] = str(datetime.datetime.combine(data[4], data[5]))
            return_data['max_capacity'] = data[7]
            return_data['curr_capacity'] = data[9]
            return_data['price'] = data[8]
            driver_accepted = data[10]
            return_data["driver_username"] = data[11]


            """return_data['trip_id'] = data[0]
            return_data['origin'] = data[1]
            return_data['destination'] = data[2]
            return_data['driver_username'] = data[3]

            return_data['date_time'] = str(datetime.datetime.combine(data[4], data[5]))"""



            if datetime.datetime.combine(data[4], data[5]) < datetime.datetime.now():
                past_trips.append(return_data)
            elif driver_accepted:
                future_trips.append(return_data)
            else:
                pending_trips.append(return_data)
        return_json = {
            'future_trips': future_trips,
            'pending_trips' : pending_trips,
            'past_trips': past_trips
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
                LEFT JOIN rider_trip ON t.trip_id = rider_trip.trip_id\
                GROUP BY t.trip_id, u.username, t.origin, t.destination, t.start_date, t.start_time\
                HAVING count(rider_trip.rider_id) < t.max_capacity AND t.trip_id not \
                in(SELECT my_trip.trip_id from my_trip\
                LEFT JOIN rider_trip on my_trip.trip_id = rider_trip.trip_id\
                LEFT JOIN riders on riders.rider_id = rider_trip.rider_id\
                LEFT JOIN users on riders.user_id = users.user_id\
                WHERE users.username = %s)"
                cur.execute(query, (username,))
                query_result = cur.fetchall()

        print(query_result)

        past_trips = []
        future_trips = []


        for data in query_result:
            return_data = {}
            return_data['trip_id'] = data[0]
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
        }
    elif rider == "false":
        query = "SELECT my_trip.trip_id, my_trip.driver_id, my_trip.origin, my_trip.destination,\
        my_trip.start_date, my_trip.start_time, string_agg(users.username, ', ') AS rider_usernames,\
        my_trip.max_capacity, my_trip.price, count(rt.accepted) as curr_capacity\
        FROM my_trip\
        LEFT JOIN rider_trip rt ON my_trip.trip_id = rt.trip_id AND rt.accepted = true\
        LEFT JOIN riders ON rt.rider_id = riders.rider_id\
        LEFT JOIN users ON riders.user_id = users.user_id\
        WHERE my_trip.driver_id = (\
        SELECT driver_id FROM driver INNER JOIN users on driver.user_id = users.user_id\
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
        return {
            'statusCode': 200,
            'body': json.dumps({'results': return_json}),
        }
    elif show_pending == "true":
        return_data = []
        with connect_to_db() as db:
            with db.cursor() as cur:
                cur.execute("SELECT my_trip.trip_id, my_trip.origin, my_trip.destination,\
                            my_trip.start_date, my_trip.start_time, users.username AS request_username,\
                            my_trip.max_capacity, my_trip.price\
                            FROM my_trip\
                            LEFT JOIN rider_trip rt ON my_trip.trip_id = rt.trip_id\
                            LEFT JOIN riders ON rt.rider_id = riders.rider_id\
                            LEFT JOIN users ON riders.user_id = users.user_id\
                            LEFT JOIN driver ON my_trip.driver_id = driver.driver_id\
                            LEFT JOIN users driver_users ON driver.user_id = driver_users.user_id\
                            WHERE rt.accepted = false AND driver_users.username = %s \
                            GROUP BY my_trip.trip_id, users.username", (username,) )

                for row in cur:
                    row['date_time'] = str(datetime.datetime.combine(row["start_date"], row["start_time"]))
                    row.pop("start_time")
                    row.pop("start_date")
                    return_data.append(row)


        return {
            'statusCode': 200,
            'body': return_data,
        }
    return {
        'statusCode': 200,
        'body': json.dumps({'results': return_json}),
    }

    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!'),
        'event' : event
    }
