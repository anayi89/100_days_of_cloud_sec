from boto3.session import Session

def view_ec2_assets_in_each_region():
    access_key = input("Copy and paste the compromised AWS access key ID here: ")
    secret_key = input("Copy and paste the compromised AWS secret access key here: ")
    aws_regions = [
        'ap-northeast-1', 'ap-northeast-2', 'ap-south-1', 'ap-southeast-1',
        'ap-southeast-2', 'ca-central-1', 'eu-central-1', 'eu-north-1',
        'eu-west-1', 'eu-west-2', 'eu-west-3', 'sa-east-1',
        'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2'
    ]

    for i in range(len(aws_regions)):
        session = Session(
            aws_access_key_id='{}'.format(access_key),
            aws_secret_access_key='{}'.format(secret_key)
        )

        ec2_client = session.client(
            'ec2',
            region_name = '{}'.format(aws_regions[i])
        )

        ec2_instances = ec2_client.describe_instances()['Reservations']
        ec2_security_groups = ec2_client.describe_security_groups()['SecurityGroups']
        ec2_subnets = ec2_client.describe_subnets()['Subnets']
        ec2_vpcs =  ec2_client.describe_vpcs()['Vpcs']

        print('Region {0} has {1} instances, {2} security groups, {3} subnets & {4} VPCs.'.format(
                aws_regions[i],
                len(ec2_instances),
                len(ec2_security_groups),
                len(ec2_subnets),
                len(ec2_vpcs)
            )
        )

if __name__ == "__main__":
    view_ec2_assets_in_each_region()
