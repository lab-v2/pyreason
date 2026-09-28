# ruff: noqa: F403 F405 (Ignore Pyreason import * for public api)
from pyreason.pyreason import *
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    # package is not installed
    pass
