import json
import os
import boto3
import psycopg
from psycopg.rows import dict_row
import urllib.request
import time
from jose import jwk, jwt
from jose.utils import base64url_decode


region = 'us-east-1'
userpool_id = 'us-east-1_t2k3bBj7B'
app_client_id = '11rhsugidc5dspcofo86ec77ed'
keys_url = 'https://cognito-idp.{}.amazonaws.com/{}/.well-known/jwks.json'.format(region, userpool_id)
# instead of re-downloading the public keys every time
# we download them only on cold start
# https://aws.amazon.com/blogs/compute/container-reuse-in-lambda/
with urllib.request.urlopen(keys_url) as f:
  response = f.read()
keys = json.loads(response.decode('utf-8'))['keys']
print(keys)



def lambda_handler(event, context):
    print(event)

    try:
        username = event.get("params",{}).get("path",{}).get("username",False)
    except:
        print('username not present')


    request_body = event.get("body",{})

    request_keys = request_body.keys()

    assert(len(list(request_keys))>0)


    token = event.get("params",{}).get("header",{}).get("Authorization","")
    token_claims = verify_jwt_token(token)
    assert(token_claims != False)
    username = token_claims["cognito:username"]


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
    id = ''
    request_body = event.get("body",{})
    print(request_body)

    if username:
        with psycopg.connect(postgres_connect_string, row_factory=dict_row) as db:
            with db.cursor() as cur:

                query1 = "SELECT driver.driver_id FROM driver JOIN users ON driver.user_id = users.user_id WHERE users.username=%s"
                query_values1 = (username,)
                cur.execute(query1, query_values1)
                h = cur.fetchone()
                id = h['driver_id']
                query = "INSERT INTO my_trip (driver_id, origin, destination, start_date, start_time, max_capacity, curr_capacity, price) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                query_values = (id, request_body['origin'], request_body['destination'], request_body['date'], request_body['time'], request_body['number'], 0, request_body['price'])
                cur.execute(query, query_values)
            db.commit()


    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!'),
        'event' : id
    }


def verify_jwt_token(token):
    # get the kid from the headers prior to verification
    headers = jwt.get_unverified_headers(token)
    kid = headers['kid']
    # search for the kid in the downloaded public keys
    key_index = -1
    for i in range(len(keys)):
        if kid == keys[i]['kid']:
            key_index = i
            break
    if key_index == -1:
        print('Public key not found in jwks.json')
        return False
    # construct the public key
    public_key = jwk.construct(keys[key_index])
    # get the last two sections of the token,
    # message and signature (encoded in base64)
    message, encoded_signature = str(token).rsplit('.', 1)
    # decode the signature
    decoded_signature = base64url_decode(encoded_signature.encode('utf-8'))
    # verify the signature
    if not public_key.verify(message.encode("utf8"), decoded_signature):
        print('Signature verification failed')
        return False
    print('Signature successfully verified')
    # since we passed the verification, we can now safely
    # use the unverified claims
    claims = jwt.get_unverified_claims(token)
    # additionally we can verify the token expiration
    if time.time() > claims['exp']:
        print('Token is expired')
        return False
    # and the Audience  (use claims['client_id'] if verifying an access token)
    if claims['aud'] != app_client_id:
        print('Token was not issued for this audience')
        return False
    # now we can use the claims
    print(claims)
    return claims
