"""
Development settings for TRIZ-Solver project.
"""
from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ["*"]

# ---------- CORS ----------
CORS_ALLOW_ALL_ORIGINS = True

# ---------- DRF (add session auth for browsable API) ----------
REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = [  # noqa: F405
    "rest_framework_simplejwt.authentication.JWTAuthentication",
    "rest_framework.authentication.SessionAuthentication",
]
