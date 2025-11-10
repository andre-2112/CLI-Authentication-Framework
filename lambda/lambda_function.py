import json
import boto3
import hmac
import hashlib
import base64
import os
from datetime import datetime, timedelta
from urllib.parse import parse_qs

ses = boto3.client('ses')
cognito = boto3.client('cognito-idp')
kms = boto3.client('kms')

# Environment variables
USER_POOL_ID = os.environ['USER_POOL_ID']
KMS_KEY_ID = os.environ['KMS_KEY_ID']
FROM_EMAIL = os.environ['FROM_EMAIL']
ADMIN_EMAIL = os.environ['ADMIN_EMAIL']
SECRET_KEY = os.environ['SECRET_KEY']

# CORS headers for all responses
CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
}

def get_display_name(user_data):
    """Get display name from user_data, handling optional first/last names"""
    first_name = user_data.get('first_name', '').strip() if user_data.get('first_name') else ''
    last_name = user_data.get('last_name', '').strip() if user_data.get('last_name') else ''

    if first_name and last_name:
        return f"{first_name} {last_name}"
    elif first_name:
        return first_name
    elif last_name:
        return last_name
    else:
        # Use email username as fallback
        return user_data.get('email', 'User').split('@')[0]

def get_greeting_name(user_data):
    """Get friendly greeting name (first name or email username)"""
    first_name = user_data.get('first_name', '').strip() if user_data.get('first_name') else ''
    if first_name:
        return first_name
    else:
        return user_data.get('email', 'User').split('@')[0]

def lambda_handler(event, context):
    """
    Single Lambda function handling:
    - Registration submissions (with password)
    - Approval actions (creates Cognito user)
    - Denial actions
    """

    print(f"[LAMBDA] Event: {json.dumps(event, default=str)}")

    # Handle OPTIONS preflight requests
    if event.get('requestContext', {}).get('http', {}).get('method') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': ''
        }

    # Determine action based on path
    path = event.get('rawPath', event.get('path', ''))
    print(f"[LAMBDA] Request path: {path}")

    if path == '/register' or path == '/':
        print("[REG] Handling registration request")
        return handle_registration(event)
    elif path == '/approve':
        print("[APP] Handling approval request")
        return handle_approval(event)
    elif path == '/deny':
        print("[DENY] Handling denial request")
        return handle_denial(event)
    else:
        print(f"[ERROR] Unknown path: {path}")
        return {
            'statusCode': 404,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'Not found'})
        }

def handle_registration(event):
    """Handle new registration submissions with password"""

    # Parse request body
    try:
        if event.get('body'):
            body = json.loads(event['body'])
        else:
            return error_response('Missing request body', 400)
    except json.JSONDecodeError:
        return error_response('Invalid JSON', 400)

    # Validate required fields (email and password only - names are optional!)
    required = ['email', 'password']
    missing = [f for f in required if not body.get(f)]

    if missing:
        return error_response(f'Missing fields: {", ".join(missing)}', 400)

    # Validate password strength
    password = body['password']
    if len(password) < 8:
        return error_response('Password must be at least 8 characters long', 400)

    # Get optional names (use email username as fallback for display)
    first_name = body.get('first_name', '').strip() or None
    last_name = body.get('last_name', '').strip() or None
    display_name = f"{first_name} {last_name}" if first_name and last_name else body['email'].split('@')[0]

    print(f"[REG] Processing registration for: {display_name} ({body['email']})")
    print(f"[REG] Password received: {len(password)} characters")
    print(f"[REG] Names provided: first_name={'Yes' if first_name else 'No'}, last_name={'Yes' if last_name else 'No'}")

    # Encrypt password with KMS
    try:
        print(f"[KMS] Encrypting password with KMS key: {KMS_KEY_ID}")
        encrypted_pwd = kms.encrypt(
            KeyId=KMS_KEY_ID,
            Plaintext=password.encode('utf-8')
        )
        encrypted_pwd_b64 = base64.b64encode(encrypted_pwd['CiphertextBlob']).decode('utf-8')
        print(f"[KMS] Password encrypted successfully. Ciphertext length: {len(encrypted_pwd_b64)}")
    except Exception as e:
        print(f"[KMS ERROR] Failed to encrypt password: {e}")
        return error_response(f'Failed to encrypt password: {str(e)}', 500)

    # Create JWT token with user data and encrypted password
    user_data = {
        'email': body['email'],
        'first_name': first_name,  # Can be None
        'last_name': last_name,     # Can be None
        'encrypted_password': encrypted_pwd_b64,  # Store encrypted password in JWT
        'submitted_at': datetime.utcnow().isoformat(),
        'expires_at': (datetime.utcnow() + timedelta(days=7)).isoformat()
    }

    approve_token = create_signed_token(user_data, 'approve')
    deny_token = create_signed_token(user_data, 'deny')

    # Get Lambda Function URL
    lambda_url = event['requestContext']['domainName']
    protocol = 'https'

    approve_url = f"{protocol}://{lambda_url}/approve?token={approve_token}"
    deny_url = f"{protocol}://{lambda_url}/deny?token={deny_token}"

    print(f"[REG] Approve URL: {approve_url}")
    print(f"[REG] Deny URL: {deny_url}")

    # Send email to admin
    try:
        send_admin_email(user_data, approve_url, deny_url)
        print(f"[+] Registration completed successfully for: {user_data['email']}")
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        return error_response(f'Failed to send email: {str(e)}', 500)

    return {
        'statusCode': 200,
        'headers': {
            **CORS_HEADERS,
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'message': 'Registration submitted successfully',
            'status': 'pending_approval'
        })
    }

def handle_approval(event):
    """Handle approval action - creates Cognito user with password"""

    # Get token from query parameters
    params = event.get('queryStringParameters', {}) or {}
    token = params.get('token')

    if not token:
        return html_response('<h1>Error: Missing token</h1>', 400)

    # Verify and decode token
    try:
        user_data = verify_signed_token(token, 'approve')
    except Exception as e:
        return html_response(f'<h1>Error: Invalid or expired token</h1><p>{str(e)}</p>', 400)

    # Create display name for logging
    display_name = f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip() or user_data['email'].split('@')[0]
    print(f"[APP] Approved registration for: {display_name} ({user_data['email']})")

    # Check if user already exists
    try:
        print(f"[APP] Checking if user already exists: {user_data['email']}")
        existing = cognito.list_users(
            UserPoolId=USER_POOL_ID,
            Filter=f'email = "{user_data["email"]}"'
        )

        if existing.get('Users'):
            print(f"[APP] User already exists: {user_data['email']}")
            return html_response(
                f'<h1>User Already Exists</h1><p>User {user_data["email"]} was already created.</p>',
                200
            )
    except Exception as e:
        print(f"[ERROR] Error checking existing user: {e}")

    # Decrypt password from JWT using KMS
    plaintext_password = None
    try:
        print(f"[KMS] Decrypting password from JWT token")
        encrypted_pwd_blob = base64.b64decode(user_data['encrypted_password'])
        decrypted = kms.decrypt(
            CiphertextBlob=encrypted_pwd_blob
        )
        plaintext_password = decrypted['Plaintext'].decode('utf-8')
        print(f"[KMS] Password decrypted successfully. Length: {len(plaintext_password)}")
    except Exception as e:
        print(f"[KMS ERROR] Failed to decrypt password: {e}")
        return html_response(
            f'<h1>Error Decrypting Password</h1><p>{str(e)}</p>',
            500
        )

    # Create user in Cognito
    try:
        print(f"[COGNITO] Creating user in Cognito User Pool: {user_data['email']}")

        # Build user attributes (names are optional)
        user_attributes = [
            {'Name': 'email', 'Value': user_data['email']},
            {'Name': 'email_verified', 'Value': 'true'}
        ]

        # Add names only if provided
        if user_data.get('first_name'):
            user_attributes.append({'Name': 'given_name', 'Value': user_data['first_name']})
        if user_data.get('last_name'):
            user_attributes.append({'Name': 'family_name', 'Value': user_data['last_name']})
        if user_data.get('first_name') and user_data.get('last_name'):
            user_attributes.append({'Name': 'name', 'Value': f"{user_data['first_name']} {user_data['last_name']}"})
        elif user_data.get('first_name'):
            user_attributes.append({'Name': 'name', 'Value': user_data['first_name']})

        # Create user with admin_create_user
        cognito.admin_create_user(
            UserPoolId=USER_POOL_ID,
            Username=user_data['email'],  # Using email as username
            UserAttributes=user_attributes,
            MessageAction='SUPPRESS'  # Don't send welcome email from Cognito
        )

        print(f"[COGNITO] User created successfully: {user_data['email']}")

        # Set permanent password
        print(f"[COGNITO] Setting permanent password for user")
        cognito.admin_set_user_password(
            UserPoolId=USER_POOL_ID,
            Username=user_data['email'],
            Password=plaintext_password,
            Permanent=True
        )

        print(f"[COGNITO] Password set successfully for user: {user_data['email']}")

        # Send welcome email
        print(f"[EMAIL] Sending welcome email to: {user_data['email']}")
        send_welcome_email(user_data)
        print(f"[+] Welcome email sent successfully")

        return html_response(f'''
            <html>
            <head>
                <title>Registration Approved</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        max-width: 600px;
                        margin: 50px auto;
                        padding: 20px;
                        text-align: center;
                    }}
                    h1 {{ color: #28a745; }}
                    .info {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <h1>✅ Registration Approved</h1>
                <div class="info">
                    <p><strong>Email:</strong> {user_data["email"]}</p>
                    <p><strong>Name:</strong> {get_display_name(user_data)}</p>
                </div>
                <p>User has been created successfully in Cognito.</p>
                <p>They will receive a welcome email with login instructions.</p>
            </body>
            </html>
        ''', 200)

    except Exception as e:
        print(f"[ERROR] Error creating Cognito user: {e}")
        print(f"[ERROR] Error details: {type(e).__name__}: {str(e)}")
        return html_response(
            f'<h1>Error Creating User</h1><p>{str(e)}</p>',
            500
        )
    finally:
        # Always cleanup plaintext password from memory
        if plaintext_password is not None:
            del plaintext_password
            print(f"[SECURITY] Plaintext password cleaned from memory")

def handle_denial(event):
    """Handle denial action"""

    # Get token from query parameters
    params = event.get('queryStringParameters', {}) or {}
    token = params.get('token')

    if not token:
        return html_response('<h1>Error: Missing token</h1>', 400)

    # Verify and decode token
    try:
        user_data = verify_signed_token(token, 'deny')
    except Exception as e:
        return html_response(f'<h1>Error: Invalid or expired token</h1><p>{str(e)}</p>', 400)

    print(f"[DENY] Registration denied for: {get_display_name(user_data)} ({user_data['email']})")

    # Send denial email
    try:
        send_denial_email(user_data)
    except Exception as e:
        print(f"[ERROR] Error sending denial email: {e}")

    return html_response(f'''
        <html>
        <head>
            <title>Registration Denied</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 600px;
                    margin: 50px auto;
                    padding: 20px;
                    text-align: center;
                }}
                h1 {{ color: #dc3545; }}
                .info {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <h1>❌ Registration Denied</h1>
            <div class="info">
                <p><strong>Email:</strong> {user_data["email"]}</p>
                <p><strong>Name:</strong> {get_display_name(user_data)}</p>
            </div>
            <p>Registration request has been denied.</p>
        </body>
        </html>
    ''', 200)

def create_signed_token(data, action):
    """Create JWT-like signed token with data and action"""
    payload = {
        'data': data,
        'action': action
    }

    payload_json = json.dumps(payload, separators=(',', ':'))
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode()

    signature = hmac.new(
        SECRET_KEY.encode(),
        payload_b64.encode(),
        hashlib.sha256
    ).hexdigest()

    token = f"{payload_b64}.{signature}"
    return base64.urlsafe_b64encode(token.encode()).decode()

def verify_signed_token(token, expected_action):
    """Verify and decode signed token"""
    try:
        # Decode outer base64
        decoded = base64.urlsafe_b64decode(token.encode()).decode()
        payload_b64, signature = decoded.split('.')

        # Verify signature
        expected_sig = hmac.new(
            SECRET_KEY.encode(),
            payload_b64.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_sig):
            raise ValueError("Invalid signature")

        # Decode payload
        payload_json = base64.urlsafe_b64decode(payload_b64.encode()).decode()
        payload = json.loads(payload_json)

        # Verify action
        if payload['action'] != expected_action:
            raise ValueError("Invalid action")

        # Check expiration
        expires_at = datetime.fromisoformat(payload['data']['expires_at'])
        if datetime.utcnow() > expires_at:
            raise ValueError("Token expired")

        return payload['data']

    except Exception as e:
        raise ValueError(f"Token verification failed: {str(e)}")

def send_admin_email(user_data, approve_url, deny_url):
    """Send approval request email to admin"""

    subject = f"[CCA 0.2] New Registration Request: {user_data['email']}"

    # Don't include password info in email (it's encrypted in the token)
    text_body = f"""
New Cloud CLI Access registration request:

Email: {user_data['email']}
Name: {get_display_name(user_data)}
Submitted: {user_data['submitted_at']}

To approve this request:
{approve_url}

To deny this request:
{deny_url}

These links will expire in 7 days.

Note: This is CCA 0.2 with Cognito authentication.
"""

    html_body = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 5px; }}
        .content {{ background: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 5px; }}
        .info-row {{ margin: 10px 0; }}
        .label {{ font-weight: bold; color: #555; }}
        .button {{ display: inline-block; padding: 12px 30px; margin: 10px 5px; text-decoration: none; border-radius: 5px; font-weight: bold; }}
        .approve {{ background: #28a745; color: white; }}
        .deny {{ background: #dc3545; color: white; }}
        .actions {{ text-align: center; margin: 30px 0; }}
        .badge {{ display: inline-block; background: #ffc107; color: #000; padding: 4px 8px; border-radius: 3px; font-size: 12px; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>🔐 New Registration Request <span class="badge">CCA 0.2</span></h2>
        </div>
        <div class="content">
            <div class="info-row"><span class="label">Email:</span> {user_data['email']}</div>
            <div class="info-row"><span class="label">Name:</span> {get_display_name(user_data)}</div>
            <div class="info-row"><span class="label">Submitted:</span> {user_data['submitted_at']}</div>
        </div>
        <div class="actions">
            <a href="{approve_url}" class="button approve">✓ Approve</a>
            <a href="{deny_url}" class="button deny">✗ Deny</a>
        </div>
        <p style="color: #666; font-size: 12px; text-align: center;">These links will expire in 7 days.</p>
        <p style="color: #666; font-size: 12px; text-align: center;">🔒 User password is encrypted with AWS KMS in the approval token.</p>
    </div>
</body>
</html>
"""

    try:
        print(f"[EMAIL] Sending admin approval email to: {ADMIN_EMAIL}")
        print(f"[EMAIL] FROM address: {FROM_EMAIL}")
        response = ses.send_email(
            Source=FROM_EMAIL,
            Destination={'ToAddresses': [ADMIN_EMAIL]},
            Message={
                'Subject': {'Data': subject},
                'Body': {
                    'Text': {'Data': text_body},
                    'Html': {'Data': html_body}
                }
            }
        )
        print(f"[+] Admin email sent successfully. MessageId: {response.get('MessageId')}")
    except Exception as e:
        print(f"[ERROR] Error sending admin email: {e}")
        print(f"[ERROR] Error details: {type(e).__name__}: {str(e)}")
        raise

def send_welcome_email(user_data):
    """Send welcome email to approved user - password already set!"""

    subject = "Welcome to Cloud CLI Access (CCA 0.2)"

    text_body = f"""
Welcome to Cloud CLI Access!

Your registration has been approved and your account is ready to use.

Email: {user_data['email']}
Name: {get_display_name(user_data)}

Your password has been set successfully. You can now log in using the CCC CLI tool:

1. Install the CCC CLI tool (if not already installed)
2. Run: ccc configure
3. Run: ccc login
4. When prompted, enter your email and password

For help, contact your administrator.

Best regards,
Cloud CLI Access Team
"""

    html_body = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 5px; text-align: center; }}
        .content {{ padding: 20px; }}
        .info-box {{ background: #f8f9fa; padding: 15px; border-left: 4px solid #667eea; margin: 20px 0; }}
        .success {{ background: #d4edda; border-left-color: #28a745; padding: 15px; margin: 20px 0; }}
        .steps {{ background: #f8f9fa; padding: 20px; border-radius: 5px; }}
        .step {{ margin: 15px 0; padding-left: 30px; position: relative; }}
        .step:before {{ content: "→"; position: absolute; left: 0; color: #667eea; font-weight: bold; }}
        .badge {{ display: inline-block; background: #ffc107; color: #000; padding: 4px 8px; border-radius: 3px; font-size: 12px; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Welcome to Cloud CLI Access! <span class="badge">CCA 0.2</span></h1>
        </div>
        <div class="content">
            <div class="success">
                <strong>✅ Your Account is Ready!</strong><br>
                Your registration has been approved and your password has been set successfully.
            </div>

            <div class="info-box">
                <strong>Your Account:</strong><br>
                Email: {user_data['email']}<br>
                Name: {get_display_name(user_data)}
            </div>

            <h3>Get Started:</h3>
            <div class="steps">
                <div class="step">Install the CCC CLI tool</div>
                <div class="step">Run: <code>ccc configure</code></div>
                <div class="step">Run: <code>ccc login</code></div>
                <div class="step">Enter your email and password when prompted</div>
            </div>

            <p>You can now use your credentials to authenticate with AWS services via the CLI.</p>

            <p>For help, contact your administrator.</p>

            <p>Best regards,<br><strong>Cloud CLI Access Team</strong></p>
        </div>
    </div>
</body>
</html>
"""

    try:
        print(f"[EMAIL] Attempting to send welcome email to: {user_data['email']}")
        print(f"[EMAIL] FROM address: {FROM_EMAIL}")
        response = ses.send_email(
            Source=FROM_EMAIL,
            Destination={'ToAddresses': [user_data['email']]},
            Message={
                'Subject': {'Data': subject},
                'Body': {
                    'Text': {'Data': text_body},
                    'Html': {'Data': html_body}
                }
            }
        )
        print(f"[+] Welcome email sent successfully. MessageId: {response.get('MessageId')}")
    except Exception as e:
        print(f"[ERROR] Error sending welcome email: {e}")
        print(f"[ERROR] Error details: {type(e).__name__}: {str(e)}")

def send_denial_email(user_data):
    """Send denial notification to user"""

    subject = "Cloud CLI Access Registration Status"

    text_body = f"""
Hello {get_greeting_name(user_data)},

Thank you for your interest in Cloud CLI Access.

Unfortunately, your registration request has not been approved at this time.

If you believe this is an error or would like more information, please contact the administrator.

Best regards,
Cloud CLI Access Team
"""

    html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2>Cloud CLI Access Registration</h2>
        <p>Hello {get_greeting_name(user_data)},</p>
        <p>Thank you for your interest in Cloud CLI Access.</p>
        <p>Unfortunately, your registration request has not been approved at this time.</p>
        <p>If you believe this is an error or would like more information, please contact the administrator.</p>
        <p>Best regards,<br><strong>Cloud CLI Access Team</strong></p>
    </div>
</body>
</html>
"""

    try:
        ses.send_email(
            Source=FROM_EMAIL,
            Destination={'ToAddresses': [user_data['email']]},
            Message={
                'Subject': {'Data': subject},
                'Body': {
                    'Text': {'Data': text_body},
                    'Html': {'Data': html_body}
                }
            }
        )
    except Exception as e:
        print(f"[ERROR] Error sending denial email: {e}")

def error_response(message, status_code):
    """Return error response with CORS headers"""
    return {
        'statusCode': status_code,
        'headers': {
            **CORS_HEADERS,
            'Content-Type': 'application/json'
        },
        'body': json.dumps({'error': message})
    }

def html_response(html, status_code):
    """Return HTML response with CORS headers"""
    return {
        'statusCode': status_code,
        'headers': {
            **CORS_HEADERS,
            'Content-Type': 'text/html'
        },
        'body': html
    }
