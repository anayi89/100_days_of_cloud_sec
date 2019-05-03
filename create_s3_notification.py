import boto3, json, sys, time

def create_sns_topic():
    global sns_client, sns_topic_arn

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
                        "Sid": "Allows S3 access to this SNS topic.",
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "s3.amazonaws.com"
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

def select_s3_bucket():
    global chosen_bucket, s3_client

    s3_client = boto3.client('s3')
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

def create_s3_bucket_notification():
    s3_bucket_events = ['s3:ReducedRedundancyLostObject',
                        's3:ObjectCreated:*',
                        's3:ObjectCreated:Put',
                        's3:ObjectCreated:Post',
                        's3:ObjectCreated:Copy',
                        's3:ObjectCreated:CompleteMultipartUpload',
                        's3:ObjectRemoved:*',
                        's3:ObjectRemoved:Delete',
                        's3:ObjectRemoved:DeleteMarkerCreated',
                        's3:ObjectRestore:Post',
                        's3:ObjectRestore:Completed']

    for i in range(len(s3_bucket_events)):
        s3_client.put_bucket_notification_configuration(
            Bucket='{}'.format(chosen_bucket),
            NotificationConfiguration={
                'TopicConfigurations': [
                    {
                        'TopicArn': '{}'.format(sns_topic_arn),
                        'Events': [
                            '{}'.format(s3_bucket_events[i])
                        ]
                    }
                ]
            }
        )

        print("Wait 30 seconds each for the S3 bucket event notifications to complete.")
        t = 30
        while t >= 0:
            sys.stdout.write('\r{} '.format(t))
            t -= 1
            sys.stdout.flush()
            time.sleep(1)
    
        print("\n")
    
        print(json.dumps(
            s3_client.get_bucket_notification_configuration(
                Bucket='{}'.format(chosen_bucket))['TopicConfigurations'],
            indent = 1,
            default = str
            )
        )

if __name__ == "__main__":
    create_sns_topic()
    create_sns_subscription()
    select_s3_bucket()
    create_s3_bucket_notification()
