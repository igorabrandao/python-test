from __future__ import print_function
import os
import datetime
import json
import sys

# Append Opt for lambda layers
sys.path.append('/opt')

try:
    from wrapped_logging import log
except ImportError:
    print("failed importing wrapped_logging")
    import logging
    log = logging.getLogger("About")
except Exception, e:
    print ("Failed importing (no import error!): %s", e)

    import logging
    log = logging.getLogger("AboutNoAirbrake")
else:
    print("imported wrapped_logging")


def about_handler(event, context):
    """
    Returns some very simple data about the api
    :param event:
    :param context:
    :return:
    """
    log.info("Handling about request %s" % datetime.datetime.utcnow())

    code_version = os.environ.get('CODE_VERSION', None)

    if context:
        body = {
        "message": "This is the about endpoint for %s (event=%s)" % (context.client_context,
                                                                     type(event)),
        "version": context.function_version,
        "code_version": code_version}
    else:
        body = {
            "code_version": code_version,
            "no_context": True
        }

    if isinstance(event, dict) and event.get('requestContext', {}).get('stage', '').startswith('dev'):
        body['debug'] = {
            'triggering_event': event
        }

    return {
        'statusCode': 200,
        'body': json.dumps(body),
        'headers': {
            'Content-Type': 'application/json',
        }
    }
