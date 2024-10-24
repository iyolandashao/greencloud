from aws_cdk import (aws_lambda, aws_apigateway, aws_rds as rds, aws_ec2, aws_secretsmanager as secretsmanager, aws_iam as iam, Stack)
from constructs import Construct
#import os
#import boto3


class MyCdkProjectStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Define VPC (if needed for RDS)
        vpc = aws_ec2.Vpc(self, "MyVpc", max_azs=2, nat_gateways=1)

        # Create an RDS credentials secret in AWS Secrets Manager
        db_credentials_secret = secretsmanager.Secret(self, "DBCredentialsSecret",
            secret_name="rds-credentials",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                exclude_punctuation=True,
                include_space=False,
                generate_string_key="password",
                secret_string_template='{"username":"admin"}'
            )
        )

        # Define RDS Database
        db_instance = rds.DatabaseInstance(self, "MyRdsInstance",
                                engine=rds.DatabaseInstanceEngine.mysql(version=rds.MysqlEngineVersion.VER_8_0_39),
                                instance_type=aws_ec2.InstanceType.of(aws_ec2.InstanceClass.BURSTABLE3, aws_ec2.InstanceSize.MICRO),
                                vpc=vpc,
                                multi_az=False,
                                allocated_storage=20,
                                storage_type=rds.StorageType.GP2,
                                deletion_protection=False,
                                max_allocated_storage=100,
                                database_name='my_db',
                                iam_authentication=True,  # This enables IAM DB Authentication
                                publicly_accessible=False,
                                credentials=rds.Credentials.from_secret(db_credentials_secret)
                            )
        
        # Create an IAM user
        #lambda_user = iam.User(self, "LambdaUser")
        # Attach a policy to the user (customize this according to your needs)
        #rds_client = boto3.client("rds")  # Create an RDS client
        #db_instance_identifier = "database0"  # Describe the DB instance to get its resource ID
        #response = rds_client.describe_db_instances(DBInstanceIdentifier=db_instance_identifier)
        #dbi_resource_id = response['DBInstances'][0]['DbiResourceId'] # Extract the DB resource ID (DbiResourceId)
        #lambda_user.add_to_policy(iam.PolicyStatement(
        #    actions=["rds:Connect"],
        #    resources=["arn:aws:rds-db:region:accountid:resourceid/special_user"],  # You can specify resources more granularly
        #))

        # Define Lambda function
        lambda_fn = aws_lambda.Function(self, "MyFunction",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            handler="lambda_function.lambda_handler",
            code=aws_lambda.Code.from_asset("my-cdk-project/lambda"),
            environment={
                "DB_HOST": db_instance.instance_endpoint.socket_address.split(':')[0],
                "DB_NAME": "my_db",
                "DB_USER": db_credentials_secret.secret_value_from_json("username").to_string(),
                "DB_PASSWORD": db_credentials_secret.secret_value_from_json("password").to_string()
                },
            vpc=vpc
        )

        # Attach policies to the Lambda function's role
        lambda_fn.add_to_role_policy(iam.PolicyStatement(
        actions=["rds:Connect"],
        resources=["arn:aws:rds-db:region:accountid:resourceid/special_user"]  # Specify resources as needed
        ))

        # Grant Lambda permission to access the RDS
        db_instance.connections.allow_default_port_from(lambda_fn)

        # Define API Gateway
        api = aws_apigateway.LambdaRestApi(self, "MyApi",
            handler=lambda_fn,
            proxy=False
        )

        items = api.root.add_resource("items")
        items.add_method("GET")  # Get method
        items.add_method("POST")  # Post method