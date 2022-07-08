import json
from boto3.session import Session

def connect_to_aws():
    global iam_client

    access_key = input("Copy and paste the compromised AWS access key ID here: ")
    secret_key = input("Copy and paste the compromised AWS secret access key here: ")
    region = input("Enter a region here: ")

    while True:
        try:
            aws_regions = [
                'ap-east-1', 'ap-northeast-1', 'ap-northeast-2', 'ap-south-1', 'ap-southeast-1', 'ap-southeast-2', 'ca-central-1', 
                'cn-north-1', 'cn-northwest-1', 'eu-central-1', 'eu-north-1', 'eu-west-1', 'eu-west-2', 'eu-west-3', 
                'sa-east-1', 'us-east-1', 'us-east-2', 'us-gov-east-1', 'us-gov-west-1', 'us-west-1', 'us-west-2'
            ]
            region in aws_regions
            break
        except ValueError:
            print("Enter a valid AWS region.")

    session = Session(
        aws_access_key_id='{}'.format(access_key),
        aws_secret_access_key='{}'.format(secret_key),
        region_name='{}'.format(region)
    )

    # Connect to the AWS IAM service.
    iam_client = session.client('iam')

def create_iam_user():
    get_iam_user = iam_client.list_users()
    user_list = []

    # Put the IAM users in the 'user_list' list.
    for i in range(len(get_iam_user['Users'])):
        user_list.append(get_iam_user['Users'][i]['UserName'])
    
    # Create the user if it has not been created already.
    iam_user_first_name = input("Enter a first name for the IAM user: ")
    iam_user_last_name = input("Enter a last name for the IAM user: ")
    iam_user_full_name = "{} {}".format(iam_user_first_name, iam_user_last_name)

    if iam_user_full_name not in user_list:
        create_iam_user = iam_client().create_user(
            UserName=iam_user_full_name,
            # Give the user permissions to access the EC2 service.
            PermissionsBoundary= {
                'PermissionsBoundaryType': 'PermissionsBoundaryPolicy',
                'PermissionsBoundaryArn': {
                    "Version": "2012-10-17",
                    "Statement": [{
                        "Effect": "Allow",
                        "Action": [
                            "ec2:AuthorizeSecurityGroupIngress",
                            "ec2:AuthorizeSecurityGroupEgress",
                            "ec2:RevokeSecurityGroupIngress",
                            "ec2:RevokeSecurityGroupEgress"
                        ]
                    }]
                }
            }
        )

    print(create_iam_user)

if __name__ == "__main__":
    connect_to_aws()
    create_iam_user()
