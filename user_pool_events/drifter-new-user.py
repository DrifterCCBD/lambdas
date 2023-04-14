import json
import psycopg
import os

def lambda_handler(event, context):
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
    
    username = event.get("userName",False)
    email = event.get("request",{}).get("userAttributes",{}).get("email",False)
    if username and email:
        with psycopg.connect(postgres_connect_string) as db:
           with db.cursor() as cur:
                cur.execute("INSERT into users (username, email, first_name, last_name, phone, dob, gender) VALUES (%s, %s, ' ', ' ', '15555555555', '1990-01-01', ' ')", (username, email))
           db.commit()
    return event

