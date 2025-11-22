import sys
import logging
import pymysql
import json
import os

# rds settings
user_name = os.getenv("USER_NAME")
password = os.getenv("PASSWORD")
rds_proxy_host = os.getenv("RDS_PROXY_HOST")
db_name = os.getenv("DB_NAME")

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# create the database connection outside of the handler to allow connections to be
# re-used by subsequent function invocations.
try:
    logger.info("Attempting to connect to the database")
    conn = pymysql.connect(host=rds_proxy_host, user=user_name, password=password, database=db_name, connect_timeout=5)
except pymysql.MySQLError as e:
    logger.error("ERROR: Unexpected error: Could not connect to MySQL instance.")
    logger.error(e)
    sys.exit(1)

logger.info("SUCCESS: Connection to RDS for MySQL instance succeeded")

def lambda_handler(event, context):
    item_count = 0


    api_body = json.loads(event['body'])
    logger.info(f"Received event: {json.dumps(api_body)}")

    keys = api_body.keys()
    values = []
    sql_columns = ''
    sql_placeholders = ''
    

    for key in keys:
        sql_columns = ', '.join(keys)
        sql_placeholders = ', '.join(['%s'] * len(keys))

        if isinstance(api_body[key], dict) or key == 'Skills':
            values.append(json.dumps(api_body[key]))
        elif isinstance(api_body[key], list):
            values.append(','.join(api_body[key]))
        else:
            values.append(api_body[key])


    #sql_string = f"INSERT INTO Servants(Name, Skills, Church, Availability, ContactInfo) values(%s, %s, %s, %s)"
    sql_string = f"INSERT INTO Servants({sql_columns}) values({sql_placeholders})"

    try:
        print(f"Executing SQL statement: {sql_string} {values}")
        with conn.cursor() as cur:
            cur.execute(sql_string, values)  
            conn.commit()
            cur.execute("SELECT * FROM Servants")
            logger.info("The following items have been added to the database:")
            for row in cur:
                item_count += 1
                logger.info(row)

        return {
            "statusCode": 200,
            "body": f"Added {item_count} items to RDS for MySQL table"
        }
    except Exception as e:
        logger.error(f"Error executing SQL or processing event: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }