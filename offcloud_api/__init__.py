"""
offcloud_api - Python client for the Offcloud API

A comprehensive client library for interacting with Offcloud's download service,
supporting instant downloads, cloud storage, remote transfers, and local file downloads.
"""

from .client import OffcloudAPI
from .exceptions import (
    OffcloudError,
    HTTPError,
    AuthError,
    NotFoundError,
    RateLimitError,
    BadRequestError,
    ServerError,
    TemporaryError,
    FeatureNotAvailableError,
    DownloadError,
)

__version__ = "0.3.0"
__author__ = "apacalpa"
__email__ = "me@apacalpa.com"

__all__ = [
    "OffcloudAPI",
    "OffcloudError",
    "HTTPError",
    "AuthError",
    "NotFoundError",
    "RateLimitError",
    "BadRequestError",
    "ServerError",
    "TemporaryError",
    "FeatureNotAvailableError",
    "DownloadError",
]
