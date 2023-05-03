import json
import os
import boto3
import psycopg
from psycopg.rows import dict_row

lambda_client = boto3.client('lambda')



def mark_completed(username):
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
    email = False
    with psycopg.connect(postgres_connect_string, row_factory=dict_row) as db:
        with db.cursor() as cur:
            query = "UPDATE driver SET background_check_complete = true WHERE user_id = (SELECT user_id FROM users WHERE username = %s)"
            query_values = (username,)
            cur.execute(query, query_values)
            cur.execute("SELECT email from users where username = %s", query_values)
            for row in cur:
                email = row["email"]
        db.commit()

    if email:
        msg = {"msg": "Your background check has been completed and approved!", "dst" : email}
        lambda_client.invoke(
            FunctionName="drifter-process-notification",
            InvocationType='Event',
            Payload=json.dumps(msg)
        )
def lambda_handler(event, context):
    username = event.get("username",False)
    if username:
        mark_completed(username)
    return {
        'statusCode': 200,
    }
