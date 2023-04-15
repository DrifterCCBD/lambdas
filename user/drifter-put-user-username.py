import json
import psycopg
from psycopg.rows import dict_row
import os
import urllib.request
import time
from jose import jwk, jwt
from jose.utils import base64url_decode


authorized_keys = ['firstName', 'lastName', 'address', 'city', 'country', 'zip', 'dob', 'gender']

key_to_table= {
    'firstName': "users",
    'lastName': "users", 
    'address': "addresses", 
    'city': "addresses", 
    'country': "addresses", 
    'zip': "addresses", 
    'dob': "users", 
    'gender': "users"
}

form_key_to_table_key= {
    'firstName': "first_name",
    'lastName': "last_name", 
    'address': "street_name_and_number", 
    'city': "city", 
    'country': "country", 
    'zip': "zip_code", 
    'dob': "dob", 
    'gender': "gender"
}

final_query = {
    "users" : "where username = %s",
    "addresses" : "where user_id = (select user_id from users where username = %s)"
}


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

def build_query(table,keys):
    query = "UPDATE {} SET ".format(table)
    query += "{} = %s".format(" = %s, ".join(keys))
    return query + final_query[table]

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
    
    request_body = event.get("body",{})
    
    request_keys = request_body.keys()
    
    assert(len(list(request_keys))>0)
    
    query_keys = {"users": [], "addresses": []}
    query_values = {"users": [], "addresses": []}
    
    for key in request_keys:
        assert(key in authorized_keys)
        if request_body[key] != "":
            table = key_to_table[key]
            query_keys[table].append(form_key_to_table_key[key])
            query_values[table].append(request_body[key])
    
    username = event.get("params",{}).get("path",{}).get("username",False)
    
    assert(username != False)
    
    token = event.get("params",{}).get("header",{}).get("Authorization","")
    token_claims = verify_jwt_token(token)
    assert(token_claims["cognito:username"] == username)
    print(token_claims)
    user_is_authorized = token_claims != False
    
    assert(user_is_authorized)
    

    with psycopg.connect(postgres_connect_string, row_factory=dict_row) as db:
       with db.cursor() as cur:
           for table in query_keys.keys():
               if len(list(query_keys[table])) > 0:
                   query = build_query(table,query_keys[table])
                   query_values[table].append(username)
                   print(query, query_values[table])
                   cur.execute(query, query_values[table])
           db.commit()
               
    
    return "success"


