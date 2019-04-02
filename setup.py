#File present to facilitate testing with
# python setup.py test

from setuptools import setup

setup(
    test_suite='nose.collector',
    tests_require=[
        'nose>=1.3.7',
        'boto3>=1.9.94',
        'moto>=1.3.7'
    ])