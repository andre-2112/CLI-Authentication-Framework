"""
CCA SDK - Cloud CLI Access
A modular SDK for secure AWS authentication using Amazon Cognito.

Usage:
    from cca import CognitoAuthenticator, load_config, save_config
    from cca.auth import save_credentials
    from cca.aws import get_user_history, list_user_resources, get_user_permissions

Example:
    # Load configuration
    config = load_config()

    # Authenticate
    auth = CognitoAuthenticator(config)
    tokens = auth.authenticate(username, password)

    # Get AWS credentials
    aws_creds = auth.get_aws_credentials(tokens['IdToken'])

    # Save credentials
    save_credentials(aws_creds, profile='cca')

    # Use AWS operations
    session = boto3.Session(profile_name='cca')
    events, source = get_user_history(session, username, days=7)
"""

__version__ = "0.2.3"

# Core imports
from .config import load_config, save_config, get_config_value, set_config_value
from .auth import CognitoAuthenticator, save_credentials, remove_credentials

# AWS operations imports
from .aws import (
    get_user_history,
    format_events,
    list_user_resources,
    format_resources,
    get_user_permissions,
    test_permissions,
    format_permissions
)

__all__ = [
    # Version
    '__version__',

    # Configuration
    'load_config',
    'save_config',
    'get_config_value',
    'set_config_value',

    # Authentication
    'CognitoAuthenticator',
    'save_credentials',
    'remove_credentials',

    # AWS Operations - CloudTrail
    'get_user_history',
    'format_events',

    # AWS Operations - Resources
    'list_user_resources',
    'format_resources',

    # AWS Operations - Permissions
    'get_user_permissions',
    'test_permissions',
    'format_permissions',
]
