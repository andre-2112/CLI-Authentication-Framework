"""
CCA AWS Operations Module
Provides AWS operations for CloudTrail, resources, and permissions.
"""

from .cloudtrail import get_user_history, format_events
from .resources import list_user_resources, format_resources
from .permissions import get_user_permissions, test_permissions, format_permissions

__all__ = [
    'get_user_history',
    'format_events',
    'list_user_resources',
    'format_resources',
    'get_user_permissions',
    'test_permissions',
    'format_permissions'
]
