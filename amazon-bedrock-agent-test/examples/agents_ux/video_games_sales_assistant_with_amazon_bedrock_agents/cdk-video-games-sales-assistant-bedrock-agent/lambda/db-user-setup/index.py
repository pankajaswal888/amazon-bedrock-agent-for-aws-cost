"""
CloudFormation Custom Resource handler for creating a read-only PostgreSQL user
in Aurora Serverless v2 via the RDS Data API.

On Create/Update: Creates the readonly_user with password from the read-only secret,
grants SELECT on all tables in the public schema.
On Delete: No-op (user is dropped when the cluster is deleted).
"""

import json
import os
import logging
from urllib.request import Request, urlopen

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

rds_data = boto3.client("rds-data")
secrets_client = boto3.client("secretsmanager")


def send_cfn_response(event, context, status, reason=""):
    """Send response to CloudFormation pre-signed URL."""
    body = json.dumps({
        "Status": status,
        "Reason": reason or f"See CloudWatch Log Stream: {context.log_stream_name}",
        "PhysicalResourceId": event.get("PhysicalResourceId", context.log_stream_name),
        "StackId": event["StackId"],
        "RequestId": event["RequestId"],
        "LogicalResourceId": event["LogicalResourceId"],
    })
    req = Request(
        event["ResponseURL"],
        data=body.encode("utf-8"),
        headers={"Content-Type": ""},
        method="PUT",
    )
    urlopen(req)


def get_readonly_password():
    """Retrieve the read-only user password from Secrets Manager."""
    secret_arn = os.environ["READONLY_SECRET_ARN"]
    resp = secrets_client.get_secret_value(SecretId=secret_arn)
    secret = json.loads(resp["SecretString"])
    return secret["password"]


def execute_sql(sql, params=None):
    """Execute a SQL statement via RDS Data API using admin credentials."""
    kwargs = {
        "resourceArn": os.environ["CLUSTER_ARN"],
        "secretArn": os.environ["ADMIN_SECRET_ARN"],
        "database": os.environ["DATABASE_NAME"],
        "sql": sql,
    }
    if params:
        kwargs["parameters"] = params
    return rds_data.execute_statement(**kwargs)


def create_readonly_user(password):
    """Create the read-only user and grant SELECT privileges."""
    # Create user or update password if user already exists
    execute_sql(
        f"DO $$ BEGIN "
        f"IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'readonly_user') THEN "
        f"CREATE USER readonly_user WITH PASSWORD '{password}'; "
        f"ELSE "
        f"ALTER USER readonly_user WITH PASSWORD '{password}'; "
        f"END IF; "
        f"END $$;"
    )

    # Grant schema usage
    execute_sql("GRANT USAGE ON SCHEMA public TO readonly_user;")

    # Grant SELECT on all existing tables
    execute_sql("GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;")

    # Grant SELECT on future tables
    execute_sql(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO readonly_user;"
    )


def handler(event, context):
    """CloudFormation custom resource handler."""
    logger.info("Received event: %s", json.dumps(event))
    request_type = event.get("RequestType", "")

    try:
        if request_type in ("Create", "Update"):
            password = get_readonly_password()
            create_readonly_user(password)
            logger.info("Successfully created/updated readonly_user")

        # Delete is a no-op — user is dropped when cluster is deleted
        send_cfn_response(event, context, "SUCCESS")

    except Exception as e:
        logger.error("Failed to handle %s: %s", request_type, str(e))
        send_cfn_response(event, context, "FAILED", str(e))
