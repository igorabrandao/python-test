import boto3
import json
import cfnresponse
import os
import time


# Enviroment Variable validation function
def get_mandatory_evar(evar_name):
    if not evar_name in os.environ:
        raise RuntimeError("Missing environment variable: {}".format(evar_name))
    return os.environ[evar_name]


def lambda_handler(event, context):
    print (str(event))
    print (json.dumps(event))
    responseData = {}
    res = False
    reason = "NA"
    try:
        resource_name = event['LogicalResourceId']
        if event['RequestType'] == 'Create' or event['RequestType'] == 'Update':
            delay_in_secs = int(event['ResourceProperties']['DelaySeconds'])

            if delay_in_secs > 899:
                delay_in_secs = 899

            print("Delaying the resource creation for  {} secs ".format(str(delay_in_secs)))

            time.sleep(delay_in_secs)

            res = True

        elif event['RequestType'] == 'Delete':
            res = True
            reason = 'Delete is Not supported. Hence Gracefully returning.'
        else:
            res = False
            reason = "Unknown operation: " + event['RequestType']
        responseData['Reason'] = reason
    except Exception as e:
        print ("Exception while updating stackset {}".format(str(e)))
        res = False
        responseData['Reason'] = str(e)

    if res:
        cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData, resource_name)
    else:
        cfnresponse.send(event, context, cfnresponse.FAILED, responseData, resource_name)
