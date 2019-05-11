import boto3, json

def create_iam_role_for_config():
    global iam_role_arn

    iam_client = boto3.client('iam')
    iam_role = 'AWSServiceRoleForConfig'
    iam_roles = iam_client.list_roles()['Roles']
    iam_roles_list = []

    for i in range(len(iam_roles)):
        iam_roles_list.append(iam_roles[i]['RoleName'])

    if iam_role not in iam_roles_list:
        iam_client.create_service_linked_role(
            AWSServiceName = 'config.amazonaws.com',
            Description = 'Permits AWS Config List, Get & Describe permissions to all resources.'
        )

    iam_role_arn = iam_client.get_role(
        RoleName = iam_role
    )['Role']['Arn']

def select_s3_bucket():
    global selected_bucket, s3_client

    s3_client = boto3.client('s3')
    s3_buckets = s3_client.list_buckets()['Buckets']
    bucket_list = []

    for i in range(len(s3_buckets)):
        bucket_list.append(s3_buckets[i]['Name'])
        print('{0}. {1}'.format(i + 1, bucket_list[i]))

    bucket_num = input("Enter the list number of the bucket you want to store config files in: ")

    while True:
        try:
            bucket_num = int(bucket_num)
            break
        except ValueError:
            print("This is not a number.")
        try:
            bucket_num <= len(bucket_list)
            break
        except ValueError:
            print("The number must be less than or equal to the number of S3 buckets.")

    selected_bucket = bucket_list[bucket_num - 1]

def update_s3_bucket_policy():
    global aws_account_num

    aws_account_num = boto3.resource('iam').CurrentUser().arn.split(':')[4]

    s3_client.put_bucket_policy(
        Bucket='{}'.format(selected_bucket),
        Policy=json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "Allow Config access to the S3 bucket's ACL",
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "config.amazonaws.com"
                        },
                        "Action": "s3:GetBucketAcl",
                        "Resource": "arn:aws:s3:::{}".format(selected_bucket)
                    },
                    {
                        "Sid": "Allow Config to store config files in the S3 bucket",
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "config.amazonaws.com"
                        },
                        "Action": "s3:PutObject",
                        "Resource": "arn:aws:s3:::{0}/AWSLogs/{1}/*".format(selected_bucket, aws_account_num),
                        "Condition": {
                            "StringEquals": {
                                "s3:x-amz-acl": "bucket-owner-full-control"
                            }
                        }
                    }
                ]
            },
            indent = 1,
            default = str
        )
    )

def create_sns_topic():
    global current_region, sns_client, sns_topic_arn, sns_topic_name

    sns_client = boto3.client('sns')
    current_region = sns_client.meta.region_name
    sns_topic_name = input('Enter a name for an SNS topic: ')

    sns_topic = sns_client.create_topic(
        Name = '{}'.format(sns_topic_name),
        Attributes = {
            'Policy': json.dumps(
                {
                    "Version": "2008-10-17",
                    "Statement": [{
                        "Sid": "Allows the AWS account owner access to this SNS topic.",
                        "Effect": "Allow",
                        "Principal": {
                            "AWS": "*"
                        },
                        "Action": [
                            "SNS:GetTopicAttributes",
                            "SNS:SetTopicAttributes",
                            "SNS:AddPermission",
                            "SNS:RemovePermission",
                            "SNS:DeleteTopic",
                            "SNS:Subscribe",
                            "SNS:ListSubscriptionsByTopic",
                            "SNS:Publish",
                            "SNS:Receive"
                        ],
                        "Resource": "arn:aws:sns:{}:{}:{}".format(current_region, aws_account_num, sns_topic_name),
                        "Condition": {
                            "StringEquals": {
                            "AWS:SourceOwner": "{}".format(aws_account_num)
                            }
                        }
                    },
                    {
                        "Sid": "Allows Config access to this SNS topic.",
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "config.amazonaws.com"
                        },
                        "Action": [
                            "SNS:Publish"
                        ],
                        "Resource": "arn:aws:sns:{}:{}:{}".format(current_region, aws_account_num, sns_topic_name)
                    }]
                },
                indent = 1,
                default = str
            )
        }
    )

    sns_topic_arn = sns_topic['TopicArn']

def create_sns_subscription():
    email_add = input('Enter your email address: ')
    sns_client_token = input("Copy and paste the token at the end of the URL of the \
link you clicked to confirm the SNS subscription: ")

    sns_client.subscribe(
        TopicArn='{}'.format(sns_topic_arn),
        Protocol= 'email',
        Endpoint='{}'.format(email_add)
    )

    sns_client.confirm_subscription(
        TopicArn='{}'.format(sns_topic_arn),
        Token='{}'.format(sns_client_token)
    )

def record_configurations():
    global config_client, config_record_name

    config_client = boto3.client('config')
    config_record_name = 'aws_config_record'

    config_client.put_configuration_recorder(
        ConfigurationRecorder = {
            'name': config_record_name,
            'roleARN': iam_role_arn,
            'recordingGroup': {
                'allSupported': True,
                'includeGlobalResourceTypes': True
            }
        }
    )

    config_client.put_delivery_channel(
        DeliveryChannel = {
            'name': 'default-delivery-channel',
            's3BucketName': selected_bucket,
            'snsTopicARN': sns_topic_arn,
            'configSnapshotDeliveryProperties': {
                'deliveryFrequency': 'Three_Hours'
            }
        }
    )

    config_client.start_configuration_recorder(
        ConfigurationRecorderName = config_record_name
    )

def view_metadata():
    print(json.dumps(
        config_client.describe_configuration_recorders(
            ConfigurationRecorderNames = [
                config_record_name
            ]
        )['ConfigurationRecorders'],
        indent = 1,
        default = str
        )
    )

if __name__ == "__main__":
    create_iam_role_for_config()
    select_s3_bucket()
    update_s3_bucket_policy()
    create_sns_topic()
    create_sns_subscription()
    record_configurations()
    view_metadata()
