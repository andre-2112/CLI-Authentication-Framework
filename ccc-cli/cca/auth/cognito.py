"""
Cognito Authentication Module
Handles Amazon Cognito authentication and AWS credential federation.
"""

import boto3
import requests
import json
from datetime import datetime, timezone
from botocore.exceptions import ClientError


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

    def register(self, email, password, first_name=None, last_name=None, lambda_url=None):
        """
        Register a new user via Lambda registration endpoint
        Returns: dict with registration result
        """
        if not lambda_url:
            raise Exception("Lambda URL is required for registration. Please set 'lambda_url' in config or pass as parameter.")

        try:
            print(f"[REGISTER] Submitting registration request...")

            # Build registration data
            data = {
                'email': email,
                'password': password
            }

            # Add optional names if provided
            if first_name:
                data['first_name'] = first_name
            if last_name:
                data['last_name'] = last_name

            # Call Lambda registration endpoint
            response = requests.post(
                f"{lambda_url}register",
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )

            response_data = response.json()

            if response.status_code == 200:
                print(f"[OK] Registration submitted successfully!")
                return response_data
            else:
                error_msg = response_data.get('error', 'Registration failed')
                raise Exception(error_msg)

        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error during registration: {e}")
        except json.JSONDecodeError:
            raise Exception("Invalid response from registration service")
        except Exception as e:
            if "Lambda URL is required" in str(e):
                raise
            raise Exception(f"Registration failed: {e}")

    def forgot_password(self, username):
        """
        Initiate forgot password flow
        Sends verification code to user's email
        Returns: dict with CodeDeliveryDetails
        """
        try:
            print(f"[FORGOT-PASSWORD] Initiating forgot password flow...")

            response = self.cognito_client.forgot_password(
                ClientId=self.app_client_id,
                Username=username
            )

            print(f"[OK] Verification code sent to your email!")
            print(f"[INFO] Destination: {response['CodeDeliveryDetails'].get('Destination', 'your email')}")

            return response['CodeDeliveryDetails']

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'UserNotFoundException':
                raise Exception("User not found")
            elif error_code == 'InvalidParameterException':
                raise Exception("Invalid parameters")
            elif error_code == 'LimitExceededException':
                raise Exception("Too many attempts. Please try again later.")
            else:
                raise Exception(f"Forgot password failed: {e.response['Error']['Message']}")

    def confirm_forgot_password(self, username, code, new_password):
        """
        Confirm forgot password with verification code
        Sets the new password
        """
        try:
            print(f"[CONFIRM-PASSWORD] Confirming new password...")

            self.cognito_client.confirm_forgot_password(
                ClientId=self.app_client_id,
                Username=username,
                ConfirmationCode=code,
                Password=new_password
            )

            print(f"[OK] Password changed successfully!")
            print(f"[INFO] You can now login with your new password")

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'CodeMismatchException':
                raise Exception("Invalid verification code")
            elif error_code == 'ExpiredCodeException':
                raise Exception("Verification code has expired. Please request a new one.")
            elif error_code == 'InvalidPasswordException':
                raise Exception("Password does not meet requirements (8+ chars, uppercase, lowercase, number, symbol)")
            elif error_code == 'UserNotFoundException':
                raise Exception("User not found")
            else:
                raise Exception(f"Password reset failed: {e.response['Error']['Message']}")

    def change_password(self, access_token, old_password, new_password):
        """
        Change password (requires current password and access token)
        """
        try:
            print(f"[CHANGE-PASSWORD] Changing password...")

            self.cognito_client.change_password(
                AccessToken=access_token,
                PreviousPassword=old_password,
                ProposedPassword=new_password
            )

            print(f"[OK] Password changed successfully!")
            print(f"[INFO] You can continue using your current session")

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NotAuthorizedException':
                raise Exception("Current password is incorrect")
            elif error_code == 'InvalidPasswordException':
                raise Exception("New password does not meet requirements (8+ chars, uppercase, lowercase, number, symbol)")
            elif error_code == 'LimitExceededException':
                raise Exception("Too many attempts. Please try again later.")
            else:
                raise Exception(f"Password change failed: {e.response['Error']['Message']}")
