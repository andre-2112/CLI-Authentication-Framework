# CCA 0.2 - SDK Integration Guide

## Overview

The CCA (Cloud CLI Access) SDK provides a modular, reusable framework for integrating Cognito-based AWS authentication and authorization into your Python applications. This guide shows developers how to use the CCA SDK to add secure authentication and AWS operations to their own tools.

**Document Version**: 1.0
**Date**: November 10, 2025
**CCA Version**: 0.2.0

---

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [SDK Architecture](#sdk-architecture)
4. [Core Modules](#core-modules)
5. [Usage Examples](#usage-examples)
6. [Best Practices](#best-practices)
7. [Error Handling](#error-handling)
8. [Advanced Use Cases](#advanced-use-cases)

---

## Installation

### Option 1: Install from Source (Development Mode)

```bash
git clone https://github.com/2112-lab/cca.git
cd cca/ccc-cli
pip install -e .
```

### Option 2: Install as Package

```bash
pip install cca-sdk
```

### Requirements

- Python 3.8 or higher
- boto3 >= 1.26.0

---

## Quick Start

### Basic Authentication Flow

```python
#!/usr/bin/env python3
"""
Quick start example: Authenticate and get AWS credentials
"""

from cca import (
    CognitoAuthenticator,
    load_config,
    save_config,
    save_credentials
)

# Load configuration
config = load_config()

# If not configured, set up Cognito settings
if not config.get('user_pool_id'):
    config = {
        'user_pool_id': 'us-east-1_XXXXXXXXX',
        'app_client_id': 'YYYYYYYYYYYYYYYYYYYYYY',
        'identity_pool_id': 'us-east-1:ZZZZZZZZ-ZZZZ-ZZZZ-ZZZZ-ZZZZZZZZZZZZ',
        'region': 'us-east-1',
        'profile': 'my-app'
    }
    save_config(config)

# Authenticate
auth = CognitoAuthenticator(config)
tokens = auth.authenticate('user@example.com', 'password123')

# Get AWS credentials
aws_creds = auth.get_aws_credentials(tokens['IdToken'])

# Save to ~/.aws/credentials
save_credentials(aws_creds, profile='my-app')

print(f"✓ Authentication successful!")
print(f"✓ Credentials saved to profile: {config['profile']}")
```

---

## SDK Architecture

The CCA SDK is organized into modular components:

```
cca/
├── __init__.py                 # Main SDK exports
├── config.py                   # Configuration management
├── auth/                       # Authentication module
│   ├── __init__.py
│   ├── cognito.py              # CognitoAuthenticator class
│   └── credentials.py          # AWS credentials management
└── aws/                        # AWS operations module
    ├── __init__.py
    ├── cloudtrail.py           # CloudTrail/CloudWatch Logs operations
    ├── resources.py            # Resource listing operations
    └── permissions.py          # Permission inspection operations
```

### Design Principles

1. **Separation of Concerns**: Authentication, configuration, and AWS operations are separate modules
2. **Reusability**: Each module can be used independently
3. **No CLI Dependencies**: Core SDK has no CLI-specific code
4. **Standard boto3 Integration**: Works seamlessly with existing boto3 code

---

## Core Modules

### 1. Configuration Module (`cca.config`)

Handles loading and saving CCA configuration from `~/.ccc/config.json`.

```python
from cca.config import load_config, save_config, get_config_value, set_config_value

# Load entire configuration
config = load_config()

# Get a single value
user_pool_id = get_config_value('user_pool_id')

# Set a single value
set_config_value('profile', 'my-custom-profile')

# Save entire configuration
save_config({
    'user_pool_id': 'us-east-1_XXXXXXXXX',
    'app_client_id': 'YYYYYY',
    'identity_pool_id': 'us-east-1:ZZZZZZ',
    'region': 'us-east-1'
})
```

### 2. Authentication Module (`cca.auth`)

#### CognitoAuthenticator Class

The main authentication class that handles Cognito authentication flows.

```python
from cca.auth import CognitoAuthenticator

# Initialize with configuration
config = {
    'user_pool_id': 'us-east-1_XXXXXXXXX',
    'app_client_id': 'YYYYYYYYYYYYYYYYYYYYYY',
    'identity_pool_id': 'us-east-1:ZZZZZZZZ-ZZZZ-ZZZZ-ZZZZ-ZZZZZZZZZZZZ',
    'region': 'us-east-1',
    'profile': 'cca'
}
auth = CognitoAuthenticator(config)

# Authenticate with username/password
tokens = auth.authenticate('user@example.com', 'password')
# Returns: {'IdToken': '...', 'AccessToken': '...', 'RefreshToken': '...'}

# Exchange ID token for AWS credentials
aws_creds = auth.get_aws_credentials(tokens['IdToken'])
# Returns: {
#     'AccessKeyId': '...',
#     'SecretAccessKey': '...',
#     'SessionToken': '...',
#     'Expiration': '2025-11-10T15:30:00.000000+00:00'
# }

# Refresh credentials using refresh token
new_tokens = auth.refresh_credentials(tokens['RefreshToken'])
```

#### Credentials Management

```python
from cca.auth import save_credentials, remove_credentials

# Save AWS credentials to ~/.aws/credentials
save_credentials(aws_creds, profile='my-profile')

# Remove credentials profile
remove_credentials(profile='my-profile')
```

### 3. AWS Operations Module (`cca.aws`)

#### CloudTrail Operations

```python
import boto3
from cca.aws import get_user_history, format_events

# Create boto3 session with your profile
session = boto3.Session(profile_name='my-profile', region_name='us-east-1')

# Get user activity history
events, source = get_user_history(
    session,
    username='user123',
    days=7,
    limit=50
)

# Format events for display
formatted = format_events(events, limit=50, verbose=True)
print(formatted)
```

#### Resource Listing

```python
import boto3
from cca.aws import list_user_resources, format_resources

session = boto3.Session(profile_name='my-profile', region_name='us-east-1')

# List all resources
result = list_user_resources(
    session,
    username='user@example.com',
    filter_by_owner=True,
    limit=10,
    show_all=False,
    verbose=True
)

# Format and display
output = format_resources(result)
print(output)
```

#### Permission Inspection

```python
import boto3
from cca.aws import get_user_permissions, test_permissions, format_permissions

session = boto3.Session(profile_name='my-profile', region_name='us-east-1')

# Get user permissions
result = get_user_permissions(session, verbose=True)

# Test common permissions
test_results = test_permissions(session)

# Format and display
output = format_permissions(result, test_results)
print(output)
```

---

## Usage Examples

### Example 1: Custom CLI Tool

Create a custom CLI tool that uses CCA for authentication:

```python
#!/usr/bin/env python3
"""
my-aws-tool.py - Custom AWS CLI tool using CCA SDK
"""

import argparse
import boto3
from cca import CognitoAuthenticator, load_config, save_credentials

def authenticate():
    """Authenticate and save credentials"""
    config = load_config()

    if not config.get('user_pool_id'):
        print("Error: Not configured. Run 'ccc configure' first.")
        return False

    # Get credentials
    email = input("Email: ")
    password = input("Password: ")

    auth = CognitoAuthenticator(config)
    tokens = auth.authenticate(email, password)
    aws_creds = auth.get_aws_credentials(tokens['IdToken'])

    # Save credentials
    save_credentials(aws_creds, profile=config.get('profile', 'default'))

    print("✓ Authentication successful!")
    return True

def list_s3_buckets():
    """List S3 buckets using authenticated profile"""
    config = load_config()
    profile = config.get('profile', 'default')

    session = boto3.Session(profile_name=profile)
    s3 = session.client('s3')

    response = s3.list_buckets()

    print("\nS3 Buckets:")
    for bucket in response['Buckets']:
        print(f"  - {bucket['Name']}")

def main():
    parser = argparse.ArgumentParser(description='My AWS Tool')
    subparsers = parser.add_subparsers(dest='command')

    subparsers.add_parser('login', help='Authenticate with Cognito')
    subparsers.add_parser('list-buckets', help='List S3 buckets')

    args = parser.parse_args()

    if args.command == 'login':
        authenticate()
    elif args.command == 'list-buckets':
        list_s3_buckets()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
```

### Example 2: Web Application Integration

Integrate CCA authentication into a Flask web application:

```python
from flask import Flask, request, jsonify, session
from cca import CognitoAuthenticator, load_config

app = Flask(__name__)
app.secret_key = 'your-secret-key'

# Load CCA configuration
cca_config = load_config()

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login endpoint"""
    data = request.json
    email = data.get('email')
    password = data.get('password')

    try:
        # Authenticate with Cognito
        auth = CognitoAuthenticator(cca_config)
        tokens = auth.authenticate(email, password)

        # Get AWS credentials
        aws_creds = auth.get_aws_credentials(tokens['IdToken'])

        # Store in session
        session['tokens'] = tokens
        session['aws_credentials'] = aws_creds
        session['email'] = email

        return jsonify({
            'success': True,
            'message': 'Authentication successful'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 401

@app.route('/api/auth/refresh', methods=['POST'])
def refresh():
    """Refresh credentials endpoint"""
    refresh_token = session.get('tokens', {}).get('RefreshToken')

    if not refresh_token:
        return jsonify({'success': False, 'error': 'No refresh token'}), 401

    try:
        auth = CognitoAuthenticator(cca_config)
        new_tokens = auth.refresh_credentials(refresh_token)
        aws_creds = auth.get_aws_credentials(new_tokens['IdToken'])

        session['tokens'] = new_tokens
        session['aws_credentials'] = aws_creds

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 401

if __name__ == '__main__':
    app.run(debug=True)
```

### Example 3: Automated Script

Create a script that authenticates and performs AWS operations:

```python
#!/usr/bin/env python3
"""
backup-script.py - Automated S3 backup using CCA authentication
"""

import boto3
from datetime import datetime
from cca import CognitoAuthenticator, load_config, save_credentials

def main():
    # Load CCA configuration
    config = load_config()

    if not config.get('tokens'):
        print("Error: Not authenticated. Run 'ccc login' first.")
        return

    # Check if credentials need refresh
    auth = CognitoAuthenticator(config)

    try:
        # Try to refresh credentials
        tokens = auth.refresh_credentials(config['tokens']['refresh_token'])
        aws_creds = auth.get_aws_credentials(tokens['IdToken'])
        save_credentials(aws_creds, profile=config.get('profile', 'cca'))
    except Exception as e:
        print(f"Error refreshing credentials: {e}")
        print("Please run 'ccc login' to re-authenticate.")
        return

    # Perform backup using authenticated session
    session = boto3.Session(profile_name=config.get('profile', 'cca'))
    s3 = session.client('s3')

    # Upload backup file
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    backup_file = f'backup-{timestamp}.tar.gz'

    print(f"Uploading {backup_file} to S3...")
    s3.upload_file(
        backup_file,
        'my-backup-bucket',
        f'backups/{backup_file}'
    )

    print("✓ Backup complete!")

if __name__ == '__main__':
    main()
```

### Example 4: AWS Resource Monitoring Tool

Build a monitoring tool that uses CCA AWS operations:

```python
#!/usr/bin/env python3
"""
aws-monitor.py - Monitor AWS resources using CCA SDK
"""

import boto3
from cca import load_config
from cca.aws import list_user_resources, get_user_history

def monitor_resources():
    """Monitor and report on AWS resources"""
    config = load_config()
    session = boto3.Session(
        profile_name=config.get('profile', 'cca'),
        region_name=config.get('region', 'us-east-1')
    )

    # Get user identity
    sts = session.client('sts')
    identity = sts.get_caller_identity()
    username = config.get('tokens', {}).get('username', 'Unknown')

    print(f"=== AWS Resource Monitor ===")
    print(f"User: {username}")
    print(f"Account: {identity['Account']}\n")

    # List resources
    result = list_user_resources(
        session,
        username=username,
        filter_by_owner=False,
        show_all=True
    )

    print(f"Total Resources: {result['total_resources']}")
    print(f"Resource Types: {len(result['resources_by_type'])}\n")

    # Show recent activity
    events, source = get_user_history(
        session,
        username=identity['Arn'].split('/')[-1],
        days=1,
        limit=10
    )

    print(f"Recent Activity (last 24 hours):")
    print(f"  - Total events: {len(events)}")
    print(f"  - Data source: {source}")

if __name__ == '__main__':
    monitor_resources()
```

---

## Best Practices

### 1. Configuration Management

**DO**:
- Use `load_config()` to read configuration at startup
- Store sensitive configuration (pool IDs, etc.) in the CCA config file
- Use environment variables for truly sensitive data (passwords)

**DON'T**:
- Hard-code Cognito pool IDs or credentials in your code
- Store passwords in configuration files

### 2. Error Handling

Always wrap authentication calls in try-except blocks:

```python
from botocore.exceptions import ClientError

try:
    auth = CognitoAuthenticator(config)
    tokens = auth.authenticate(username, password)
except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == 'NotAuthorizedException':
        print("Invalid username or password")
    elif error_code == 'UserNotFoundException':
        print("User not found")
    else:
        print(f"Authentication error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### 3. Token Management

- Store refresh tokens securely
- Refresh credentials before they expire
- Clear tokens on logout

```python
from datetime import datetime, timezone
from dateutil import parser

def should_refresh_credentials(config):
    """Check if credentials should be refreshed"""
    retrieved_at = config.get('tokens', {}).get('retrieved_at')

    if not retrieved_at:
        return True

    # Parse timestamp
    retrieved_time = parser.isoparse(retrieved_at)
    now = datetime.now(timezone.utc)

    # Refresh if older than 55 minutes (tokens expire at 60 minutes)
    age_minutes = (now - retrieved_time).total_seconds() / 60

    return age_minutes > 55
```

### 4. Session Management

Create boto3 sessions explicitly:

```python
# GOOD: Explicit session with profile
session = boto3.Session(
    profile_name=config.get('profile', 'cca'),
    region_name=config.get('region', 'us-east-1')
)
s3 = session.client('s3')

# AVOID: Implicit default session
s3 = boto3.client('s3')  # May not use correct profile
```

### 5. Resource Cleanup

Always clean up resources:

```python
def cleanup_session():
    """Remove credentials on application exit"""
    from cca.auth import remove_credentials
    config = load_config()
    remove_credentials(profile=config.get('profile', 'cca'))
```

---

## Error Handling

### Common Errors and Solutions

#### 1. NotAuthorizedException

```python
try:
    tokens = auth.authenticate(username, password)
except Exception as e:
    if 'NotAuthorizedException' in str(e):
        print("Invalid credentials. Please check username and password.")
```

#### 2. ExpiredToken

```python
try:
    session = boto3.Session(profile_name='cca')
    sts = session.client('sts')
    identity = sts.get_caller_identity()
except ClientError as e:
    if e.response['Error']['Code'] == 'ExpiredToken':
        print("Token expired. Refreshing...")
        # Refresh credentials
        auth = CognitoAuthenticator(config)
        new_tokens = auth.refresh_credentials(refresh_token)
```

#### 3. AccessDeniedException

```python
from cca.aws import get_user_permissions

result = get_user_permissions(session)

if 'error' in result:
    if result['error'] == 'AccessDeniedException':
        print("Access denied. Check IAM permissions.")
        print("Required: sts:GetCallerIdentity, iam:GetRole")
```

### Error Handling Pattern

```python
def safe_authenticate(username, password):
    """Safely authenticate with comprehensive error handling"""
    try:
        config = load_config()

        if not config.get('user_pool_id'):
            return {'success': False, 'error': 'Not configured'}

        auth = CognitoAuthenticator(config)
        tokens = auth.authenticate(username, password)
        aws_creds = auth.get_aws_credentials(tokens['IdToken'])

        return {
            'success': True,
            'tokens': tokens,
            'credentials': aws_creds
        }

    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_messages = {
            'NotAuthorizedException': 'Invalid credentials',
            'UserNotFoundException': 'User not found',
            'UserNotConfirmedException': 'Email not verified'
        }
        return {
            'success': False,
            'error': error_messages.get(error_code, f'AWS error: {error_code}')
        }

    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }
```

---

## Advanced Use Cases

### 1. Multi-Region Support

```python
def create_regional_sessions(profile='cca'):
    """Create boto3 sessions for multiple regions"""
    regions = ['us-east-1', 'us-west-2', 'eu-west-1']

    sessions = {}
    for region in regions:
        sessions[region] = boto3.Session(
            profile_name=profile,
            region_name=region
        )

    return sessions

# Usage
sessions = create_regional_sessions()
for region, session in sessions.items():
    ec2 = session.client('ec2')
    instances = ec2.describe_instances()
    print(f"{region}: {len(instances['Reservations'])} instances")
```

### 2. Credential Caching

```python
import pickle
from pathlib import Path

class CredentialCache:
    """Cache AWS credentials to reduce Cognito API calls"""

    def __init__(self, cache_dir=None):
        self.cache_dir = cache_dir or Path.home() / '.ccc' / 'cache'
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, username):
        """Get cached credentials if valid"""
        cache_file = self.cache_dir / f"{username}.pkl"

        if not cache_file.exists():
            return None

        with open(cache_file, 'rb') as f:
            cached = pickle.load(f)

        # Check expiration
        expiration = parser.isoparse(cached['Expiration'])
        if datetime.now(timezone.utc) >= expiration:
            return None  # Expired

        return cached

    def set(self, username, credentials):
        """Cache credentials"""
        cache_file = self.cache_dir / f"{username}.pkl"

        with open(cache_file, 'wb') as f:
            pickle.dump(credentials, f)
```

### 3. Automatic Credential Refresh

```python
import boto3
from botocore.exceptions import ClientError

class AutoRefreshSession:
    """boto3 Session wrapper with automatic credential refresh"""

    def __init__(self, config, auth):
        self.config = config
        self.auth = auth
        self.session = None
        self._refresh_session()

    def _refresh_session(self):
        """Refresh AWS credentials"""
        try:
            tokens = self.auth.refresh_credentials(
                self.config['tokens']['refresh_token']
            )
            aws_creds = self.auth.get_aws_credentials(tokens['IdToken'])
            save_credentials(aws_creds, profile=self.config.get('profile', 'cca'))

            self.session = boto3.Session(
                profile_name=self.config.get('profile', 'cca'),
                region_name=self.config.get('region', 'us-east-1')
            )
        except Exception as e:
            raise Exception(f"Failed to refresh credentials: {e}")

    def client(self, service_name):
        """Create a client with automatic retry on ExpiredToken"""
        client = self.session.client(service_name)

        # Wrap client to auto-refresh on expired token
        original_make_request = client._make_request

        def make_request_with_retry(*args, **kwargs):
            try:
                return original_make_request(*args, **kwargs)
            except ClientError as e:
                if e.response['Error']['Code'] == 'ExpiredToken':
                    self._refresh_session()
                    client = self.session.client(service_name)
                    return client._make_request(*args, **kwargs)
                raise

        client._make_request = make_request_with_retry
        return client

# Usage
config = load_config()
auth = CognitoAuthenticator(config)
session = AutoRefreshSession(config, auth)

# This will automatically refresh if token expires
s3 = session.client('s3')
buckets = s3.list_buckets()
```

### 4. Parallel AWS Operations

```python
import concurrent.futures
from cca.aws import list_user_resources

def scan_region(region, profile):
    """Scan resources in a specific region"""
    session = boto3.Session(profile_name=profile, region_name=region)
    result = list_user_resources(session, show_all=True)
    return region, result['total_resources']

def scan_all_regions(profile='cca'):
    """Scan all regions in parallel"""
    regions = [
        'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
        'eu-west-1', 'eu-west-2', 'eu-central-1',
        'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1'
    ]

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(scan_region, region, profile)
            for region in regions
        ]

        results = {}
        for future in concurrent.futures.as_completed(futures):
            region, count = future.result()
            results[region] = count

    return results

# Usage
results = scan_all_regions()
for region, count in sorted(results.items(), key=lambda x: x[1], reverse=True):
    print(f"{region}: {count} resources")
```

---

## Conclusion

The CCA SDK provides a robust, modular foundation for integrating Cognito-based AWS authentication into your Python applications. By following this guide and the best practices outlined, you can:

- Add secure authentication to CLI tools and web applications
- Leverage AWS operations for monitoring and automation
- Build scalable, maintainable solutions with clean separation of concerns

For additional support and examples, refer to:
- CCA GitHub Repository: https://github.com/2112-lab/cca
- CCA Documentation: https://github.com/2112-lab/cca/docs
- Issue Tracker: https://github.com/2112-lab/cca/issues

---

**Document Version History**:
- v1.0 (2025-11-10): Initial release with SDK 0.2.0
