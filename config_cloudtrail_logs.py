import boto3, json, os

def create_sns_topic():
    global aws_account_num, current_region, sns_client, sns_topic_arn, sns_topic_name

    sns_client = boto3.client('sns')
    current_region = sns_client.meta.region_name
    aws_account_num = boto3.resource('iam').CurrentUser().arn.split(':')[4]
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
                        "Sid": "Allows Cloudtrail & S3 access to this SNS topic.",
                        "Effect": "Allow",
                        "Principal": {
                            "Service": ["cloudtrail.amazonaws.com",
                                         "s3.amazonaws.com"
                        ]},
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

def select_s3_bucket_to_monitor():
    global chosen_bucket, s3_client, s3_resource

    s3_client = boto3.client('s3')
    s3_resource = boto3.resource('s3')
    s3_buckets = s3_client.list_buckets()['Buckets']
    bucket_list = []

    for i in range(len(s3_buckets)):
        bucket_list.append(s3_buckets[i]['Name'])
        print('{0}. {1}'.format(i + 1, bucket_list[i]))

    bucket_num = input("Enter the list number of the bucket you want to monitor: ")

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

    chosen_bucket = bucket_list[bucket_num - 1]

def create_s3_bucket_to_store_cloudtrail_logs():
    global target_s3_bucket_name

    target_s3_bucket_name = '{0}-logs'.format(chosen_bucket)

    s3_client.create_bucket(
        Bucket = '{}'.format(target_s3_bucket_name),
        CreateBucketConfiguration = {
        'LocationConstraint': '{}'.format(current_region)
        }
    )

def update_s3_bucket_policy():
    s3_client.put_bucket_policy(
        Bucket='{}'.format(target_s3_bucket_name),
        Policy=json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "Allow CloudTrail access to the S3 bucket's ACL",
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "cloudtrail.amazonaws.com"
                        },
                        "Action": "s3:GetBucketAcl",
                        "Resource": "arn:aws:s3:::{}".format(target_s3_bucket_name)
                    },
                    {
                        "Sid": "Allow Cloudtrail to store logs in the S3 bucket",
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "cloudtrail.amazonaws.com"
                        },
                        "Action": "s3:PutObject",
                        "Resource": "arn:aws:s3:::{0}/AWSLogs/{1}/*".format(target_s3_bucket_name, aws_account_num),
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

def config_cloudtrail_logs():
    global cloudtrail_client, cloudtrail_name

    cloudtrail_client = boto3.client('cloudtrail')
    cloudtrail_name = 'cloudtrail-logs-stored-in-s3-bucket'

    cloudtrail_client.create_trail(
        Name = '{}'.format(cloudtrail_name),
        S3BucketName = '{}'.format(target_s3_bucket_name),
        SnsTopicName = '{}'.format(sns_topic_name),
        IncludeGlobalServiceEvents = True,
        IsMultiRegionTrail = True,
        EnableLogFileValidation = True
    )

    cloudtrail_client.start_logging(
        Name = '{}'.format(cloudtrail_name)
    )

    cloudtrail_client.put_event_selectors(
        TrailName = '{}'.format(cloudtrail_name),
        EventSelectors = [
            {
                'ReadWriteType': 'All',
                'IncludeManagementEvents': True,
                'DataResources': [
                    {
                        'Type': 'AWS::S3::Object',
                        'Values': [
                            'arn:aws:s3:::{}/'.format(chosen_bucket),
                        ]
                    },
                ]
            },
        ]
    )

def view_metadata():
    print(json.dumps(
                cloudtrail_client.describe_trails(
                    trailNameList = [
                        '{}'.format(cloudtrail_name)
                ])['trailList'],
                indent = 1,
                default = str
        )
    )

if __name__ == "__main__":
    create_sns_topic()
    create_sns_subscription()
    select_s3_bucket_to_monitor()
    create_s3_bucket_to_store_cloudtrail_logs()
    update_s3_bucket_policy()
    config_cloudtrail_logs()
    view_metadata()
