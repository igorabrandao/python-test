from __future__ import print_function
from boto3.session import Session
from botocore.vendored import requests
import urllib
import boto3
import zipfile
import tempfile
import botocore
import traceback
import json
import os

import sys
sys.path.append('/opt')
import  params

print('Loading function')

cf = boto3.client('cloudformation')
code_pipeline = boto3.client('codepipeline')
lambda_client = boto3.client('lambda')


def find_artifact(artifacts, name):
    """Finds the artifact 'name' among the 'artifacts'

    Args:
        artifacts: The list of artifacts available to the function
        name: The artifact we wish to use
    Returns:
        The artifact dictionary found
    Raises:
        Exception: If no matching artifact is found

    """
    for artifact in artifacts:
        if artifact['name'] == name:
            return artifact

    raise Exception('Input artifact named "{0}" not found in event'.format(name))


def get_stack_output(s3, artifact, file_in_zip):
    """Gets the template artifact

    Downloads the artifact from the S3 artifact store to a temporary file
    then extracts the zip and returns the file containing the CloudFormation
    template.

    Args:
        artifact: The artifact to download
        file_in_zip: The path to the file within the zip containing the template

    Returns:
        The CloudFormation template as a string

    Raises:
        Exception: Any exception thrown while downloading the artifact or unzipping it

    """
    tmp_file = tempfile.NamedTemporaryFile()
    bucket = artifact['location']['s3Location']['bucketName']
    key = artifact['location']['s3Location']['objectKey']

    print(bucket, key, file_in_zip)

    with tempfile.NamedTemporaryFile() as tmp_file:
        s3.download_file(bucket, key, tmp_file.name)
        with zipfile.ZipFile(tmp_file.name, 'r') as zip:
            return zip.read(file_in_zip)



def put_job_success(job, message):
    """Notify CodePipeline of a successful job

    Args:
        job: The CodePipeline job ID
        message: A message to be logged relating to the job status

    Raises:
        Exception: Any exception thrown by .put_job_success_result()

    """
    print('Putting job success')
    print(message)
    code_pipeline.put_job_success_result(jobId=job)


def put_job_failure(job, message):
    """Notify CodePipeline of a failed job

    Args:
        job: The CodePipeline job ID
        message: A message to be logged relating to the job status

    Raises:
        Exception: Any exception thrown by .put_job_failure_result()

    """
    print('Putting job failure')
    print(message)
    code_pipeline.put_job_failure_result(jobId=job, failureDetails={'message': message, 'type': 'JobFailed'})


def get_user_params(job_data):
    """Decodes the JSON user parameters and validates the required properties.

    Args:
        job_data: The job data structure containing the UserParameters string which should be a valid JSON structure

    Returns:
        The JSON parameters decoded as a dictionary.

    Raises:
        Exception: The JSON can't be decoded or a property is missing.

    """
    try:
        # Get the user parameters which contain the stack, artifact and file settings
        user_parameters = job_data['actionConfiguration']['configuration']['UserParameters']
        # Added this convert to the single quoted string to double quoted string.
        user_parameters = user_parameters.replace("'",'"')
        decoded_parameters = json.loads(user_parameters)

    except Exception as e:
        # We're expecting the user parameters to be encoded as JSON
        # so we can pass multiple values. If the JSON can't be decoded
        # then fail the job with a helpful message.
        raise Exception('UserParameters could not be decoded as JSON')
    '''
    if 'stack' not in decoded_parameters:
        # Validate that the stack is provided, otherwise fail the job
        # with a helpful message.
        raise Exception('Your UserParameters JSON must include the stack name')

    if 'artifact' not in decoded_parameters:
        # Validate that the artifact name is provided, otherwise fail the job
        # with a helpful message.
        raise Exception('Your UserParameters JSON must include the artifact name')

    if 'file' not in decoded_parameters:
        # Validate that the template file is provided, otherwise fail the job
        # with a helpful message.
        raise Exception('Your UserParameters JSON must include the template file name')

    '''
    return decoded_parameters


def setup_s3_client(job_data):
    """Creates an S3 client

    Uses the credentials passed in the event by CodePipeline. These
    credentials can be used to access the artifact bucket.

    Args:
        job_data: The job data structure

    Returns:
        An S3 client with the appropriate credentials

    """
    key_id = job_data['artifactCredentials']['accessKeyId']
    key_secret = job_data['artifactCredentials']['secretAccessKey']
    session_token = job_data['artifactCredentials']['sessionToken']

    session = Session(aws_access_key_id=key_id,
                      aws_secret_access_key=key_secret,
                      aws_session_token=session_token)
    return session.client('s3', config=botocore.client.Config(signature_version='s3v4'))


def enable_layer_cross_account_permisson(stack_output, layer_suffix_in_stack_output, cross_accounts):
    '''
    :param stack_output: This has all the info reagarding the newly created / updated lambda layers
    :param layer_suffix_in_stack_output: to filter out the necassary layes to allow the cross accout consumption
    :param cross_accounts: list of cross account which needs to consiume the lambda layers
    :return: None
    '''

    for key in stack_output.keys():
        if key.endswith(layer_suffix_in_stack_output):
            print("Adding permisson for layer: {}".format(stack_output[key]))
            layer_arn = stack_output[key]
            layer_name = layer_arn.split(':')[-2]

            layer_version = layer_arn.split(':')[-1]

            for account in cross_accounts:
                statement_id = "{}-{}-{}-permission".format(str(account), layer_name, layer_version)
                response = lambda_client.add_layer_version_permission(
                    LayerName=layer_name,
                    VersionNumber=int(layer_version),
                    StatementId=statement_id,
                    Action='lambda:GetLayerVersion',
                    Principal=str(account)
                )
                print(" Adding layer permission response {} ".format(response))


def lambda_handler(event, context):
    """The Lambda function handler

    This handler reads the input artifact and registers the deploy in airbrake.

    https://airbrake.io/docs/features/deploy-tracking/#deploy-tracking-with-the-api

    Args:
        event: The event passed by Lambda
        context: The context passed by Lambda

    """
    try:
        # Extract the Job ID
        print(event)
        job_id = event['CodePipeline.job']['id']

        # Extract the Job Data
        job_data = event['CodePipeline.job']['data']

        # Extract the params
        params = get_user_params(job_data)

        print(type(params))
        print(params)

        # Get the list of artifacts passed to the function
        artifacts = job_data['inputArtifacts']

        name = params['Name']

        # Get S3 client to access artifact with
        s3 = setup_s3_client(job_data)
        # Get the JSON Output file out of the artifact

        print("S3 client setup is completed")

        # Filering out the necessary artifacat from codepipeline event
        artifact_data = find_artifact(artifacts, 'BuildArtifact')
        print(artifacts, artifact_data)
        version = str(get_stack_output(s3, artifact_data, name).decode("utf-8")).rstrip('\n')

        print(version)


        PROJECT_ID = os.environ['PARAM_STORE_AIRBRAKE_PROJECT_ID_CHECKOUTAPI']
        PROJECT_KEY = os.environ['PARAM_STORE_AIRBRAKE_API_KEY_CHECKOUTAPI']
        ENVIRONMENT = params['TargetStage']
        REPOSITORY = os.environ["REPO_URL"]
        REVISION = version

        url = "https://airbrake.io/api/v4/projects/{}/deploys?key={}".format(PROJECT_ID, PROJECT_KEY)

        data = {"environment": ENVIRONMENT,  "repository": REPOSITORY,
                "revision": REVISION}

        headers = {
            "Content-Type": "application/json"
        }
        resp = requests.post(url, data=json.dumps(data), headers=headers)

        print (resp.status_code)

        if resp.status_code==201:
            put_job_success(job_id, "Success")
        else:
            put_job_failure(job_id, 'Airbrake Deploy Failed: ' + str(resp.text))

    except Exception as e:
        # If any other exceptions which we didn't expect are raised
        # then fail the job and log the exception message.
        print('Function failed due to exception.')
        print(e)
        traceback.print_exc()
        put_job_failure(job_id, 'Function exception: ' + str(e))

    print('Function complete.')
    return "Complete."

