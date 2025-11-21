"""
WSGI config for vibez project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
# This file contains the WSGI configuration required to serve up your
# web application at http://<your-username>.pythonanywhere.com/
# It works by setting the variable 'application' to a WSGI handler of some
# description.

import sys
import os

# Add your project directory to the sys.path
project_home = '/home/MICHAEL256/vibez-app'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables
os.environ['DJANGO_SETTINGS_MODULE'] = 'vibez.settings'

# Import Django and load the application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vibez.settings')

application = get_wsgi_application()
