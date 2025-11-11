"""
AWS Credentials Management
Handles saving and loading AWS credentials to/from ~/.aws/credentials file.
"""

import os
import configparser
from pathlib import Path


# Configuration file paths
CREDENTIALS_FILE = Path.home() / ".aws" / "credentials"


def save_credentials(credentials, profile='cca'):
    """
    Save AWS credentials to ~/.aws/credentials file

    Args:
        credentials: dict with AccessKeyId, SecretAccessKey, SessionToken, Expiration
        profile: AWS profile name (default: 'cca')
    """
    # Ensure .aws directory exists
    credentials_dir = CREDENTIALS_FILE.parent
    credentials_dir.mkdir(parents=True, exist_ok=True)

    # Read existing credentials file
    config_content = {}
    if CREDENTIALS_FILE.exists():
        try:
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


def remove_credentials(profile='cca'):
    """
    Remove AWS credentials profile from ~/.aws/credentials file

    Args:
        profile: AWS profile name to remove (default: 'cca')
    """
    if CREDENTIALS_FILE.exists():
        try:
            parser = configparser.ConfigParser()
            parser.read(CREDENTIALS_FILE)

            if parser.has_section(profile):
                parser.remove_section(profile)

                with open(CREDENTIALS_FILE, 'w') as f:
                    parser.write(f)

                print(f"[OK] Removed profile '{profile}' from {CREDENTIALS_FILE}")
                return True
        except Exception as e:
            print(f"[WARN] Could not remove credentials: {e}")
            return False
    return False
