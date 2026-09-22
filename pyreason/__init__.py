# ruff: noqa: F403 F405 (Ignore Pyreason import * for public api)
from pyreason.pyreason import *
from importlib.metadata import version
from pkg_resources import get_distribution, DistributionNotFound

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    pass
