from notificationsLib import antikvariatjusticna_notification, gymbeam_notification, status_notification
# from datetime import datetime, timezone, timedelta

def lambda_handler(event, context):
    responses = []
    
    antikvariatjusticna_notification()
    # responses.append(antikvariatjusticna_notification()['statusCode'])
    # responses.append(gymbeam_notification()['statusCode'])
    
    """
    if '200' not in responses:
        status_notification()
    """



if __name__ ==  "__main__":
    lambda_handler(None, None)
    