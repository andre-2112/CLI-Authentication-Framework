#!/usr/bin/env python3
"""
Test script to perform login and test all CCC commands
"""

import sys
import boto3
from cca import CognitoAuthenticator, load_config, save_config, save_credentials
from datetime import datetime, timezone

def test_login():
    """Test login flow"""
    print("=== Testing CCC Login ===\n")

    config = load_config()

    if not config.get('user_pool_id'):
        print("[ERROR] Not configured. Please run 'ccc configure' first.")
        return False

    # Test credentials
    username = "testuser@example.com"
    password = "TestPassword123!"

    try:
        # Initialize authenticator
        auth = CognitoAuthenticator(config)
        print(f"[TEST] Authenticating as {username}...")

        # Authenticate with Cognito
        tokens = auth.authenticate(username, password)
        print("[OK] Authentication successful!")

        # Save tokens for future refresh
        config['tokens'] = {
            'id_token': tokens['IdToken'],
            'access_token': tokens['AccessToken'],
            'refresh_token': tokens.get('RefreshToken'),
            'username': username,
            'retrieved_at': datetime.now(timezone.utc).isoformat()
        }
        save_config(config)
        print("[OK] Tokens saved to config")

        # Get AWS credentials
        aws_credentials = auth.get_aws_credentials(tokens['IdToken'])
        print("[OK] AWS credentials obtained")

        # Save AWS credentials to ~/.aws/credentials
        save_credentials(aws_credentials, profile=config.get('profile', 'cca'))
        print("[OK] Credentials saved to AWS profile")

        print(f"\n[SUCCESS] Login test passed!")
        print(f"  - Profile: {config.get('profile', 'cca')}")
        print(f"  - Region: {config.get('region', 'us-east-1')}")
        print(f"  - Expiration: {aws_credentials['Expiration']}")

        return True

    except Exception as e:
        print(f"\n[FAILED] Login test failed: {e}")
        return False

if __name__ == '__main__':
    success = test_login()
    sys.exit(0 if success else 1)
