import boto3, json

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
                        "Sid": "Allows Cloudwatch & Cloudwatch Events access to this SNS topic.",
                        "Effect": "Allow",
                        "Principal": {
                            "Service": ["cloudwatch.amazonaws.com",
                                         "events.amazonaws.com"
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

def select_instance_to_monitor():
    global selected_instance, ec2_instance_arn

    ec2_client = boto3.client('ec2')
    ec2_instances = ec2_client.describe_instances()['Reservations']

    for i in range(len(ec2_instances)):
        print('{0}. {1}'.format(i + 1, ec2_instances[i]['Instances'][0]['InstanceId']))

    instance_num = input('Enter the list number of the EC2 instance to monitor: ')

    while True:
        try:
            instance_num = int(instance_num)
            break
        except ValueError:
            print("This is not a number.")
        try:
            instance_num <= len(ec2_instances)
            break
        except ValueError:
            print("The number must be less than or equal to the number of EC2 instances.")

    selected_instance = ec2_instances[instance_num - 1]['Instances'][0]['InstanceId']
    ec2_instance_region = ec2_instances[instance_num - 1]['Instances'][0]['Placement']['AvailabilityZone'][:-1]

    ec2_instance_arn = 'arn:aws:ec2:{0}:{1}:instance/{2}'.format(ec2_instance_region, aws_account_num, selected_instance)

def create_cloudwatch_rule():
    global cloudwatch_event_client, rule_name

    cloudwatch_event_client = boto3.client('events')
    rule_name = 'cloudwatch_rule_for_ec2_instance'

    cloudwatch_event_client.put_rule(
        Name = '{}'.format(rule_name),
        EventPattern = '{}'.format(json.dumps(
                {
                    'Source': ['aws.ec2'],
                    'Resources': ['{}'.format(ec2_instance_arn)],
                    'DetailType': ['EC2 Instance State-change Notification'],
                    'Detail':
                    {
                        'instance-id': ['{}'.format(selected_instance)],
                        'state': ['pending']
                    }
                }
            )
        ),
        State = 'ENABLED',
        Description = 'Cloudwatch rule for EC2 instance.'
    )

    cloudwatch_event_client.put_targets(
        Rule = '{}'.format(rule_name),
        Targets = [
            {
                'Id': 'CloudwatchTargetForSNSTopic',
                'Arn': '{}'.format(sns_topic_arn)
            }
        ]
    )

def view_metadata():
    cloudwatch_rules = cloudwatch_event_client.list_rules()['Rules']

    for i in range(len(cloudwatch_rules)):
        if cloudwatch_rules[i]['Name'] == '{}'.format(rule_name):
            print(json.dumps(
                    cloudwatch_rules[i],
                    indent = 1,
                    default = str
                )
            )

if __name__ == "__main__":
    create_sns_topic()
    create_sns_subscription()
    select_instance_to_monitor()
    create_cloudwatch_rule()
    view_metadata()
