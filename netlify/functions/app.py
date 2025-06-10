"""Netlify function wrapper for the Flask app."""

import os
import sys

# Ensure the bundled webapp package is on the import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'webapp')))

from webapp.app import app
from aws_lambda_wsgi import response

def handler(event, context):
    return response(app, event, context)
