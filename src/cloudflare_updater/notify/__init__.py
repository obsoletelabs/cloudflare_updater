"""__init__.py for notify library"""
# from importlib.metadata import version

from .send_email_notification import send_email_via_smtp

# __version__ = version("")
__all__ = ["send_email_via_smtp"]
