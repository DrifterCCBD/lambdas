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
                query = "INSERT into users (username, email, first_name, last_name, phone, dob, gender) VALUES (%s, %s, ' ', ' ', '0000000000', '1900-01-01', ' ')" + \
                " ON CONFLICT ON CONSTRAINT users_username_key DO UPDATE SET email = %s WHERE users.username = %s  RETURNING user_id", (username, email, email, username)
                print(query)
                cur.execute(query[0],query[1])
                user_id = cur.fetchone()
                print(user_id)
                cur.execute("SELECT COUNT(*) as count from addresses where user_id = %s", user_id)
                result = cur.fetchone()[0]
                if result == 0:
                    cur.execute("INSERT into addresses (zip_code, country, city, street_name_and_number, user_id) VALUES ('00000', ' ', ' ', ' ', %s)", user_id)
           db.commit()
    return event


