#!/usr/bin/env python3
"""
CCC CLI - Cloud CLI Access Tool (v0.2 - Cognito)
Provides secure CLI authentication to AWS using Amazon Cognito.
"""

import sys
import os
import json
import argparse
import boto3
import getpass
from pathlib import Path
from datetime import datetime, timezone
from botocore.exceptions import ClientError, NoCredentialsError

# Version
VERSION = "0.2.0"

# Configuration file paths
CONFIG_DIR = Path.home() / ".ccc"
CONFIG_FILE = CONFIG_DIR / "config.json"
CREDENTIALS_FILE = Path.home() / ".aws" / "credentials"

class CognitoAuthenticator:
    """Handles Cognito authentication and AWS credential management"""

    def __init__(self, config=None):
        self.config = config or {}
        self.user_pool_id = self.config.get('user_pool_id')
        self.app_client_id = self.config.get('app_client_id')
        self.identity_pool_id = self.config.get('identity_pool_id')
        self.region = self.config.get('region', 'us-east-1')
        self.profile = self.config.get('profile', 'cca')

        if self.user_pool_id and self.app_client_id:
            self.cognito_client = boto3.client('cognito-idp', region_name=self.region)
        if self.identity_pool_id:
            self.identity_client = boto3.client('cognito-identity', region_name=self.region)

    def authenticate(self, username, password):
        """
        Authenticate user with Cognito using USER_PASSWORD_AUTH flow
        Returns: dict with tokens (IdToken, AccessToken, RefreshToken)
        """
        try:
            print(f"[AUTH] Authenticating with Cognito...")
            response = self.cognito_client.initiate_auth(
                ClientId=self.app_client_id,
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': username,
                    'PASSWORD': password
                }
            )

            if 'AuthenticationResult' in response:
                tokens = response['AuthenticationResult']
                print(f"[OK] Authentication successful!")
                return tokens
            else:
                raise Exception("Authentication did not return tokens")

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NotAuthorizedException':
                raise Exception("Invalid username or password")
            elif error_code == 'UserNotFoundException':
                raise Exception("User not found")
            elif error_code == 'UserNotConfirmedException':
                raise Exception("User not confirmed")
            else:
                raise Exception(f"Authentication failed: {e.response['Error']['Message']}")

    def get_aws_credentials(self, id_token):
        """
        Exchange Cognito ID token for temporary AWS credentials
        Returns: dict with AWS credentials
        """
        try:
            print(f"[AUTH] Exchanging Cognito token for AWS credentials...")

            # Get Identity ID
            identity_response = self.identity_client.get_id(
                IdentityPoolId=self.identity_pool_id,
                Logins={
                    f'cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}': id_token
                }
            )
            identity_id = identity_response['IdentityId']
            print(f"[AUTH] Identity ID: {identity_id}")

            # Get credentials for identity
            credentials_response = self.identity_client.get_credentials_for_identity(
                IdentityId=identity_id,
                Logins={
                    f'cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}': id_token
                }
            )

            credentials = credentials_response['Credentials']
            print(f"[OK] AWS credentials obtained!")
            print(f"[INFO] Credentials expire at: {credentials['Expiration']}")

            return {
                'AccessKeyId': credentials['AccessKeyId'],
                'SecretAccessKey': credentials['SecretKey'],
                'SessionToken': credentials['SessionToken'],
                'Expiration': credentials['Expiration'].isoformat()
            }

        except ClientError as e:
            raise Exception(f"Failed to get AWS credentials: {e.response['Error']['Message']}")

    def save_credentials(self, credentials, profile=None):
        """Save AWS credentials to ~/.aws/credentials file"""
        profile = profile or self.profile

        # Ensure .aws directory exists
        credentials_dir = CREDENTIALS_FILE.parent
        credentials_dir.mkdir(parents=True, exist_ok=True)

        # Read existing credentials file
        config_content = {}
        if CREDENTIALS_FILE.exists():
            try:
                import configparser
                parser = configparser.ConfigParser()
                parser.read(CREDENTIALS_FILE)
                config_content = {section: dict(parser.items(section)) for section in parser.sections()}
            except Exception as e:
                print(f"[WARN] Could not read existing credentials file: {e}")

        # Update profile
        config_content[profile] = {
            'aws_access_key_id': credentials['AccessKeyId'],
            'aws_secret_access_key': credentials['SecretAccessKey'],
            'aws_session_token': credentials['SessionToken'],
            '# expires_at': credentials['Expiration']
        }

        # Write credentials file
        import configparser
        parser = configparser.ConfigParser()
        for section, values in config_content.items():
            parser.add_section(section)
            for key, value in values.items():
                parser.set(section, key, value)

        with open(CREDENTIALS_FILE, 'w') as f:
            parser.write(f)

        # Set restrictive permissions (Unix-like systems)
        try:
            os.chmod(CREDENTIALS_FILE, 0o600)
        except Exception:
            pass

        print(f"[OK] Credentials saved to {CREDENTIALS_FILE}")
        print(f"[OK] AWS Profile: {profile}")

    def refresh_credentials(self, refresh_token):
        """Refresh AWS credentials using refresh token"""
        try:
            print(f"[AUTH] Refreshing credentials...")
            response = self.cognito_client.initiate_auth(
                ClientId=self.app_client_id,
                AuthFlow='REFRESH_TOKEN_AUTH',
                AuthParameters={
                    'REFRESH_TOKEN': refresh_token
                }
            )

            if 'AuthenticationResult' in response:
                tokens = response['AuthenticationResult']
                print(f"[OK] Credentials refreshed successfully!")
                return tokens
            else:
                raise Exception("Refresh did not return tokens")

        except ClientError as e:
            raise Exception(f"Failed to refresh credentials: {e.response['Error']['Message']}")


def load_config():
    """Load CCC configuration from ~/.ccc/config.json"""
    if not CONFIG_FILE.exists():
        return {}

    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load config: {e}")
        return {}


def save_config(config):
    """Save CCC configuration to ~/.ccc/config.json"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"[OK] Configuration saved to {CONFIG_FILE}")
    except Exception as e:
        print(f"[ERROR] Failed to save config: {e}")
        sys.exit(1)


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
        auth.save_credentials(aws_credentials)

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
        auth.save_credentials(aws_credentials)

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

    if CREDENTIALS_FILE.exists():
        try:
            import configparser
            parser = configparser.ConfigParser()
            parser.read(CREDENTIALS_FILE)

            if parser.has_section(profile):
                parser.remove_section(profile)

                with open(CREDENTIALS_FILE, 'w') as f:
                    parser.write(f)

                print(f"[OK] Removed profile '{profile}' from {CREDENTIALS_FILE}")
        except Exception as e:
            print(f"[WARN] Could not remove credentials: {e}")

    print("[OK] Logout complete!")


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

    events = []
    source = None

    # Try CloudTrail first (recent events, fast)
    try:
        from datetime import timedelta
        start_time = datetime.now(timezone.utc) - timedelta(days=args.days)

        print("[INFO] Fetching events from CloudTrail...")
        cloudtrail = session.client('cloudtrail')

        response = cloudtrail.lookup_events(
            LookupAttributes=[
                {
                    'AttributeKey': 'Username',
                    'AttributeValue': username
                }
            ],
            StartTime=start_time,
            MaxResults=args.limit
        )

        ct_events = response.get('Events', [])

        if ct_events:
            # Convert CloudTrail events to common format
            for event in ct_events:
                events.append({
                    'time': event['EventTime'],
                    'event_name': event['EventName'],
                    'resources': event.get('Resources', []),
                    'error_code': event.get('ErrorCode', ''),
                    'event_id': event['EventId'],
                    'source': 'CloudTrail'
                })
            source = 'CloudTrail'
            print(f"[OK] Retrieved {len(events)} events from CloudTrail\n")

    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AccessDeniedException':
            print("[INFO] CloudTrail access denied, trying CloudWatch Logs...\n")
        else:
            print(f"[WARN] CloudTrail error: {error_code}, trying CloudWatch Logs...\n")
    except Exception as e:
        print(f"[WARN] CloudTrail unavailable: {e}, trying CloudWatch Logs...\n")

    # Fallback to CloudWatch Logs if CloudTrail failed or returned no events
    if not events:
        try:
            from datetime import timedelta
            import time

            print("[INFO] Fetching events from CloudWatch Logs...")
            logs = session.client('logs')

            log_group_name = '/aws/cloudtrail/cca-users'

            # Calculate time range in milliseconds
            start_time = datetime.now(timezone.utc) - timedelta(days=args.days)
            start_time_ms = int(start_time.timestamp() * 1000)
            end_time_ms = int(time.time() * 1000)

            # Filter pattern to match events for this user
            filter_pattern = f'{{ $.userIdentity.arn = "*{username}*" }}'

            response = logs.filter_log_events(
                logGroupName=log_group_name,
                startTime=start_time_ms,
                endTime=end_time_ms,
                filterPattern=filter_pattern,
                limit=args.limit
            )

            log_events = response.get('events', [])

            if log_events:
                # Parse CloudWatch Logs events
                for log_event in log_events:
                    try:
                        event_data = json.loads(log_event['message'])
                        events.append({
                            'time': datetime.fromtimestamp(log_event['timestamp'] / 1000, tz=timezone.utc),
                            'event_name': event_data.get('eventName', 'Unknown'),
                            'resources': event_data.get('resources', []),
                            'error_code': event_data.get('errorCode', ''),
                            'event_id': event_data.get('eventID', 'N/A'),
                            'source': 'CloudWatch Logs'
                        })
                    except json.JSONDecodeError:
                        continue

                source = 'CloudWatch Logs'
                print(f"[OK] Retrieved {len(events)} events from CloudWatch Logs\n")

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceNotFoundException':
                print("[WARN] CloudWatch Logs group not found")
            elif error_code == 'AccessDeniedException':
                print("[ERROR] Access denied to CloudWatch Logs\n")
                print("Your IAM role does not have permission to view CloudWatch Logs.")
                print("\nRequired IAM permissions:")
                print("  - logs:FilterLogEvents")
                print("  - logs:GetLogEvents")
            else:
                print(f"[WARN] CloudWatch Logs error: {error_code}")
        except Exception as e:
            print(f"[WARN] CloudWatch Logs unavailable: {e}")

    # Display events if we found any
    if events:
        # Sort by time (most recent first)
        events.sort(key=lambda x: x['time'], reverse=True)

        print(f"{'Time':<20} {'Event':<30} {'Resource':<40} {'Status':<15}")
        print("-" * 105)

        for event in events[:args.limit]:
            event_time = event['time'].strftime('%Y-%m-%d %H:%M:%S')
            event_name = event['event_name'][:29]

            # Extract resource info
            resources = event['resources']
            if resources and isinstance(resources, list) and len(resources) > 0:
                if isinstance(resources[0], dict):
                    resource_name = resources[0].get('ResourceName', 'N/A')[:39]
                else:
                    resource_name = str(resources[0])[:39]
            else:
                resource_name = 'N/A'

            # Get error status
            error_code = event['error_code']
            status = 'Error' if error_code else 'Success'

            print(f"{event_time:<20} {event_name:<30} {resource_name:<40} {status:<15}")

            if args.verbose:
                print(f"  Event ID: {event['event_id']}")
                print(f"  Source: {event['source']}")
                if error_code:
                    print(f"  Error: {error_code}")
                print()

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

        # Use Resource Groups Tagging API to find all resources
        tagging = session.client('resourcegroupstaggingapi')

        print("[INFO] Scanning for resources...")

        # Get all resources (optionally filter by Owner tag)
        paginator = tagging.get_paginator('get_resources')

        # Try to filter by Owner tag if available
        tag_filters = []
        if args.owner:
            tag_filters = [{'Key': 'Owner', 'Values': [username]}]

        all_resources = []
        for page in paginator.paginate(TagFilters=tag_filters):
            all_resources.extend(page['ResourceTagMappingList'])

        if not all_resources:
            print("[INFO] No resources found")
            if not args.owner:
                print("[INFO] Tip: Use --owner to filter resources by Owner tag")
            return

        # Group resources by type
        resources_by_type = {}
        for resource in all_resources:
            arn = resource['ResourceARN']
            # Extract service from ARN (format: arn:aws:service:region:account:resource)
            parts = arn.split(':')
            if len(parts) >= 6:
                service = parts[2]
                resource_type = parts[5].split('/')[0] if '/' in parts[5] else parts[5]
            else:
                service = 'unknown'
                resource_type = 'unknown'

            key = f"{service}/{resource_type}"
            if key not in resources_by_type:
                resources_by_type[key] = []
            resources_by_type[key].append(resource)

        # Display summary
        print(f"\nFound {len(all_resources)} resources across {len(resources_by_type)} resource types:\n")

        for resource_type, resources in sorted(resources_by_type.items()):
            print(f"\n{resource_type} ({len(resources)} resources):")
            print("-" * 80)

            for resource in resources[:args.limit if not args.all else None]:
                arn = resource['ResourceARN']
                tags = {tag['Key']: tag['Value'] for tag in resource.get('Tags', [])}

                # Extract resource name from ARN
                resource_name = arn.split('/')[-1] if '/' in arn else arn.split(':')[-1]

                print(f"  Resource: {resource_name}")
                print(f"  ARN: {arn}")

                if args.verbose and tags:
                    print(f"  Tags:")
                    for key, value in tags.items():
                        print(f"    {key}: {value}")

                print()

            if not args.all and len(resources) > args.limit:
                print(f"  ... and {len(resources) - args.limit} more (use --all to see all)")

        print(f"\nTotal resources: {len(all_resources)}")

    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']

        if error_code == 'AccessDeniedException' or 'not authorized' in error_msg:
            print("[ERROR] Access denied to Resource Groups Tagging API\n")
            print("Your IAM role does not have permission to query AWS resources.")
            print("\nRequired IAM permissions:")
            print("  - tag:GetResources")
            print("  - tag:GetTagKeys (optional)")
            print("  - tag:GetTagValues (optional)\n")
            print("To enable this feature, ask your administrator to add the following policy:")
            print(json.dumps({
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Action": [
                        "tag:GetResources",
                        "tag:GetTagKeys",
                        "tag:GetTagValues"
                    ],
                    "Resource": "*"
                }]
            }, indent=2))
        elif error_code == 'InvalidClientTokenId':
            print("[ERROR] Invalid or expired credentials")
            print("[INFO] Run 'ccc refresh' or 'ccc login' to renew your credentials")
        elif error_code == 'ExpiredToken':
            print("[ERROR] Your session has expired")
            print("[INFO] Run 'ccc refresh' or 'ccc login' to obtain new credentials")
        else:
            print(f"[ERROR] Failed to list resources: {error_msg}")
            print(f"[ERROR CODE] {error_code}")
    except NoCredentialsError:
        print("[ERROR] No credentials found")
        print("[INFO] Run 'ccc login' first to authenticate")
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
        sts = session.client('sts')
        iam = session.client('iam')

        # Get caller identity
        identity = sts.get_caller_identity()
        arn = identity['Arn']

        print(f"User ARN: {arn}")
        print(f"Account: {identity['Account']}")
        print(f"User ID: {identity['UserId']}\n")

        # Determine if using assumed role
        if ':assumed-role/' in arn:
            role_name = arn.split('/')[-2]
            print(f"Role: {role_name}")
            print(f"Session: {arn.split('/')[-1]}\n")

            print("[INFO] Fetching role policies...\n")

            # Get role details
            try:
                role_response = iam.get_role(RoleName=role_name)
                role = role_response['Role']

                print(f"Role Created: {role['CreateDate']}")
                print(f"Max Session Duration: {role['MaxSessionDuration']} seconds")

                # Check for permission boundary
                if 'PermissionsBoundary' in role:
                    print(f"\nPermission Boundary: {role['PermissionsBoundary']['PermissionsBoundaryArn']}")

                print("\nAssumeRole Policy:")
                print(json.dumps(role['AssumeRolePolicyDocument'], indent=2))

                # List attached policies
                print("\nAttached Policies:")
                attached_policies = iam.list_attached_role_policies(RoleName=role_name)

                if attached_policies['AttachedPolicies']:
                    for policy in attached_policies['AttachedPolicies']:
                        print(f"  - {policy['PolicyName']} ({policy['PolicyArn']})")

                        if args.verbose:
                            # Get policy details
                            policy_response = iam.get_policy(PolicyArn=policy['PolicyArn'])
                            default_version = policy_response['Policy']['DefaultVersionId']

                            version_response = iam.get_policy_version(
                                PolicyArn=policy['PolicyArn'],
                                VersionId=default_version
                            )

                            print(f"\n    Policy Document:")
                            doc = version_response['PolicyVersion']['Document']
                            print(json.dumps(doc, indent=6))
                            print()
                else:
                    print("  (None)")

                # List inline policies
                print("\nInline Policies:")
                inline_policies = iam.list_role_policies(RoleName=role_name)

                if inline_policies['PolicyNames']:
                    for policy_name in inline_policies['PolicyNames']:
                        print(f"  - {policy_name}")

                        if args.verbose:
                            policy_response = iam.get_role_policy(
                                RoleName=role_name,
                                PolicyName=policy_name
                            )
                            print(f"\n    Policy Document:")
                            print(json.dumps(policy_response['PolicyDocument'], indent=6))
                            print()
                else:
                    print("  (None)")

            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == 'AccessDenied':
                    print("[ERROR] Access denied to IAM role details\n")
                    print("Your role does not have permission to view IAM role configurations.")
                    print("\nRequired IAM permissions:")
                    print("  - iam:GetRole")
                    print("  - iam:ListAttachedRolePolicies")
                    print("  - iam:ListRolePolicies")
                    print("  - iam:GetPolicy (for --verbose)")
                    print("  - iam:GetPolicyVersion (for --verbose)")
                    print("  - iam:GetRolePolicy (for --verbose)\n")
                    print("Note: You can still see your effective permissions, just not the role details.")
                else:
                    print(f"[ERROR] Failed to get role details: {e.response['Error']['Message']}")
                    print(f"[ERROR CODE] {error_code}")

        # Test common permissions
        if args.test:
            print("\n\nTesting Common Permissions:")
            print("-" * 80)

            test_permissions = [
                ('ec2:DescribeInstances', 'List EC2 instances'),
                ('s3:ListAllMyBuckets', 'List S3 buckets'),
                ('lambda:ListFunctions', 'List Lambda functions'),
                ('dynamodb:ListTables', 'List DynamoDB tables'),
                ('cloudwatch:DescribeAlarms', 'List CloudWatch alarms'),
                ('iam:GetUser', 'Get IAM user details'),
                ('iam:CreateUser', 'Create IAM users'),
            ]

            for action, description in test_permissions:
                try:
                    service = action.split(':')[0]
                    operation = action.split(':')[1]

                    if service == 'ec2' and operation == 'DescribeInstances':
                        ec2 = session.client('ec2')
                        ec2.describe_instances(MaxResults=5)
                        result = "[+] Allowed"
                    elif service == 's3' and operation == 'ListAllMyBuckets':
                        s3 = session.client('s3')
                        s3.list_buckets()
                        result = "[+] Allowed"
                    elif service == 'lambda' and operation == 'ListFunctions':
                        lambda_client = session.client('lambda')
                        lambda_client.list_functions(MaxItems=5)
                        result = "[+] Allowed"
                    elif service == 'dynamodb' and operation == 'ListTables':
                        dynamodb = session.client('dynamodb')
                        dynamodb.list_tables(Limit=5)
                        result = "[+] Allowed"
                    elif service == 'cloudwatch' and operation == 'DescribeAlarms':
                        cloudwatch = session.client('cloudwatch')
                        cloudwatch.describe_alarms(MaxRecords=5)
                        result = "[+] Allowed"
                    elif service == 'iam' and operation == 'GetUser':
                        iam.get_user()
                        result = "[+] Allowed"
                    elif service == 'iam' and operation == 'CreateUser':
                        # Don't actually create, just test with simulate
                        result = "[x] Not tested (dangerous)"
                    else:
                        result = "[?] Unknown"

                except ClientError as e:
                    if e.response['Error']['Code'] in ['AccessDenied', 'UnauthorizedOperation']:
                        result = "[x] Denied"
                    else:
                        result = f"[?] {e.response['Error']['Code']}"
                except Exception as e:
                    result = f"? Error: {str(e)[:30]}"

                print(f"  {action:<30} {description:<30} {result}")

    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']

        if error_code == 'AccessDenied' or error_code == 'AccessDeniedException':
            print("[ERROR] Access denied\n")
            print("Your IAM role does not have permission to retrieve identity information.")
            print("\nRequired IAM permissions:")
            print("  - sts:GetCallerIdentity (usually always available)")
            print("  - iam:GetRole (to view role configuration)")
            print("  - iam:ListAttachedRolePolicies (to view policies)")
        elif error_code == 'InvalidClientTokenId':
            print("[ERROR] Invalid or expired credentials")
            print("[INFO] Run 'ccc refresh' or 'ccc login' to renew your credentials")
        elif error_code == 'ExpiredToken':
            print("[ERROR] Your session has expired")
            print("[INFO] Run 'ccc refresh' or 'ccc login' to obtain new credentials")
        else:
            print(f"[ERROR] Failed to get permissions: {error_msg}")
            print(f"[ERROR CODE] {error_code}")
    except NoCredentialsError:
        print("[ERROR] No credentials found")
        print("[INFO] Run 'ccc login' first to authenticate")
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
