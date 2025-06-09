from webapp.app import app
from aws_lambda_wsgi import response

def handler(event, context):
    return response(app, event, context)
