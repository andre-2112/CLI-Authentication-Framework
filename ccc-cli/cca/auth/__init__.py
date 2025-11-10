"""
CCA Authentication Module
Handles Cognito authentication and credential management.
"""

from .cognito import CognitoAuthenticator
from .credentials import save_credentials, remove_credentials

__all__ = ['CognitoAuthenticator', 'save_credentials', 'remove_credentials']
