"""
WSGI config for TheaterWin project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/wsgi/
"""

import os,sys

from django.core.wsgi import get_wsgi_application

# 개발 용
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TheaterWin.settings')
#
# application = get_wsgi_application()


# 배포용 (apache2)
path = os.path.abspath(__file__+'/../..')
if path not in sys.path :
        sys.path.append(path)
from django.core.wsgi import get_wsgi_application
os.environ.setdefault("DJANGO_SETTINGS_MODULE","TheaterWin.settings")
application = get_wsgi_application()
