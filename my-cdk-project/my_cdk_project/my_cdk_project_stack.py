from aws_cdk import aws_lambda, aws_apigateway, aws_rds as rds, aws_ec2, Stack
from constructs import Construct

myvpc = ""
myapi = ""
mydb = ""
DB_HOST = ""
DB_NAME = mydb
DB_USER = ""
DB_PASSWORD = ""

class MyCdkProjectStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Define VPC (if needed for RDS)
        vpc = aws_ec2.Vpc(self, myvpc, max_azs=2, nat_gateways=1)

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
                                          database_name=mydb,
                                          #removal_policy=RemovalPolicy.DESTROY
                                          )

        # Define Lambda function
        lambda_fn = aws_lambda.Function(self, "MyFunction",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            handler="lambda_function.lambda_handler",
            code=aws_lambda.Code.from_asset("my-cdk-project/lambda"),
            environment={
                "DB_HOST": DB_HOST,
                "DB_NAME": DB_NAME,
                "DB_USER": DB_USER,
                "DB_PASSWORD": DB_PASSWORD
            },
            vpc=vpc
        )

        # Grant Lambda permission to access the RDS
        db_instance.connections.allow_default_port_from(lambda_fn)

        # Define API Gateway
        api = aws_apigateway.LambdaRestApi(self, myapi,
            handler=lambda_fn,
            proxy=False
        )

        items = api.root.add_resource("items")
        items.add_method("GET")  # Get method
        items.add_method("POST")  # Post method