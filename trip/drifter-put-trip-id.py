import json
import psycopg
from psycopg.rows import dict_row
import os
import urllib.request
import time
from jose import jwk, jwt
from jose.utils import base64url_decode
#reference: https://github.com/awslabs/aws-support-tools/blob/master/Cognito/decode-verify-jwt/decode-verify-jwt.py#L16

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

def add_data_to_queue(data, msg_group="notification"):
    dedup_id = hashlib.md5(str(data).encode('utf-8')).hexdigest()[:8] + str(time.time())[-14:-4]
    sqs = sqs = boto3.resource('sqs')
    queue = sqs.get_queue_by_name(QueueName='drifter-sqs.fifo')
    msg = json.dumps(data)
    response = queue.send_message(MessageBody=msg, MessageGroupId=msg_group, MessageDeduplicationId=dedup_id)
    print(response)
    return "failed" not in response.keys()

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

    #case: jwt token is owned by driver_id
        #subcase: making changes to trip
            #possible keys:
                #max_capacity
                #start_time
                #start_date
                #destination
                #origin
            #are there accepted riders?
            #if so, notify each one of the change.
        #subcase: making decision about rider
            #{"rider_id": 1, "accepted": true}
            #if this puts the trip at capacity
            #and another rider also requested to join
            #then reject other riders
    #case: jwt token is *not* owned by driver_id
        #{"rider_id" : 7}


def ret_error(msg, errcode=500):
    err_msg = {
        'statusCode' : errcode,
        'body': json.dumps(msg)
    }
    return err_msg

authorized_update_keys = [ "max_capacity", "start_time", "start_date", "destination", "origin" ]

def lambda_handler(event, context):

    trip_id = event.get("params",{}).get("path",{}).get("id",False)
    token = event.get("params",{}).get("header",{}).get("Authorization",False)

    if not token:
        return ret_error("missing token")
    if not trip_id:
        return ret_error("missing trip id")

    token_claims = verify_jwt_token(token)
    assert(token_claims != False)
    username = token_claims.get("cognito:username",False)

    if not username:
        return ret_error("username missing from token")

    request_body = event.get("body",{})
    request_keys = request_body.keys()

    response_message = ""
    trip_current_status = {}
    with connect_to_db() as db:
        with db.cursor() as cur:
            cur.execute("SELECT my_trip.trip_id, my_trip.driver_id, origin, destination," + \
            "start_date, start_time, max_capacity, count(rider_trip.rider_id) as rider_count," + \
            " users.username as driver_username FROM my_trip" + \
            " LEFT JOIN driver on driver.driver_id = my_trip.driver_id" + \
            " LEFT JOIN users on driver.user_id = users.user_id" + \
            " LEFT JOIN rider_trip on rider_trip.trip_id = my_trip.trip_id" + \
            " WHERE my_trip.trip_id = %s" + \
            " GROUP BY rider_trip.trip_id, my_trip.trip_id, users.username", (trip_id,) )
            trip_current_status = cur.fetchone();
            if "rider_id" in request_keys:
                if trip_current_status["rider_count"] >= trip_current_status["max_capacity"]
                    return ret_error("Trip At Capacity",403)
                if "accepted" in request_keys and username == trip_current_status["driver_username"]:
                    # accept user to trip
                    pass
                elif username != trip_current_status["driver_username"]:
                    # request to add trip
                    pass
                else:
                    return ret_error("missing key: accepted")
            elif username == trip_current_status["driver_username"]:
                # update trip for user
                pass
            else:
                return ret_error("Malformed Request")
            db.commit()
    print(trip_current_status)


    return {
        'statusCode': 200,
        'body': json.dumps(response_message),
    }
