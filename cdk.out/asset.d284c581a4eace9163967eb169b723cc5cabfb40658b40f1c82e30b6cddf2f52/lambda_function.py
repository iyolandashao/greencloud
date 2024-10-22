import os
import pymysql
import json

db_host = os.environ['DB_HOST']
db_username = os.environ['DB_USER']
db_password = os.environ['DB_PASSWORD']
db_name = os.environ['DB_NAME']


def connect_to_rds():
    connection = pymysql.connect(host=db_host, user=db_username, password=db_password, db=db_name, connect_timeout=5)
    return connection

def lambda_handler(event, context):
    conn = connect_to_rds()
    method = event['httpMethod']
    if method == 'POST':
        body = event['body']
        if not body:
            return {'statusCode': 400,
                    'body': json.dumps('Missing body in POST request')
                   }
        body = json.loads(body)
        # Get the userid from the parsed body
        user_id = body.get('userid')
        message = body.get('content')
        try:
            with conn.cursor() as cursor:
                sql = "INSERT INTO message (userid, content) VALUES (%s, %s)"
                cursor.execute(sql, (user_id, message))
                conn.commit()
            return {'statusCode': 200,
                    'body': json.dumps(f"POST received: User ID: {user_id}, Message: {message}")
                    }
        except Exception as e:
            return {'statusCode': 500,
                    'body': json.dumps(f"Error: {str(e)}")
                    }
    elif method == 'GET':
        params = event.get('queryStringParameters',{})
        user_id = params.get('userid')
        if not user_id:
            return {'statusCode': 400,
                    'body': json.dumps('Missing userid in GET query parameters')
                   }
        with conn.cursor() as cursor:
            cursor.execute("USE my_db")
            sql = "SELECT content FROM message WHERE userid = %s"
            cursor.execute(sql, (user_id,))
            result = cursor.fetchone()

            if result:
                message = result[0]
                return {
                    "statusCode": 200,
                    "body": json.dumps(f"The message of userId {user_id}: {message}")
                }
            else:
                return {
                    "statusCode": 404,
                    "body": json.dumps({"error": "No message found for this user"})
                }
               
    else:
        return {'statusCode': 405,  # Method Not Allowed
                'body': json.dumps(f"Unsupported method: {method}")
               }