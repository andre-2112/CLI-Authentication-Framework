#!/usr/bin/env python3
"""
CCC CLI - Cloud CLI Access Tool (v0.2 - Cognito)
Provides secure CLI authentication to AWS using Amazon Cognito.

This is a thin wrapper around the CCA SDK.
"""

import sys
import argparse
import boto3
import getpass
from datetime import datetime, timezone

# Import CCA SDK
from cca import (
    __version__ as VERSION,
    CognitoAuthenticator,
    load_config,
    save_config,
    save_credentials,
    remove_credentials,
    get_user_history,
    format_events,
    list_user_resources,
    format_resources,
    get_user_permissions,
    test_permissions,
    format_permissions
)


def validate_password(password):
    """
    Validate password meets Cognito requirements
    Returns: (bool, str) - (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not any(c.islower() for c in password):
        return False, "Password must contain lowercase letters"
    if not any(c.isupper() for c in password):
        return False, "Password must contain uppercase letters"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain numbers"
    if not any(not c.isalnum() for c in password):
        return False, "Password must contain special characters"
    return True, ""


def cmd_configure(args):
    """Configure CCC CLI with Cognito settings"""
    print("=== CCC CLI Configuration (v0.2 - Cognito) ===\n")

    config = load_config()

    # Prompt for configuration values
    user_pool_id = input(f"Cognito User Pool ID [{config.get('user_pool_id', '')}]: ").strip()
    app_client_id = input(f"Cognito App Client ID [{config.get('app_client_id', '')}]: ").strip()
    identity_pool_id = input(f"Cognito Identity Pool ID [{config.get('identity_pool_id', '')}]: ").strip()
    region = input(f"AWS Region [{config.get('region', 'us-east-1')}]: ").strip()
    profile = input(f"AWS Profile Name [{config.get('profile', 'cca')}]: ").strip()

    # Update config with new values (keep old if not provided)
    if user_pool_id:
        config['user_pool_id'] = user_pool_id
    if app_client_id:
        config['app_client_id'] = app_client_id
    if identity_pool_id:
        config['identity_pool_id'] = identity_pool_id
    if region:
        config['region'] = region
    else:
        config.setdefault('region', 'us-east-1')
    if profile:
        config['profile'] = profile
    else:
        config.setdefault('profile', 'cca')

    # Validate required fields
    if not config.get('user_pool_id'):
        print("[ERROR] User Pool ID is required")
        sys.exit(1)
    if not config.get('app_client_id'):
        print("[ERROR] App Client ID is required")
        sys.exit(1)
    if not config.get('identity_pool_id'):
        print("[ERROR] Identity Pool ID is required")
        sys.exit(1)

    save_config(config)
    print("\n[OK] Configuration complete!")
    print(f"\nYou can now run: ccc login")


def cmd_login(args):
    """Login to AWS using Cognito credentials"""
    print("=== CCC CLI Login (v0.2 - Cognito) ===\n")

    config = load_config()

    if not config.get('user_pool_id') or not config.get('app_client_id'):
        print("[ERROR] Not configured. Run 'ccc configure' first.")
        sys.exit(1)

    # Prompt for credentials
    username = input("Email: ").strip()
    password = getpass.getpass("Password: ")

    if not username or not password:
        print("[ERROR] Username and password are required")
        sys.exit(1)

    try:
        # Initialize authenticator
        auth = CognitoAuthenticator(config)

        # Authenticate with Cognito
        tokens = auth.authenticate(username, password)

        # Save tokens for future refresh
        config['tokens'] = {
            'id_token': tokens['IdToken'],
            'access_token': tokens['AccessToken'],
            'refresh_token': tokens.get('RefreshToken'),
            'username': username,
            'retrieved_at': datetime.now(timezone.utc).isoformat()
        }
        save_config(config)

        # Get AWS credentials
        aws_credentials = auth.get_aws_credentials(tokens['IdToken'])

        # Save AWS credentials to ~/.aws/credentials
        save_credentials(aws_credentials, profile=config.get('profile', 'cca'))

        print(f"\n[OK] Login successful!")
        print(f"\nYou can now use AWS CLI with: aws --profile {config.get('profile', 'cca')} <command>")
        print(f"Or set: export AWS_PROFILE={config.get('profile', 'cca')}")

    except Exception as e:
        print(f"\n[ERROR] Login failed: {e}")
        sys.exit(1)


def cmd_refresh(args):
    """Refresh AWS credentials using stored refresh token"""
    print("=== CCC CLI Refresh ===\n")

    config = load_config()

    if not config.get('tokens', {}).get('refresh_token'):
        print("[ERROR] No refresh token found. Please run 'ccc login' first.")
        sys.exit(1)

    try:
        auth = CognitoAuthenticator(config)

        # Refresh tokens
        tokens = auth.refresh_credentials(config['tokens']['refresh_token'])

        # Update stored tokens
        config['tokens']['id_token'] = tokens['IdToken']
        config['tokens']['access_token'] = tokens['AccessToken']
        # Note: Refresh token might not be returned (reuse existing one)
        if 'RefreshToken' in tokens:
            config['tokens']['refresh_token'] = tokens['RefreshToken']
        config['tokens']['retrieved_at'] = datetime.now(timezone.utc).isoformat()
        save_config(config)

        # Get new AWS credentials
        aws_credentials = auth.get_aws_credentials(tokens['IdToken'])

        # Save AWS credentials
        save_credentials(aws_credentials, profile=config.get('profile', 'cca'))

        print(f"[OK] Credentials refreshed successfully!")

    except Exception as e:
        print(f"[ERROR] Refresh failed: {e}")
        print("[INFO] Try running 'ccc login' again")
        sys.exit(1)


def cmd_logout(args):
    """Logout and clear stored credentials"""
    print("=== CCC CLI Logout ===\n")

    config = load_config()

    # Clear tokens from config
    if 'tokens' in config:
        del config['tokens']
        save_config(config)

    # Remove profile from ~/.aws/credentials
    profile = config.get('profile', 'cca')
    remove_credentials(profile)

    print("[OK] Logout complete!")


def cmd_register(args):
    """Register a new user via CLI"""
    print("=== CCC CLI Registration ===\n")

    config = load_config()

    # Check if Lambda URL is configured
    lambda_url = config.get('lambda_url')
    if not lambda_url:
        print("[ERROR] Lambda URL not configured")
        print("[INFO] Add 'lambda_url' to your config or set it via environment variable")
        print("[INFO] Example: https://xxxxx.lambda-url.us-east-1.on.aws/")
        sys.exit(1)

    # Interactive prompts
    email = input("Email: ").strip()
    if not email:
        print("[ERROR] Email is required")
        sys.exit(1)

    first_name = input("First Name (optional, press Enter to skip): ").strip() or None
    last_name = input("Last Name (optional, press Enter to skip): ").strip() or None

    # Password with confirmation
    password = getpass.getpass("Password: ")
    if not password:
        print("[ERROR] Password is required")
        sys.exit(1)

    # Validate password
    is_valid, error_msg = validate_password(password)
    if not is_valid:
        print(f"[ERROR] {error_msg}")
        print("[INFO] Password must be 8+ characters with uppercase, lowercase, number, and symbol")
        sys.exit(1)

    password_confirm = getpass.getpass("Confirm Password: ")
    if password != password_confirm:
        print("[ERROR] Passwords do not match")
        sys.exit(1)

    try:
        # Initialize authenticator (just for registration method)
        auth = CognitoAuthenticator(config)

        # Register user
        result = auth.register(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            lambda_url=lambda_url
        )

        print("\n[OK] Registration submitted successfully!")
        print("\n[INFO] Your request will be reviewed by an administrator")
        print("[INFO] Once approved, you can login with: ccc login")

    except Exception as e:
        print(f"\n[ERROR] Registration failed: {e}")
        sys.exit(1)


def cmd_forgot_password(args):
    """Initiate forgot password flow"""
    print("=== CCC CLI Forgot Password ===\n")

    config = load_config()

    if not config.get('user_pool_id') or not config.get('app_client_id'):
        print("[ERROR] Not configured. Run 'ccc configure' first.")
        sys.exit(1)

    # Get email
    email = input("Email: ").strip()
    if not email:
        print("[ERROR] Email is required")
        sys.exit(1)

    try:
        # Initialize authenticator
        auth = CognitoAuthenticator(config)

        # Request verification code
        auth.forgot_password(email)

        # Now ask for code and new password
        print("\n[STEP 2] Enter the verification code sent to your email\n")

        code = input("Verification Code: ").strip()
        if not code:
            print("[ERROR] Verification code is required")
            sys.exit(1)

        new_password = getpass.getpass("New Password: ")
        if not new_password:
            print("[ERROR] New password is required")
            sys.exit(1)

        # Validate password
        is_valid, error_msg = validate_password(new_password)
        if not is_valid:
            print(f"[ERROR] {error_msg}")
            print("[INFO] Password must be 8+ characters with uppercase, lowercase, number, and symbol")
            sys.exit(1)

        new_password_confirm = getpass.getpass("Confirm New Password: ")
        if new_password != new_password_confirm:
            print("[ERROR] Passwords do not match")
            sys.exit(1)

        # Confirm forgot password with code
        auth.confirm_forgot_password(email, code, new_password)

        print("\n[OK] Password reset successful!")
        print("[INFO] You can now login with: ccc login")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)


def cmd_change_password(args):
    """Change password (requires current password)"""
    print("=== CCC CLI Change Password ===\n")

    config = load_config()

    if not config.get('tokens', {}).get('access_token'):
        print("[ERROR] Not logged in. Run 'ccc login' first.")
        sys.exit(1)

    access_token = config['tokens']['access_token']

    # Get current and new password
    current_password = getpass.getpass("Current Password: ")
    if not current_password:
        print("[ERROR] Current password is required")
        sys.exit(1)

    new_password = getpass.getpass("New Password: ")
    if not new_password:
        print("[ERROR] New password is required")
        sys.exit(1)

    # Validate password
    is_valid, error_msg = validate_password(new_password)
    if not is_valid:
        print(f"[ERROR] {error_msg}")
        print("[INFO] Password must be 8+ characters with uppercase, lowercase, number, and symbol")
        sys.exit(1)

    new_password_confirm = getpass.getpass("Confirm New Password: ")
    if new_password != new_password_confirm:
        print("[ERROR] Passwords do not match")
        sys.exit(1)

    try:
        # Initialize authenticator
        auth = CognitoAuthenticator(config)

        # Change password
        auth.change_password(access_token, current_password, new_password)

        print("\n[OK] Password changed successfully!")
        print("[INFO] You can continue using your current session")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)


def cmd_whoami(args):
    """Display current user information"""
    print("=== CCC CLI User Info ===\n")

    config = load_config()

    if not config.get('tokens'):
        print("[INFO] Not logged in")
        print("[INFO] Run 'ccc login' to authenticate")
        return

    print(f"Logged in as: {config['tokens'].get('username', 'Unknown')}")
    print(f"Region: {config.get('region', 'us-east-1')}")
    print(f"AWS Profile: {config.get('profile', 'cca')}")
    print(f"Last authenticated: {config['tokens'].get('retrieved_at', 'Unknown')}")

    # Try to get caller identity from AWS
    try:
        profile = config.get('profile', 'cca')
        session = boto3.Session(profile_name=profile)
        sts = session.client('sts')
        identity = sts.get_caller_identity()

        print(f"\nAWS Caller Identity:")
        print(f"  Account: {identity['Account']}")
        print(f"  UserId: {identity['UserId']}")
        print(f"  ARN: {identity['Arn']}")
    except Exception as e:
        print(f"\n[WARN] Could not retrieve AWS caller identity: {e}")
        print("[INFO] Your credentials may have expired. Run 'ccc refresh' or 'ccc login'")


def cmd_version(args):
    """Display version information"""
    print(f"CCC CLI v{VERSION} (Cognito)")
    print("Cloud CLI Access - Secure AWS authentication via Amazon Cognito")


def cmd_history(args):
    """Display history of AWS operations performed by the user (Hybrid: CloudTrail + CloudWatch Logs)"""
    print("=== CCC CLI History ===\n")

    config = load_config()
    profile = config.get('profile', 'cca')
    region = config.get('region', 'us-east-1')

    session = boto3.Session(profile_name=profile, region_name=region)
    sts = session.client('sts')
    identity = sts.get_caller_identity()
    user_arn = identity['Arn']
    username = user_arn.split('/')[-1]

    print(f"User: {user_arn}")
    print(f"Looking back: {args.days} days\n")

    # Get events using SDK
    events, source = get_user_history(session, username, days=args.days, limit=args.limit)

    # Display events
    if events:
        formatted = format_events(events, limit=args.limit, verbose=args.verbose)
        print(formatted)
        print(f"\nTotal events: {len(events)}")
        print(f"Source: {source}")
    else:
        print("[INFO] No events found in the specified time range")
        print("\nTroubleshooting:")
        print("  1. Make sure you have performed some AWS operations")
        print("  2. Try increasing --days parameter")
        print("  3. Check that CloudTrail is logging events")
        print("  4. Verify IAM permissions for cloudtrail:LookupEvents or logs:FilterLogEvents")


def cmd_resources(args):
    """Display all AWS resources created by the user"""
    print("=== CCC CLI Resources ===\n")

    config = load_config()
    profile = config.get('profile', 'cca')
    region = config.get('region', 'us-east-1')

    try:
        # Create session
        session = boto3.Session(profile_name=profile, region_name=region)

        # Get user identity for filtering
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        username = config.get('tokens', {}).get('username', 'Unknown')

        print(f"User: {username}")
        print(f"Account: {identity['Account']}")
        print(f"Region: {session.region_name}\n")

        # List resources using SDK
        result = list_user_resources(
            session,
            username=username,
            filter_by_owner=args.owner,
            limit=args.limit,
            show_all=args.all,
            verbose=args.verbose
        )

        # Format and display
        output = format_resources(result)
        print(output)

    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")


def cmd_permissions(args):
    """Display user's AWS permissions"""
    print("=== CCC CLI Permissions ===\n")

    config = load_config()
    profile = config.get('profile', 'cca')
    region = config.get('region', 'us-east-1')

    try:
        # Create session
        session = boto3.Session(profile_name=profile, region_name=region)

        # Get permissions using SDK
        result = get_user_permissions(session, verbose=args.verbose)

        # Test permissions if requested
        test_results = None
        if args.test:
            test_results = test_permissions(session)

        # Format and display
        output = format_permissions(result, test_results)
        print(output)

    except UnicodeEncodeError as e:
        print(f"[ERROR] Character encoding error: {e}")
        print("[INFO] This may be due to special characters in the output")
        print("[INFO] Try running in a UTF-8 compatible terminal")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        print("[INFO] If this persists, please report this issue")


def main():
    parser = argparse.ArgumentParser(
        description='CCC CLI - Cloud CLI Access Tool (v0.2 - Cognito)',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Configure command
    parser_configure = subparsers.add_parser('configure', help='Configure CCC CLI settings')
    parser_configure.set_defaults(func=cmd_configure)

    # Login command
    parser_login = subparsers.add_parser('login', help='Login and obtain AWS credentials')
    parser_login.set_defaults(func=cmd_login)

    # Refresh command
    parser_refresh = subparsers.add_parser('refresh', help='Refresh AWS credentials')
    parser_refresh.set_defaults(func=cmd_refresh)

    # Logout command
    parser_logout = subparsers.add_parser('logout', help='Logout and clear credentials')
    parser_logout.set_defaults(func=cmd_logout)

    # Register command
    parser_register = subparsers.add_parser('register', help='Register a new user')
    parser_register.set_defaults(func=cmd_register)

    # Forgot password command
    parser_forgot = subparsers.add_parser('forgot-password', help='Reset password via email verification')
    parser_forgot.set_defaults(func=cmd_forgot_password)

    # Change password command
    parser_change = subparsers.add_parser('change-password', help='Change password (requires current password)')
    parser_change.set_defaults(func=cmd_change_password)

    # Whoami command
    parser_whoami = subparsers.add_parser('whoami', help='Display current user information')
    parser_whoami.set_defaults(func=cmd_whoami)

    # Version command
    parser_version = subparsers.add_parser('version', help='Display version information')
    parser_version.set_defaults(func=cmd_version)

    # History command
    parser_history = subparsers.add_parser('history', help='Display history of AWS operations')
    parser_history.add_argument('--days', type=int, default=7, help='Number of days to look back (default: 7)')
    parser_history.add_argument('--limit', type=int, default=50, help='Maximum number of events to show (default: 50)')
    parser_history.add_argument('--verbose', action='store_true', help='Show detailed event information')
    parser_history.set_defaults(func=cmd_history)

    # Resources command
    parser_resources = subparsers.add_parser('resources', help='Display all AWS resources')
    parser_resources.add_argument('--owner', action='store_true', help='Filter resources by Owner tag matching your username')
    parser_resources.add_argument('--all', action='store_true', help='Show all resources without limit')
    parser_resources.add_argument('--limit', type=int, default=10, help='Limit resources shown per type (default: 10)')
    parser_resources.add_argument('--verbose', action='store_true', help='Show resource tags')
    parser_resources.set_defaults(func=cmd_resources)

    # Permissions command
    parser_permissions = subparsers.add_parser('permissions', help='Display user AWS permissions')
    parser_permissions.add_argument('--verbose', action='store_true', help='Show full policy documents')
    parser_permissions.add_argument('--test', action='store_true', help='Test common permissions')
    parser_permissions.set_defaults(func=cmd_permissions)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    args.func(args)


if __name__ == '__main__':
    main()
