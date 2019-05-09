import boto3, json
from time import strftime

def create_iam_role_for_s3_bucket():
    global iam_client

    iam_client = boto3.client('iam')
    iam_role_name = 'iam_access_to_traffic_logs'
    iam_policy_name = 'NetworkTrafficLogsAccess'

    iam_client.create_role(
        RoleName = '{}'.format(iam_role_name),
        Description = 'Allows S3 buckets access to network traffic logs.',
        Path = '/',
        AssumeRolePolicyDocument = json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": {
                    "Effect": "Allow",
                    "Principal": {"Service": "s3.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            },
            indent = 1,
            default = str
        )
    )

    iam_policy = iam_client.create_policy(
        PolicyName = '{}'.format(iam_policy_name),
        Description = 'Allows access to network traffic logs.',
        Path = '/',
        PolicyDocument = json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogDelivery",
                        "logs:DeleteLogDelivery"
                        ],
                    "Resource": "*"
                    }
                ]
            },
            indent = 1,
            default = str
        )
    )

    iam_policy_arn = iam_policy['Policy']['Arn']

    iam_client.attach_role_policy(
        RoleName = '{}'.format(iam_role_name),
        PolicyArn = '{}'.format(iam_policy_arn)
    )

def select_s3_bucket():
    global s3_client, selected_bucket

    s3_client = boto3.client('s3')
    s3_buckets = s3_client.list_buckets()['Buckets']

    for i in range(len(s3_buckets)):
        print('{0}. {1}'.format(i + 1, s3_buckets[i]['Name']))
    
    bucket_num = input('Enter the list number of the S3 bucket to store flow logs in: ')

    while True:
        try:
            bucket_num = int(bucket_num)
            break
        except ValueError:
            print("This is not a number.")
        try:
            bucket_num <= len(s3_buckets)
            break
        except ValueError:
            print("The number must be less than or equal to the number of S3 buckets.")
    
    selected_bucket = s3_buckets[bucket_num - 1]['Name']

def create_s3_bucket_policy_for_logs():
    global s3_bucket_arn

    current_date_time = strftime("%m%d%Y%I%M%S")
    aws_account_num = boto3.resource('iam').CurrentUser().arn.split(':')[4]
    s3_bucket_arn = 'arn:aws:s3:::{0}/{1}/awslogs/{2}/'.format(selected_bucket, current_date_time, aws_account_num)

    s3_client.put_bucket_policy(
        Bucket = '{}'.format(selected_bucket),
        Policy = json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "AWSLogDeliveryWrite",
                        "Effect": "Allow",
                        "Principal": {"Service": "delivery.logs.amazonaws.com"},
                        "Action": "s3:PutObject",
                        "Resource": "{}*".format(s3_bucket_arn),
                        "Condition": {"StringEquals": {"s3:x-amz-acl": "bucket-owner-full-control"}}
                    },
                    {
                        "Sid": "AWSLogDeliveryAclCheck",
                        "Effect": "Allow",
                        "Principal": {"Service": "delivery.logs.amazonaws.com"},
                        "Action": "s3:GetBucketAcl",
                        "Resource": "arn:aws:s3:::{}".format(selected_bucket)
                    }
                ]
            },
            indent = 1,
            default = str
        )
    )

def select_network_device():
    global device_type_num, ec2_client, select_network_device

    ec2_client = boto3.client('ec2')

    print('1. network interface\n2. VPC\n3. subnet')
    device_type_num = input('Enter the list number of the network device you want to monitor: ')

    while True:
        try:
            device_type_num = int(device_type_num)
            break
        except ValueError:
            print("This is not a number.")
        try:
            device_type_num <= 3
            break
        except ValueError:
            print("Enter either numbers 1, 2 or 3.")
    
    if device_type_num == 1:
        ec2_network_interfaces = ec2_client.describe_network_interfaces()['NetworkInterfaces']

        for i in range(len(ec2_network_interfaces)):
            print('{0}. {1}'.format(i + 1, ec2_network_interfaces[i]['NetworkInterfaceId']))
        
        network_interface_num = input('Enter the list number of the network interface you want to monitor: ')
    
        while True:
            try:
                network_interface_num = int(network_interface_num)
                break
            except ValueError:
                print("This is not a number.")
            try:
                network_interface_num <= len(ec2_network_interfaces)
                break
            except ValueError:
                print("The number must be less than or equal to the number of network interfaces.")

        select_network_device = ec2_network_interfaces[network_interface_num - 1]['NetworkInterfaceId']
    elif device_type_num == 2:
        ec2_vpcs = ec2_client.describe_vpcs()['Vpcs']

        for i in range(len(ec2_vpcs)):
            print('{0}. {1}'.format(i + 1, ec2_vpcs[i]['VpcId']))
        
        vpc_num = input('Enter the list number of the VPC you want to monitor: ')
    
        while True:
            try:
                vpc_num = int(vpc_num)
                break
            except ValueError:
                print("This is not a number.")
            try:
                vpc_num <= len(ec2_vpcs)
                break
            except ValueError:
                print("The number must be less than or equal to the number of VPCs.")

        select_network_device = ec2_vpcs[vpc_num - 1]['VpcId']
    else:
        ec2_subnets = ec2_client.describe_subnets()['Subnets']

        for i in range(len(ec2_subnets)):
            print('{0}. {1}'.format(i + 1, ec2_subnets[i]['SubnetId']))
        
        subnet_num = input('Enter the list number of the subnet you want to monitor: ')
    
        while True:
            try:
                subnet_num = int(subnet_num)
                break
            except ValueError:
                print("This is not a number.")
            try:
                subnet_num <= len(ec2_subnets)
                break
            except ValueError:
                print("The number must be less than or equal to the number of subnets.")

        select_network_device = ec2_subnets[subnet_num - 1]['SubnetId']

def create_flow_logs():
    if device_type_num == 1:
        resource_type = 'NetworkInterface'
    elif device_type_num == 2:
        resource_type = 'VPC'
    else:
        resource_type = 'Subnet'

    ec2_client.create_flow_logs(
        ResourceIds = ['{}'.format(select_network_device)],
        ResourceType = '{}'.format(resource_type),
        TrafficType = 'ALL',
        LogDestinationType = 's3',
        LogDestination = '{}'.format(s3_bucket_arn)
    )

def view_metadata():
    print(json.dumps(
            ec2_client.describe_flow_logs(
                Filters=[
                    {
                        'Name': 'resource-id',
                        'Values': [
                            '{}'.format(select_network_device)
                        ]
                    }
                ]
            )['FlowLogs'],
            indent = 1,
            default = str
        )
    )

if __name__ == "__main__":
    create_iam_role_for_s3_bucket()
    select_s3_bucket()
    create_s3_bucket_policy_for_logs()
    select_network_device()
    create_flow_logs()
    view_metadata()
