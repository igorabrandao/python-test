import unittest
import botocore.session
from botocore.stub import Stubber

import boto3

from about_handler import about_handler
from moto import mock_lambda

# Based on https://stackoverflow.com/q/53523118
# Additional resources:
# http://joshuaballoch.github.io/testing-lambda-functions/
# https://botocore.amazonaws.com/v1/documentation/api/latest/reference/stubber.htmls

"""
class AboutCaseMocked(unittest.TestCase):

    @mock_lambda
    def test_something(self):
        CLIENT = boto3.client('lambda', region_name='us-west-2')


        response = function_code.invoke_lambda()

        self.assertEqual(True, False)
"""


class AboutCaseUnit(unittest.TestCase):


    def test_about(self):
        #apigw2 = botocore.session.get_session().create_client('apigatewayv2')
        #stubber = Stubber(apigw2)
        about_handler(None, None)


if __name__ == '__main__':
    unittest.main()
