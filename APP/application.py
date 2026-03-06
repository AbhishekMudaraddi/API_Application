"""
Elastic Beanstalk WSGI entry point.
EB looks for a module-level object named `application`.
"""
from app import app as application
