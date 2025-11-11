# CLI Authentication Framework v0.3.0

Modular SDK and CLI tool for secure AWS authentication using Amazon Cognito User Pools and Identity Pools.

## Features

### CLI Features
- 🔐 Password-based authentication via Amazon Cognito
- 📝 CLI-based user registration (optional names)
- 🔑 Password management (forgot password, change password)
- 🎫 Automatic AWS credential management
- 🔄 Token refresh support
- 💾 Credentials cached in `~/.aws/credentials`
- ⏱️ 60-minute session duration (refreshable)
- 📊 Activity history tracking (CloudTrail + CloudWatch Logs)
- 🔍 AWS resource visibility
- 🔐 Permission inspection
- 🚫 Console access blocked (CLI-only)

### SDK Features
- 📦 Modular architecture (auth, config, aws operations)
- 🔌 Easy integration into Python applications
- 🎯 Clean separation of concerns
- 🔧 Reusable authentication components
- 📚 Comprehensive API documentation

## Installation

### Option 1: From Source (Development)

```bash
git clone https://github.com/andre-2112/CLI-Authentication-Framework.git
cd CLI-Authentication-Framework
pip3 install -e ccc-cli/
```

This installs both the `cca` SDK package and the `ccc` CLI command.

### Option 2: Direct Installation

```bash
pip3 install cca-sdk
```

This installs the package from PyPI (when published).

### Requirements

- Python 3.8 or higher
- boto3 >= 1.26.0

See [INSTALL.md](INSTALL.md) for detailed installation instructions.

## Quick Start

### 1. Configure

```bash
ccc configure
```

You'll be prompted for:
- **Cognito User Pool ID**: `us-east-1_XXXXXXXXX`
- **Cognito App Client ID**: `xxxxxxxxxxxxxxxxxxxxxxxxxxxx`
- **Cognito Identity Pool ID**: `us-east-1:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
- **AWS Region**: `us-east-1`
- **AWS Profile Name**: `default` (default)

### 2. Login

```bash
ccc login
```

Enter your email and password when prompted.

### 3. Use AWS CLI

```bash
# Option 1: Use profile flag
aws --profile default s3 ls

# Option 2: Set environment variable
export AWS_PROFILE=default
aws s3 ls
```

## CLI Commands

### Authentication Commands

#### `ccc configure`
Configure CCC CLI with your Cognito settings (User Pool ID, App Client ID, Identity Pool ID, region, Lambda URL).

#### `ccc register`
Register a new user account via CLI. Prompts for email (required), first name (optional), last name (optional), and password. Admin approval required before account activation.

```bash
ccc register
# Email: user@example.com
# First Name (optional): John
# Last Name (optional): Doe
# Password: [hidden]
# Confirm Password: [hidden]
```

#### `ccc login`
Authenticate with Cognito and obtain AWS credentials (60-minute session).

#### `ccc refresh`
Refresh AWS credentials using your refresh token (valid for 30 days).

#### `ccc logout`
Clear stored credentials and tokens.

### Password Management Commands

#### `ccc forgot-password`
Reset your password via email verification. Cognito sends a verification code to your email, which you use to set a new password.

```bash
ccc forgot-password
# Email: user@example.com
# [Verification code sent to email]
# Verification Code: XXXXXX
# New Password: [hidden]
# Confirm New Password: [hidden]
```

#### `ccc change-password`
Change your password using your current password. Requires an active login session.

```bash
ccc change-password
# Current Password: [hidden]
# New Password: [hidden]
# Confirm New Password: [hidden]
```

### Information Commands

#### `ccc whoami`
Display current user and AWS identity information.

```bash
ccc whoami
# Output: Email, region, profile, AWS account, ARN
```

#### `ccc version`
Display version information.

### AWS Operations Commands

#### `ccc history`
Display history of AWS operations performed by the user.

```bash
ccc history                    # Last 7 days
ccc history --days 30          # Last 30 days
ccc history --limit 100        # Show up to 100 events
ccc history --verbose          # Show detailed information
```

Uses hybrid CloudTrail + CloudWatch Logs approach for comprehensive audit trail.

#### `ccc resources`
Display all AWS resources in the account (requires `tag:GetResources` permission).

```bash
ccc resources                  # List all resources
ccc resources --owner          # Filter by Owner tag
ccc resources --all            # Show all without limit
ccc resources --verbose        # Show resource tags
```

#### `ccc permissions`
Display user's AWS permissions and test common actions.

```bash
ccc permissions                # Show role and policies
ccc permissions --verbose      # Show full policy documents
ccc permissions --test         # Test common permissions
```

## Configuration

Configuration is stored in `~/.ccc/config.json`:

```json
{
  "user_pool_id": "us-east-1_XXXXXXXXX",
  "app_client_id": "xxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "identity_pool_id": "us-east-1:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "region": "us-east-1",
  "profile": "default",
  "lambda_url": "https://xxxxx.lambda-url.us-east-1.on.aws/"
}
```

**Note**: The `lambda_url` is required for the `ccc register` command. Contact your administrator for this URL.

## Credentials

AWS credentials are stored in `~/.aws/credentials`:

```ini
[default]
aws_access_key_id = ASIA...
aws_secret_access_key = ...
aws_session_token = ...
# expires_at = 2025-11-10T07:30:00+00:00
```

Credentials are valid for **60 minutes** (1 hour) and can be refreshed using `ccc refresh`.

## Architecture

### Authentication Flow

```
┌──────────────┐
│   User       │
│  (ccc login) │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│  Cognito         │
│  User Pool       │
│  (authenticate)  │
└──────┬───────────┘
       │ ID Token
       ▼
┌──────────────────┐
│  Cognito         │
│  Identity Pool   │
│  (federate)      │
└──────┬───────────┘
       │ AWS Credentials
       ▼
┌──────────────────┐
│  ~/.aws/         │
│  credentials     │
└──────────────────┘
```

### SDK Architecture

The CCA SDK is organized into modular components:

```
cca/                           # Main SDK package
├── __init__.py                # SDK exports
├── config.py                  # Configuration management
├── auth/                      # Authentication module
│   ├── __init__.py
│   ├── cognito.py             # CognitoAuthenticator class
│   └── credentials.py         # AWS credentials management
└── aws/                       # AWS operations module
    ├── __init__.py
    ├── cloudtrail.py          # CloudTrail/CloudWatch Logs ops
    ├── resources.py           # Resource listing operations
    └── permissions.py         # Permission inspection
```

The CLI (`ccc.py`) is a thin wrapper around the SDK (390 lines, down from 991 lines).

## SDK Usage

The CCA SDK can be integrated into your own Python applications:

### Basic Authentication

```python
from cca import CognitoAuthenticator, load_config, save_credentials

# Load configuration
config = load_config()

# Authenticate
auth = CognitoAuthenticator(config)
tokens = auth.authenticate('user@example.com', 'password')

# Get AWS credentials
aws_creds = auth.get_aws_credentials(tokens['IdToken'])

# Save to AWS credentials file
save_credentials(aws_creds, profile='my-app')
```

### Using AWS Operations

```python
import boto3
from cca.aws import get_user_history, list_user_resources

# Create boto3 session
session = boto3.Session(profile_name='my-app', region_name='us-east-1')

# Get user activity history
events, source = get_user_history(session, 'username', days=7)

# List AWS resources
result = list_user_resources(session, show_all=True)
```

### Custom CLI Tool

```python
#!/usr/bin/env python3
from cca import CognitoAuthenticator, load_config

def my_custom_tool():
    config = load_config()
    auth = CognitoAuthenticator(config)
    tokens = auth.authenticate(email, password)
    # Use tokens for your operations
```

For complete SDK documentation and examples, see:
- [CCA 0.2 - SDK Integration Guide.md](docs/CCA%200.2%20-%20SDK%20Integration%20Guide.md)

## Troubleshooting

### "Not configured" error

Run `ccc configure` first to set up your Cognito settings.

### "Invalid username or password"

Check your email and password. Contact your administrator if your account hasn't been approved yet.

### "Credentials expired"

Run `ccc refresh` to refresh your credentials, or `ccc login` to re-authenticate.

### "No credentials found"

Make sure you've run `ccc login` successfully.

## Security

- Passwords are never stored locally
- Refresh tokens are stored securely in `~/.ccc/config.json`
- AWS credentials are temporary (60 minutes, refreshable)
- Credentials file has restrictive permissions (600 on Unix)
- Console access is explicitly denied in IAM policy
- Modular SDK design prevents credential leakage

## Requirements

- Python 3.8 or higher
- boto3 >= 1.26.0
- AWS CLI (optional, for using credentials)

## Version

**CLI Authentication Framework v0.3.0**

### Recent Changes (v0.3.0)

**New Features (2025-11-10)**:
- ✅ Optional names in registration (first_name and last_name now optional)
- ✅ CLI registration command (`ccc register`)
- ✅ CLI forgot password command (`ccc forgot-password`)
- ✅ CLI change password command (`ccc change-password`)
- ✅ Password validation across all password inputs
- ✅ Email username fallback for display names
- ✅ Requests library dependency added

### Previous Changes (v0.2.0)

**SDK Refactoring (2025-11-10)**:
- ✅ Modular SDK architecture (7 independent modules)
- ✅ 60% code reduction in CLI wrapper (991 → 390 lines)
- ✅ Reusable authentication components
- ✅ Easy integration into Python applications
- ✅ Clean separation of concerns

**CLI Enhancements (2025-11-10)**:
- ✅ New `ccc history` command (CloudTrail + CloudWatch Logs)
- ✅ New `ccc resources` command (Resource Groups Tagging API)
- ✅ New `ccc permissions` command (IAM role inspection)
- ✅ Enhanced error handling with actionable messages
- ✅ Windows compatibility improvements

**Authentication Improvements (2025-11-09)**:
- ✅ Username field removed (email-only identification)
- ✅ Password set during registration
- ✅ Immediate login after approval
- ✅ Cognito User Pools + Identity Pools
- ✅ 60-minute sessions (refreshable for 30 days)

### Changes from v0.1 (IAM Identity Center):
- ✅ Simpler user experience (password-based vs OAuth device flow)
- ✅ Modular SDK for code reusability
- ✅ AWS operations visibility (history, resources, permissions)
- ✅ Hybrid CloudTrail approach for audit trail

## Documentation

Comprehensive documentation is available in the `/docs` directory:

### User Guides
- **[INSTALL.md](INSTALL.md)** - Detailed installation instructions
- **[CCA 0.2 - SDK Integration Guide.md](docs/CCA%200.2%20-%20SDK%20Integration%20Guide.md)** - Complete SDK documentation with examples
- **[CCA 0.2 - Hybrid CloudTrail Implementation.md](docs/CCA%200.2%20-%20Hybrid%20CloudTrail%20Implementation.md)** - CloudTrail setup and usage

### Technical Documentation
- **[CCA 0.2 - Implementation Changes Log - Updated.md](docs/CCA%200.2%20-%20Implementation%20Changes%20Log%20-%20Updated.md)** - Version history and changes
- **[CCA 0.2 - Report - End-to-End Testing.md](docs/CCA%200.2%20-%20Report%20-%20End-to-End%20Testing.md)** - Testing results (22/22 tests passed)
- **[Addendum - AWS Resources Inventory - 0.2 - Updated.md](docs/Addendum%20-%20AWS%20Resources%20Inventory%20-%20Updated.md)** - Infrastructure details

## License

MIT License

## Support

For issues or questions:
- GitHub Issues: https://github.com/andre-2112/CLI-Authentication-Framework/issues
- Documentation: See `/docs` directory
- Contact: info@2112-lab.com
