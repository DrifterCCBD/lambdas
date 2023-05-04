import json
import psycopg
from psycopg.rows import dict_row
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

    return_val = []
    username = event.get("params",{}).get("path",{}).get("username",False)
    if username:
        print(username)
        with psycopg.connect(postgres_connect_string, row_factory=dict_row) as db:
           with db.cursor() as cur:
               cur.execute("SELECT users.user_id, first_name, last_name, email, phone,"+ \
               " dob, gender, username, street_name_and_number, city, country, zip_code, address_id" + \
               " from users LEFT JOIN addresses on users.user_id = addresses.user_id" + \
               " LEFT JOIN driver on users.user_id = driver.user_id" + \
               " where username = %s", (username, ))
               for row in cur:
                   row["dob"] = str(row["dob"])
                   return_val.append(row)


    return return_val


