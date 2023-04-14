import json
import psycopg2
import os

def lambda_handler(event, context):
    db_host = os.environ.get("POSTGRES_HOSTNAME")
    db_port = os.environ.get("POSTGRES_PORT")
    db_name = os.environ.get("POSTGRES_DB")
    db_user = os.environ.get("POSTGRES_USER")
    db_pass = os.environ.get("POSTGRES_PASS")
    postgres_uri = "pq://{}:{}@{}:{}/{}?[sslmode]=require&[sslrootcrtfile]=./global-bundle.pem".format(
        db_user,
        db_pass,
        db_host,
        db_port,
        db_name
        )
    
    username = event.get("userName",False)
    email = event.get("request",{}).get("userAttributes",{}).get("email",False)
    if username and email:
        db = postgresql.open(postgres_uri)    
        get_table = db.prepare("SELECT * from information_schema.tables WHERE table_name = $1")
        print(get_table("tables"))

        # Streaming, in a transaction.
        with db.xact():
	        for x in get_table.rows("tables"):
		        print(x)
    
    return event

