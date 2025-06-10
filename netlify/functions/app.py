"""Netlify function wrapper for the Flask app."""

import os
import sys

# Ensure the main project package is available when deployed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from webapp.app import app
from aws_lambda_wsgi import response

def handler(event, context):
    return response(app, event, context)
