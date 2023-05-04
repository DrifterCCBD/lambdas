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

    print(event)
    return_val = []
    username = event.get("params",{}).get("path",{}).get("username",False)
    if username:
        print(username)
        with psycopg.connect(postgres_connect_string, row_factory=dict_row) as db:
           with db.cursor() as cur:
               cur.execute("SELECT users.username, count(driver.user_id) as is_driver, count(riders.user_id) as is_rider" + \
               " FROM users" + \
               " LEFT JOIN driver on driver.user_id = users.user_id" + \
               " LEFT JOIN riders on riders.user_id = users.user_id" + \
               " where users.username = %s GROUP BY driver.user_id, riders.user_id, users.username", (username, ))
               for row in cur:
                   return_val.append(row)
    if len(return_val) == 1:
        return_val = return_val[0]
    return return_val

