"""
Elastic Beanstalk WSGI entry point.

The Python platform on Elastic Beanstalk looks for a module-level
object named `application` as the WSGI callable. We import the Flask
app from `app.py` and expose it as `application` here.
"""

from app import app as application

