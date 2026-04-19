"""
Production settings for linkding webapp
"""

# ruff: noqa

# Start from development settings
# noinspection PyUnresolvedReferences
import os

from django.core.management.utils import get_random_secret_key
from .base import *

# Turn of debug mode
DEBUG = False

# Serve collected static files via WhiteNoise (bundle.js, theme css, favicons).
# Runtime-generated files under data/favicons and data/previews are served by a
# dynamic view registered in bookmarks.urls at /static/<filename>, which WhiteNoise
# lets fall through when it does not find the file in STATIC_ROOT.
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# Try read secret key from file
try:
    with open(os.path.join(BASE_DIR, "data", "secretkey.txt")) as f:
        SECRET_KEY = f.read().strip()
except:
    SECRET_KEY = get_random_secret_key()

# Set ALLOWED_HOSTS
# By default look in the HOST_NAME environment variable, if that is not set then allow all hosts
host_name = os.environ.get("HOST_NAME")
if host_name:
    ALLOWED_HOSTS = [host_name]
else:
    ALLOWED_HOSTS = ["*"]

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "{asctime} {levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "simple"}},
    "root": {
        "handlers": ["console"],
        "level": "WARN",
    },
    "loggers": {
        "bookmarks": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
        "huey": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
    },
}

# Import custom settings
# noinspection PyUnresolvedReferences
from .custom import *
