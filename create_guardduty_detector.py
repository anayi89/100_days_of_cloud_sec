import boto3, sys, time

def create_gd_detector():
    global gd_client, detector_id

    gd_client = boto3.client('guardduty')
    gd_detector = gd_client.list_detectors()['DetectorIds']

    # Create a detector if one does not already exist.
    # Only one detector is allowed to be created.
    if len(gd_detector) == 0:
        gd_client.create_detector(
            Enable = True,
            FindingPublishingFrequency = 'ONE_HOUR'
        )

    print("Wait 3 minutes for the detector to fully load.")
    t = 180
    while t >= 0:
        sys.stdout.write('\r{} '.format(t))
        t -= 1
        sys.stdout.flush()
        time.sleep(1)

    detector_id = gd_detector[0]

def view_metadata():
    detector_list = list(gd_client.get_detector(DetectorId = detector_id).items())[1:]
    print('\n' + 'Detector ID: ' + detector_id)
    for i in range(len(detector_list)):
        print(detector_list[i])

if __name__ == "__main__":
    create_gd_detector()
    view_metadata()
