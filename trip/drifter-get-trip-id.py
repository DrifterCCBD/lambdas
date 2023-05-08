import json
import psycopg
from psycopg.rows import dict_row
import os


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
    print(event)
    trip_id = int(event.get("params",{}).get("path",{}).get("id",False))


    trip_current_status = {}
    if(trip_id):
        with connect_to_db() as db:
            with db.cursor() as cur:
                cur.execute("SELECT my_trip.trip_id, price, my_trip.driver_id, origin, destination," + \
                "start_date, start_time, max_capacity, price, sum(rider_trip.accepted::int) as rider_count," + \
                " users.username as driver_username FROM my_trip" + \
                " LEFT JOIN driver on driver.driver_id = my_trip.driver_id" + \
                " LEFT JOIN users on driver.user_id = users.user_id" + \
                " LEFT JOIN rider_trip on rider_trip.trip_id = my_trip.trip_id" + \
                " WHERE my_trip.trip_id = %s" + \
                " GROUP BY rider_trip.trip_id, my_trip.trip_id, users.username", (trip_id,) )
                trip_current_status = cur.fetchone()
                if trip_current_status:
                    trip_current_status["start_time"] = str(trip_current_status["start_time"])
                    trip_current_status["start_date"] = str(trip_current_status["start_date"])

    if trip_current_status["rider_count"] == None:
        trip_current_status["rider_count"] = 0
    return {
        'statusCode': 200,
        'body': json.dumps(trip_current_status),
    }
