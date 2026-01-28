# Ingestion modules for parsing Evernote and email exports
from .evernote_parser import EvernoteParser
from .email_parser import EmailParser

__all__ = ["EvernoteParser", "EmailParser"]
