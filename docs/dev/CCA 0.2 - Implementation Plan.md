# CCA 0.2 - Complete Implementation Plan

**Document Version:** 1.0
**Last Updated:** 2025-11-07
**Purpose:** Detailed implementation plan for migrating from CCA 0.1 (IAM Identity Center) to CCA 0.2 (Cognito)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Changes Overview](#changes-overview)
3. [Pre-Implementation Checklist](#pre-implementation-checklist)
4. [Phase 1: AWS Resources Setup](#phase-1-aws-resources-setup)
5. [Phase 2: Lambda Function Implementation](#phase-2-lambda-function-implementation)
6. [Phase 3: Registration Form](#phase-3-registration-form)
7. [Phase 4: CCC CLI Tool Update](#phase-4-ccc-cli-tool-update)
8. [Phase 5: Testing & Validation](#phase-5-testing--validation)
9. [Phase 6: CCA 0.1 Cleanup](#phase-6-cca-01-cleanup)
10. [Phase 7: Documentation](#phase-7-documentation)
11. [Rollback Plan](#rollback-plan)
12. [Timeline & Milestones](#timeline--milestones)

---

## Executive Summary

### Objective

Migrate the Cloud CLI Access (CCA) framework from version 0.1 (IAM Identity Center-based) to version 0.2 (Amazon Cognito-based) to address fundamental limitations in password management and user experience.

### Key Changes

| Component | v0.1 | v0.2 |
|-----------|------|------|
| **Authentication Service** | IAM Identity Center | Amazon Cognito User Pool |
| **Password Setup** | "Forgot Password" flow | Set during registration |
| **Email Count** | 2-3 emails | 1 email |
| **Registration Form** | No password field | Password + confirm fields |
| **Lambda Function** | Registration + Approval | Registration + Approval + KMS |
| **CCC CLI** | Device flow | Username/Password auth |
| **Cost** | ~$0.31/month | ~$0.56/month |

### Success Criteria

✅ User can register with password in single form
✅ Admin receives approval email with JWT token
✅ User receives ONE welcome email with credentials
✅ User can login via CCC CLI immediately
✅ All v0.1 AWS resources properly cleaned up
✅ Complete documentation updated
✅ End-to-end test passes successfully

---

## Changes Overview

### Architecture Changes

```
┌─────────────────────────────────────────────────────────────────────┐
│                         What's Changing                              │
└─────────────────────────────────────────────────────────────────────┘

REMOVED from v0.1:
──────────────────
❌ IAM Identity Center integration
❌ Identity Center user management
❌ Identity Center groups (CCA-CLI-Users)
❌ Identity Center permission sets (CCA-CLI-Access)
❌ Device flow authentication
❌ Password setup portal (password-setup.html)

ADDED to v0.2:
──────────────
✅ Amazon Cognito User Pool
✅ Cognito User Pool Client
✅ Cognito User Groups (CCA-CLI-Users)
✅ AWS KMS key for password encryption
✅ Password fields in registration form
✅ Username/Password authentication
✅ IAM role for Cognito federation

MODIFIED:
─────────
🔄 Lambda function (add KMS, update Cognito calls)
🔄 Registration form (add password fields)
🔄 CCC CLI tool (change auth flow)
🔄 Welcome email template
🔄 All documentation

UNCHANGED:
──────────
✅ S3 bucket for registration form
✅ SES email service
✅ Lambda Function URL
✅ Admin approval workflow (JWT-based)
✅ Stateless architecture philosophy
```

### Component Mapping

| v0.1 Component | Status | v0.2 Component |
|----------------|--------|----------------|
| IAM Identity Center | 🔴 REMOVE | Amazon Cognito User Pool |
| Identity Store API | 🔴 REMOVE | Cognito User Pool API |
| SSO Portal | 🔴 REMOVE | N/A (CLI only) |
| Identity Center Groups | 🔴 REMOVE | Cognito Groups |
| Permission Sets | 🔴 REMOVE | IAM Role (AssumeRoleWithWebIdentity) |
| Device Flow Auth | 🔴 REMOVE | USER_PASSWORD_AUTH |
| Lambda Function | 🟡 UPDATE | Lambda Function (+ KMS) |
| S3 Registration Form | 🟡 UPDATE | S3 Registration Form (+ password) |
| SES Email Service | 🟢 KEEP | SES Email Service |
| CCC CLI Tool | 🟡 UPDATE | CCC CLI Tool (new auth) |

---

## Pre-Implementation Checklist

### Requirements Verification

**AWS Account:**
- [ ] AWS CLI configured and working
- [ ] Correct region set (us-east-1)
- [ ] Admin permissions available
- [ ] Account ID confirmed: `211050572089`

**AWS Services:**
- [ ] Cognito available in region
- [ ] KMS available in region
- [ ] Lambda service accessible
- [ ] SES verified identity exists (`info@2112-lab.com`)

**Development Environment:**
- [ ] Python 3.11+ installed
- [ ] pip/pip3 available
- [ ] Git installed and configured
- [ ] Text editor/IDE ready
- [ ] ../CCA-2 directory exists

**Documentation:**
- [ ] Read: CCA 0.2 - Cognito Design.md
- [ ] Read: CCA 0.2 - Password Security Considerations.md
- [ ] Read: Addendum - AWS Resources Inventory.md
- [ ] Understand current v0.1 architecture

**Backup:**
- [ ] v0.1 code backed up
- [ ] v0.1 AWS resource IDs documented
- [ ] Current Lambda function code saved
- [ ] Registration form HTML saved

---

## Phase 1: AWS Resources Setup

### 1.1: Create AWS KMS Key

**Purpose:** Encrypt passwords in JWT tokens

**Steps:**
```bash
# 1. Create KMS key
aws kms create-key \
  --description "CCA 0.2 JWT Password Encryption Key" \
  --key-usage ENCRYPT_DECRYPT \
  --origin AWS_KMS \
  --multi-region false \
  --tags TagKey=Project,TagValue=CCA TagKey=Version,TagValue=0.2 \
  --region us-east-1 \
  --output json > /tmp/kms-key.json

# 2. Get Key ID
export KMS_KEY_ID=$(cat /tmp/kms-key.json | jq -r '.KeyMetadata.KeyId')
echo "KMS Key ID: $KMS_KEY_ID"

# 3. Create alias
aws kms create-alias \
  --alias-name alias/cca-jwt-encryption \
  --target-key-id $KMS_KEY_ID \
  --region us-east-1

# 4. Enable automatic key rotation
aws kms enable-key-rotation \
  --key-id $KMS_KEY_ID \
  --region us-east-1

# 5. Verify
aws kms describe-key \
  --key-id alias/cca-jwt-encryption \
  --region us-east-1

# 6. Save Key ID for later
echo $KMS_KEY_ID > ../CCA-2/tmp/kms-key-id.txt
```

**Verification:**
- [ ] Key created successfully
- [ ] Alias created: `alias/cca-jwt-encryption`
- [ ] Key rotation enabled
- [ ] Key ID saved to file

**Resources Created:**
- KMS Key: `arn:aws:kms:us-east-1:211050572089:key/<KEY_ID>`
- KMS Alias: `alias/cca-jwt-encryption`

---

### 1.2: Create Cognito User Pool

**Purpose:** User authentication and management

**Steps:**
```bash
# 1. Create User Pool
aws cognito-idp create-user-pool \
  --pool-name "CCA-UserPool-v2" \
  --policies '{
    "PasswordPolicy": {
      "MinimumLength": 8,
      "RequireUppercase": true,
      "RequireLowercase": true,
      "RequireNumbers": true,
      "RequireSymbols": true,
      "TemporaryPasswordValidityDays": 7
    }
  }' \
  --auto-verified-attributes email \
  --username-attributes email \
  --schema '[
    {"Name": "email", "Required": true, "Mutable": false},
    {"Name": "given_name", "Required": true, "Mutable": true},
    {"Name": "family_name", "Required": true, "Mutable": true}
  ]' \
  --mfa-configuration OFF \
  --email-configuration EmailSendingAccount=DEVELOPER,SourceArn=arn:aws:ses:us-east-1:211050572089:identity/info@2112-lab.com \
  --admin-create-user-config '{
    "AllowAdminCreateUserOnly": false
  }' \
  --user-pool-tags Project=CCA,Version=0.2 \
  --region us-east-1 \
  --output json > /tmp/user-pool.json

# 2. Get User Pool ID
export USER_POOL_ID=$(cat /tmp/user-pool.json | jq -r '.UserPool.Id')
echo "User Pool ID: $USER_POOL_ID"

# 3. Save for later
echo $USER_POOL_ID > ../CCA-2/tmp/user-pool-id.txt
```

**Verification:**
- [ ] User Pool created
- [ ] Password policy configured correctly
- [ ] Email as username enabled
- [ ] User Pool ID saved

**Resources Created:**
- User Pool: `us-east-1_XXXXXXXXX`

---

### 1.3: Create Cognito User Pool Client

**Purpose:** Application client for CCC CLI

**Steps:**
```bash
# 1. Create App Client
aws cognito-idp create-user-pool-client \
  --user-pool-id $USER_POOL_ID \
  --client-name "CCA-CLI-Client" \
  --generate-secret \
  --explicit-auth-flows USER_PASSWORD_AUTH REFRESH_TOKEN_AUTH ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH \
  --read-attributes email given_name family_name \
  --write-attributes email given_name family_name \
  --prevent-user-existence-errors ENABLED \
  --enable-token-revocation \
  --refresh-token-validity 30 \
  --access-token-validity 1 \
  --id-token-validity 1 \
  --token-validity-units '{
    "RefreshToken": "days",
    "AccessToken": "hours",
    "IdToken": "hours"
  }' \
  --region us-east-1 \
  --output json > /tmp/app-client.json

# 2. Get Client ID and Secret
export CLIENT_ID=$(cat /tmp/app-client.json | jq -r '.UserPoolClient.ClientId')
export CLIENT_SECRET=$(cat /tmp/app-client.json | jq -r '.UserPoolClient.ClientSecret')

echo "Client ID: $CLIENT_ID"
echo "Client Secret: $CLIENT_SECRET"

# 3. Save for later
echo $CLIENT_ID > ../CCA-2/tmp/client-id.txt
echo $CLIENT_SECRET > ../CCA-2/tmp/client-secret.txt
```

**Verification:**
- [ ] App client created
- [ ] USER_PASSWORD_AUTH enabled
- [ ] Client ID and Secret saved
- [ ] Token validity configured

**Resources Created:**
- App Client ID: `<CLIENT_ID>`
- App Client Secret: `<CLIENT_SECRET>`

---

### 1.4: Create Cognito User Group

**Purpose:** Group for CLI users with specific permissions

**Steps:**
```bash
# 1. Create group
aws cognito-idp create-group \
  --user-pool-id $USER_POOL_ID \
  --group-name "CCA-CLI-Users" \
  --description "Cloud CLI Access Users - v0.2" \
  --precedence 1 \
  --region us-east-1

# 2. Verify
aws cognito-idp list-groups \
  --user-pool-id $USER_POOL_ID \
  --region us-east-1
```

**Verification:**
- [ ] Group created successfully
- [ ] Group name: `CCA-CLI-Users`
- [ ] Precedence set to 1

---

### 1.5: Create Cognito Identity Pool

**Purpose:** Federate Cognito users to AWS credentials

**Steps:**
```bash
# 1. Create Identity Pool
aws cognito-identity create-identity-pool \
  --identity-pool-name "CCA-IdentityPool-v2" \
  --allow-unauthenticated-identities false \
  --cognito-identity-providers \
    ProviderName=cognito-idp.us-east-1.amazonaws.com/$USER_POOL_ID,ClientId=$CLIENT_ID \
  --region us-east-1 \
  --output json > /tmp/identity-pool.json

# 2. Get Identity Pool ID
export IDENTITY_POOL_ID=$(cat /tmp/identity-pool.json | jq -r '.IdentityPoolId')
echo "Identity Pool ID: $IDENTITY_POOL_ID"

# 3. Save for later
echo $IDENTITY_POOL_ID > ../CCA-2/tmp/identity-pool-id.txt
```

**Verification:**
- [ ] Identity Pool created
- [ ] Linked to User Pool
- [ ] Unauthenticated access disabled
- [ ] Identity Pool ID saved

**Resources Created:**
- Identity Pool: `us-east-1:XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX`

---

### 1.6: Create IAM Role for Cognito

**Purpose:** IAM role assumed by authenticated Cognito users

**Steps:**
```bash
# 1. Create trust policy
cat > /tmp/cognito-trust-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "cognito-identity.amazonaws.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "cognito-identity.amazonaws.com:aud": "IDENTITY_POOL_ID_PLACEHOLDER"
        },
        "ForAnyValue:StringLike": {
          "cognito-identity.amazonaws.com:amr": "authenticated"
        }
      }
    }
  ]
}
EOF

# Replace placeholder
sed -i "s/IDENTITY_POOL_ID_PLACEHOLDER/$IDENTITY_POOL_ID/g" /tmp/cognito-trust-policy.json

# 2. Create IAM role
aws iam create-role \
  --role-name CCA-Cognito-CLI-Access \
  --assume-role-policy-document file:///tmp/cognito-trust-policy.json \
  --description "CCA 0.2 - CLI Access via Cognito" \
  --tags Key=Project,Value=CCA Key=Version,Value=0.2 \
  --output json > /tmp/iam-role.json

# 3. Get Role ARN
export ROLE_ARN=$(cat /tmp/iam-role.json | jq -r '.Role.Arn')
echo "Role ARN: $ROLE_ARN"

# 4. Create permissions policy
cat > /tmp/cognito-permissions.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowCLIOperations",
      "Effect": "Allow",
      "Action": [
        "s3:ListAllMyBuckets",
        "s3:ListBucket",
        "s3:GetObject",
        "s3:PutObject",
        "ec2:Describe*",
        "lambda:List*",
        "lambda:Get*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "DenyConsoleAccess",
      "Effect": "Deny",
      "Action": [
        "console:*",
        "signin:*",
        "sso:*"
      ],
      "Resource": "*"
    }
  ]
}
EOF

# 5. Attach policy
aws iam put-role-policy \
  --role-name CCA-Cognito-CLI-Access \
  --policy-name CCA-CLI-Permissions \
  --policy-document file:///tmp/cognito-permissions.json

# 6. Save Role ARN
echo $ROLE_ARN > ../CCA-2/tmp/role-arn.txt
```

**Verification:**
- [ ] IAM role created
- [ ] Trust policy configured for Cognito
- [ ] Permissions policy attached
- [ ] Console access denied
- [ ] Role ARN saved

**Resources Created:**
- IAM Role: `arn:aws:iam::211050572089:role/CCA-Cognito-CLI-Access`

---

### 1.7: Link Identity Pool to IAM Role

**Purpose:** Configure Identity Pool to use IAM role

**Steps:**
```bash
# 1. Set Identity Pool roles
aws cognito-identity set-identity-pool-roles \
  --identity-pool-id $IDENTITY_POOL_ID \
  --roles authenticated=$ROLE_ARN \
  --region us-east-1

# 2. Verify
aws cognito-identity get-identity-pool-roles \
  --identity-pool-id $IDENTITY_POOL_ID \
  --region us-east-1
```

**Verification:**
- [ ] Role linked to Identity Pool
- [ ] Authenticated role configured

---

### 1.8: Create Lambda Execution Role

**Purpose:** IAM role for Lambda function to access KMS and Cognito

**Steps:**
```bash
# 1. Create trust policy
cat > /tmp/lambda-trust-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# 2. Create role
aws iam create-role \
  --role-name CCA-Lambda-v2-ExecutionRole \
  --assume-role-policy-document file:///tmp/lambda-trust-policy.json \
  --description "CCA 0.2 - Lambda execution role" \
  --tags Key=Project,Value=CCA Key=Version,Value=0.2

# 3. Create permissions policy
cat > /tmp/lambda-permissions.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CloudWatchLogs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:us-east-1:211050572089:*"
    },
    {
      "Sid": "KMSEncryptDecrypt",
      "Effect": "Allow",
      "Action": [
        "kms:Encrypt",
        "kms:Decrypt",
        "kms:DescribeKey"
      ],
      "Resource": "arn:aws:kms:us-east-1:211050572089:key/*"
    },
    {
      "Sid": "CognitoUserManagement",
      "Effect": "Allow",
      "Action": [
        "cognito-idp:AdminCreateUser",
        "cognito-idp:AdminSetUserPassword",
        "cognito-idp:AdminAddUserToGroup",
        "cognito-idp:AdminGetUser",
        "cognito-idp:ListUsers"
      ],
      "Resource": "arn:aws:cognito-idp:us-east-1:211050572089:userpool/*"
    },
    {
      "Sid": "SESEmailSending",
      "Effect": "Allow",
      "Action": [
        "ses:SendEmail",
        "ses:SendRawEmail"
      ],
      "Resource": "*"
    }
  ]
}
EOF

# 4. Attach policy
aws iam put-role-policy \
  --role-name CCA-Lambda-v2-ExecutionRole \
  --policy-name CCA-Lambda-v2-Permissions \
  --policy-document file:///tmp/lambda-permissions.json

# 5. Get Role ARN
export LAMBDA_ROLE_ARN=$(aws iam get-role --role-name CCA-Lambda-v2-ExecutionRole --query 'Role.Arn' --output text)
echo "Lambda Role ARN: $LAMBDA_ROLE_ARN"

# 6. Save
echo $LAMBDA_ROLE_ARN > ../CCA-2/tmp/lambda-role-arn.txt

# 7. Wait for role propagation (30 seconds)
echo "Waiting for IAM role to propagate..."
sleep 30
```

**Verification:**
- [ ] Lambda role created
- [ ] CloudWatch Logs permissions granted
- [ ] KMS permissions granted
- [ ] Cognito permissions granted
- [ ] SES permissions granted
- [ ] Role ARN saved

**Resources Created:**
- IAM Role: `arn:aws:iam::211050572089:role/CCA-Lambda-v2-ExecutionRole`

---

### Phase 1 Summary

**Resources Created:**
1. ✅ KMS Key: `alias/cca-jwt-encryption`
2. ✅ Cognito User Pool: `CCA-UserPool-v2`
3. ✅ Cognito App Client: `CCA-CLI-Client`
4. ✅ Cognito User Group: `CCA-CLI-Users`
5. ✅ Cognito Identity Pool: `CCA-IdentityPool-v2`
6. ✅ IAM Role: `CCA-Cognito-CLI-Access`
7. ✅ IAM Role: `CCA-Lambda-v2-ExecutionRole`

**Files Saved:**
- `../CCA-2/tmp/kms-key-id.txt`
- `../CCA-2/tmp/user-pool-id.txt`
- `../CCA-2/tmp/client-id.txt`
- `../CCA-2/tmp/client-secret.txt`
- `../CCA-2/tmp/identity-pool-id.txt`
- `../CCA-2/tmp/role-arn.txt`
- `../CCA-2/tmp/lambda-role-arn.txt`

---

## Phase 2: Lambda Function Implementation

### 2.1: Prepare Lambda Code

**Location:** `../CCA-2/lambda/`

**Files to Create:**
1. `lambda_function.py` - Main handler
2. `requirements.txt` - Dependencies
3. `config.py` - Configuration
4. `jwt_utils.py` - JWT helpers
5. `kms_utils.py` - KMS encryption helpers
6. `cognito_utils.py` - Cognito operations
7. `email_utils.py` - Email templates

**Steps:**
```bash
# Navigate to CCA-2
cd ../CCA-2

# Create lambda directory
mkdir -p lambda

# Create files (will implement in next sections)
touch lambda/lambda_function.py
touch lambda/requirements.txt
touch lambda/config.py
touch lambda/jwt_utils.py
touch lambda/kms_utils.py
touch lambda/cognito_utils.py
touch lambda/email_utils.py
```

### 2.2: Create requirements.txt

**File:** `../CCA-2/lambda/requirements.txt`

```
boto3>=1.34.0
python-jose[cryptography]>=3.3.0
```

### 2.3: Implement Lambda Function

(Implementation details will be in the actual execution phase)

### 2.4: Create Deployment Package

**Steps:**
```bash
cd ../CCA-2/lambda

# Create deployment directory
mkdir -p deployment
cd deployment

# Install dependencies
pip3 install -r ../requirements.txt -t .

# Copy Lambda code
cp ../*.py .

# Create ZIP
zip -r cca-v2-lambda.zip .

# Move to lambda directory
mv cca-v2-lambda.zip ..
cd ..
```

### 2.5: Deploy Lambda Function

**Steps:**
```bash
# Read saved values
export USER_POOL_ID=$(cat ../tmp/user-pool-id.txt)
export KMS_KEY_ID=$(cat ../tmp/kms-key-id.txt)
export LAMBDA_ROLE_ARN=$(cat ../tmp/lambda-role-arn.txt)
export SECRET_KEY=$(openssl rand -hex 32)

# Create Lambda function
aws lambda create-function \
  --function-name cca-registration-v2 \
  --runtime python3.11 \
  --role $LAMBDA_ROLE_ARN \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://cca-v2-lambda.zip \
  --timeout 30 \
  --memory-size 512 \
  --environment Variables="{
    USER_POOL_ID=$USER_POOL_ID,
    KMS_KEY_ID=$KMS_KEY_ID,
    FROM_EMAIL=info@2112-lab.com,
    ADMIN_EMAIL=info@2112-lab.com,
    SECRET_KEY=$SECRET_KEY,
    AWS_ACCOUNT_ID=211050572089
  }" \
  --tags Project=CCA,Version=0.2 \
  --region us-east-1 \
  --output json > /tmp/lambda-function.json

# Get Function ARN
export LAMBDA_ARN=$(cat /tmp/lambda-function.json | jq -r '.FunctionArn')
echo "Lambda ARN: $LAMBDA_ARN"

# Save
echo $LAMBDA_ARN > ../tmp/lambda-arn.txt
echo $SECRET_KEY > ../tmp/secret-key.txt
```

### 2.6: Create Lambda Function URL

**Steps:**
```bash
# Create Function URL
aws lambda create-function-url-config \
  --function-name cca-registration-v2 \
  --auth-type NONE \
  --cors '{
    "AllowOrigins": ["*"],
    "AllowMethods": ["POST", "GET"],
    "AllowHeaders": ["*"],
    "MaxAge": 300
  }' \
  --region us-east-1 \
  --output json > /tmp/function-url.json

# Get Function URL
export LAMBDA_URL=$(cat /tmp/function-url.json | jq -r '.FunctionUrl')
echo "Lambda Function URL: $LAMBDA_URL"

# Save
echo $LAMBDA_URL > ../tmp/lambda-url.txt

# Add resource policy to allow public invocation
aws lambda add-permission \
  --function-name cca-registration-v2 \
  --statement-id FunctionURLAllowPublicAccess \
  --action lambda:InvokeFunctionUrl \
  --principal "*" \
  --function-url-auth-type NONE \
  --region us-east-1
```

**Verification:**
- [ ] Lambda function deployed
- [ ] Function URL created
- [ ] CORS configured
- [ ] Public access enabled
- [ ] All IDs saved

---

## Phase 3: Registration Form

### 3.1: Update Registration Form HTML

**Location:** `../CCA-2/src/registration.html`

**Changes:**
1. Add password field
2. Add confirm password field
3. Add password strength indicator
4. Update form validation
5. Update API endpoint to Lambda URL

### 3.2: Deploy to S3

**Steps:**
```bash
# Get Lambda URL
export LAMBDA_URL=$(cat ../tmp/lambda-url.txt)

# Update API_URL in registration.html
sed -i "s|YOUR_LAMBDA_FUNCTION_URL|$LAMBDA_URL|g" ../src/registration.html

# Create S3 bucket (or reuse existing)
export BUCKET_NAME=cca-registration-v2-$(date +%s)
aws s3 mb s3://$BUCKET_NAME --region us-east-1

# Enable website hosting
aws s3 website s3://$BUCKET_NAME --index-document registration.html

# Make public
aws s3api put-public-access-block \
  --bucket $BUCKET_NAME \
  --public-access-block-configuration \
    "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"

# Bucket policy
cat > /tmp/bucket-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "PublicReadGetObject",
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::${BUCKET_NAME}/*"
  }]
}
EOF

aws s3api put-bucket-policy \
  --bucket $BUCKET_NAME \
  --policy file:///tmp/bucket-policy.json

# Upload registration form
aws s3 cp ../src/registration.html s3://$BUCKET_NAME/ --content-type text/html

# Get URL
export REGISTRATION_URL="http://${BUCKET_NAME}.s3-website-us-east-1.amazonaws.com/registration.html"
echo "Registration Form URL: $REGISTRATION_URL"

# Save
echo $REGISTRATION_URL > ../tmp/registration-url.txt
echo $BUCKET_NAME > ../tmp/bucket-name.txt
```

**Verification:**
- [ ] S3 bucket created (or reused)
- [ ] Website hosting enabled
- [ ] Public access configured
- [ ] Registration form uploaded
- [ ] URL accessible in browser

---

## Phase 4: CCC CLI Tool Update

### 4.1: Implement New Authentication

**Location:** `../CCA-2/ccc-cli/`

**Files:**
1. `ccc.py` - Main CLI tool
2. `auth.py` - Authentication module
3. `config.py` - Configuration
4. `credentials.py` - Credential management
5. `setup.py` - Installation script

### 4.2: Update Authentication Flow

**Changes:**
- Remove device flow authentication
- Add username/password authentication
- Add Cognito token exchange
- Add AWS credentials caching
- Update credential refresh logic

### 4.3: Test CLI Locally

**Steps:**
```bash
cd ../CCA-2/ccc-cli

# Install in development mode
pip3 install -e .

# Configure
ccc configure \
  --user-pool-id $(cat ../tmp/user-pool-id.txt) \
  --client-id $(cat ../tmp/client-id.txt) \
  --region us-east-1

# Test (will fail until user created)
ccc login
```

---

## Phase 5: Testing & Validation

### 5.1: Unit Tests

**Test Lambda Functions:**
```bash
# Test JWT creation/validation
# Test KMS encryption/decryption
# Test Cognito user creation
# Test email sending
```

### 5.2: Integration Tests

**Test Components:**
1. Registration form → Lambda
2. Lambda → KMS encryption
3. Lambda → Admin email
4. Admin approval → Lambda
5. Lambda → Cognito user creation
6. Lambda → User welcome email

### 5.3: End-to-End Test

**Complete User Journey:**

```bash
# Test Plan:

## Step 1: User Registration
# Action: Open registration form
open $(cat ../tmp/registration-url.txt)

# Action: Fill form
# - Username: testuser
# - Email: andre@2112-lab.com (verified in SES)
# - First Name: Test
# - Last Name: User
# - Password: SecureTest123!
# - Confirm Password: SecureTest123!

# Action: Submit form

# Expected:
# ✅ Success message displayed
# ✅ Admin email received

## Step 2: Admin Approval
# Action: Check admin email (info@2112-lab.com)
# Expected:
# ✅ Email received with approval link

# Action: Click "Approve" button

# Expected:
# ✅ Success page displayed
# ✅ User created in Cognito
# ✅ User added to CCA-CLI-Users group

## Step 3: User Receives Welcome Email
# Action: Check user email (andre@2112-lab.com)
# Expected:
# ✅ Welcome email received
# ✅ Contains username
# ✅ Mentions user-chosen password

## Step 4: User Login via CCC CLI
# Action: Configure CCC CLI
ccc configure \
  --user-pool-id $(cat ../tmp/user-pool-id.txt) \
  --client-id $(cat ../tmp/client-id.txt) \
  --region us-east-1

# Action: Login
ccc login
# Enter username: testuser
# Enter password: SecureTest123!

# Expected:
# ✅ Authentication successful
# ✅ AWS credentials obtained
# ✅ Credentials cached locally

## Step 5: Test AWS Access
# Action: Test S3 access
ccc test
aws s3 ls

# Expected:
# ✅ S3 buckets listed
# ✅ CLI commands work
# ✅ Console access denied (if attempted)

## Step 6: Test Credential Refresh
# Action: Wait for token expiration or force refresh
ccc refresh

# Expected:
# ✅ New credentials obtained
# ✅ AWS access still works

## Step 7: Test Logout
# Action: Logout
ccc logout

# Expected:
# ✅ Credentials cleared
# ✅ AWS access no longer works
```

### 5.4: Security Tests

**Tests:**
1. Password encryption in JWT
2. JWT signature validation
3. JWT expiration handling
4. Token replay prevention (idempotency)
5. KMS encryption/decryption
6. TLS/HTTPS enforcement
7. Console access denial

### 5.5: Error Handling Tests

**Test Cases:**
1. Invalid password (weak)
2. Duplicate username
3. Expired JWT token
4. Invalid JWT signature
5. Non-existent user login
6. Wrong password login
7. Network failures

---

## Phase 6: CCA 0.1 Cleanup

### 6.1: Document Current v0.1 Resources

**Reference:** `Addendum - AWS Resources Inventory.md`

**v0.1 Resources to Remove:**

```
IAM Identity Center Resources:
───────────────────────────────
1. Identity Store: d-9066117351
2. User Group: CCA-CLI-Users (f4a854b8-7001-7012-d86c-5fef774ad505)
3. Permission Set: CCA-CLI-Access
4. Account Assignment: (211050572089 + CCA-CLI-Access + CCA-CLI-Users)
5. Users: (all created users)

Lambda Function:
────────────────
6. Function: cca-registration
7. Function URL: https://kmfuod67kbaeombcknzrjbtrmi0qqncd.lambda-url.us-east-1.on.aws
8. Execution Role: CCA-Lambda-Role (or similar)

S3 Resources:
─────────────
9. Bucket: cca-registration-1762463059
10. Objects: registration.html, password-setup.html

SES Resources:
──────────────
11. Verified Identity: info@2112-lab.com (KEEP - reuse in v0.2)

Old CCC CLI:
────────────
12. ccc-cli tool (v0.1 code)
```

### 6.2: Backup Before Cleanup

**Steps:**
```bash
# Create backup directory
mkdir -p ~/CCA/backup-v0.1

# Backup Lambda function
aws lambda get-function \
  --function-name cca-registration \
  --region us-east-1 \
  --query 'Code.Location' \
  --output text | xargs wget -O ~/CCA/backup-v0.1/cca-registration-v0.1.zip

# Backup S3 content
aws s3 sync s3://cca-registration-1762463059 ~/CCA/backup-v0.1/s3-backup/

# Document all resource IDs
aws identitystore list-users \
  --identity-store-id d-9066117351 \
  --region us-east-1 > ~/CCA/backup-v0.1/identity-center-users.json

aws sso-admin list-permission-sets \
  --instance-arn arn:aws:sso:::instance/ssoins-72232e1b5b84475a \
  --region us-east-1 > ~/CCA/backup-v0.1/permission-sets.json
```

### 6.3: Cleanup Sequence

**IMPORTANT:** Only perform cleanup AFTER v0.2 is fully tested and working!

**Steps:**

```bash
# 1. Delete Identity Center Users
echo "Deleting Identity Center users..."
aws identitystore list-users \
  --identity-store-id d-9066117351 \
  --region us-east-1 \
  --query 'Users[*].UserId' \
  --output text | while read user_id; do
    echo "Deleting user: $user_id"
    aws identitystore delete-user \
      --identity-store-id d-9066117351 \
      --user-id $user_id \
      --region us-east-1
done

# 2. Delete Account Assignments
echo "Removing account assignments..."
# (Manual via console or complex CLI commands)
# Navigate to: IAM Identity Center → AWS Accounts → Permission sets
# Remove all assignments

# 3. Delete Permission Set
echo "Deleting permission set..."
# Get permission set ARN
PERMISSION_SET_ARN=$(aws sso-admin list-permission-sets \
  --instance-arn arn:aws:sso:::instance/ssoins-72232e1b5b84475a \
  --region us-east-1 \
  --query 'PermissionSets[0]' \
  --output text)

# Delete permission set
aws sso-admin delete-permission-set \
  --instance-arn arn:aws:sso:::instance/ssoins-72232e1b5b84475a \
  --permission-set-arn $PERMISSION_SET_ARN \
  --region us-east-1

# 4. Delete Identity Center Group
# (Cannot delete via CLI - must use console)
# Navigate to: IAM Identity Center → Groups
# Delete: CCA-CLI-Users

# 5. Delete Lambda Function
echo "Deleting v0.1 Lambda function..."
aws lambda delete-function \
  --function-name cca-registration \
  --region us-east-1

# 6. Delete Lambda Execution Role
echo "Deleting Lambda execution role..."
# Get role name
LAMBDA_ROLE=$(aws lambda get-function \
  --function-name cca-registration \
  --region us-east-1 \
  --query 'Configuration.Role' \
  --output text 2>/dev/null | awk -F'/' '{print $NF}')

# Delete inline policies
aws iam list-role-policies \
  --role-name $LAMBDA_ROLE \
  --query 'PolicyNames[*]' \
  --output text | while read policy; do
    aws iam delete-role-policy \
      --role-name $LAMBDA_ROLE \
      --policy-name $policy
done

# Detach managed policies
aws iam list-attached-role-policies \
  --role-name $LAMBDA_ROLE \
  --query 'AttachedPolicies[*].PolicyArn' \
  --output text | while read policy_arn; do
    aws iam detach-role-policy \
      --role-name $LAMBDA_ROLE \
      --policy-arn $policy_arn
done

# Delete role
aws iam delete-role --role-name $LAMBDA_ROLE

# 7. Empty and Delete S3 Bucket
echo "Deleting S3 bucket..."
aws s3 rm s3://cca-registration-1762463059 --recursive
aws s3 rb s3://cca-registration-1762463059

# 8. Remove old CCC CLI
echo "Cleaning up old CCC CLI..."
pip3 uninstall ccc-cli -y
rm -rf ~/CCA/ccc-cli-v0.1

# 9. Keep SES verified identity (reused in v0.2)
echo "Keeping SES identity: info@2112-lab.com"
```

### 6.4: Verification After Cleanup

**Checklist:**
- [ ] No Identity Center users remain
- [ ] Permission sets deleted
- [ ] Lambda function deleted
- [ ] S3 bucket deleted
- [ ] Old CLI uninstalled
- [ ] SES identity retained
- [ ] Backup files saved
- [ ] v0.2 still works

---

## Phase 7: Documentation

### 7.1: Documents to Create/Update

**New Documents (in CCA-2/docs/):**
1. ✅ CCA 0.2 - Cognito Design.md (already created)
2. ✅ CCA 0.2 - Password Security Considerations.md (already created)
3. ✅ CCA 0.2 - Implementation Plan.md (this document)
4. 🔄 CCA 0.2 - Deployment Summary.md (update from v0.1)
5. 🔄 CCA 0.2 - Implementation Guide.md (update from v0.1)
6. 🔄 CCA 0.2 - Summary.md (update from v0.1)
7. 🔄 Addendum - AWS Resources Inventory v0.2.md
8. 🔄 Addendum - User Management Guide v0.2.md
9. 🔄 Addendum - REST API Authentication v0.2.md
10. 🔄 Addendum - Files Manifest v0.2.md
11. 🆕 CCA 0.2 - Migration Guide (v0.1 to v0.2).md
12. 🆕 CCA 0.2 - Implementation Changes Log.md

### 7.2: Update Existing Documentation

**From ~/CCA/docs to ../CCA-2/docs:**

Documents requiring updates:
- CCA - Implementation Guide.md → Update for Cognito
- CCA - Deployment Summary.md → Update resource list
- CCA - Summary.md → Update architecture
- Addendum - AWS Resources Inventory.md → New resources
- Addendum - User Management Guide.md → Cognito commands
- Addendum - REST API Authentication.md → Cognito auth
- Addendum - Files Manifest.md → New file structure

Documents to keep as-is:
- Addendum - Github Actions Integration.md (still relevant)
- Addendum - Custom Domain Setup.md (still relevant)
- Addendum - Python Lambda Web App.md (still relevant)
- Addendum - Console Navigation Guide.md (no longer needed for v0.2)
- Addendum - Email and Password Setup Issues.md (resolved in v0.2)

---

## Rollback Plan

### When to Rollback

Rollback if:
- End-to-end test fails completely
- Critical security issue discovered
- AWS resources cannot be created
- Costs exceed expectations significantly
- User experience worse than v0.1

### Rollback Steps

```bash
# 1. Keep v0.2 resources (for analysis)
# Do not delete Cognito, KMS, etc.

# 2. Restore v0.1 Lambda function
aws lambda create-function \
  --function-name cca-registration \
  --runtime python3.11 \
  --role <OLD_ROLE_ARN> \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://~/CCA/backup-v0.1/cca-registration-v0.1.zip \
  --region us-east-1

# 3. Restore S3 bucket
aws s3 mb s3://cca-registration-1762463059
aws s3 sync ~/CCA/backup-v0.1/s3-backup/ s3://cca-registration-1762463059/

# 4. Restore Identity Center users
# (Manual recreation via console)

# 5. Re-install v0.1 CCC CLI
cd ~/CCA/ccc-cli-v0.1
pip3 install -e .

# 6. Document rollback reason
# Create incident report

# 7. Plan v0.2 fixes
```

---

## Timeline & Milestones

### Estimated Timeline

**Total Duration:** 2-3 days

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1: AWS Resources | 2-3 hours | None |
| Phase 2: Lambda Function | 3-4 hours | Phase 1 |
| Phase 3: Registration Form | 1-2 hours | Phase 2 |
| Phase 4: CCC CLI Tool | 2-3 hours | Phase 1, 2 |
| Phase 5: Testing | 4-6 hours | Phase 2, 3, 4 |
| Phase 6: v0.1 Cleanup | 1-2 hours | Phase 5 (success) |
| Phase 7: Documentation | 3-4 hours | All phases |

### Milestones

**Milestone 1:** AWS Infrastructure Ready
- ✅ All AWS resources created
- ✅ IAM roles configured
- ✅ Resource IDs saved

**Milestone 2:** Lambda Deployed
- ✅ Lambda function code complete
- ✅ Lambda deployed and accessible
- ✅ Function URL working

**Milestone 3:** Forms Ready
- ✅ Registration form updated
- ✅ Form deployed to S3
- ✅ Form accessible in browser

**Milestone 4:** CLI Tool Updated
- ✅ CCC CLI code updated
- ✅ Authentication flow working
- ✅ Credentials cached properly

**Milestone 5:** End-to-End Success
- ✅ User can register with password
- ✅ Admin can approve
- ✅ User receives one email
- ✅ User can login via CLI
- ✅ AWS access works

**Milestone 6:** Cleanup Complete
- ✅ v0.1 resources removed
- ✅ Backups saved
- ✅ v0.2 verified still working

**Milestone 7:** Documentation Complete
- ✅ All documents updated
- ✅ Migration guide written
- ✅ Changes logged

---

## Success Metrics

### Functional Requirements

- [ ] User registration includes password field
- [ ] Password encrypted with KMS in JWT
- [ ] Admin approval works via email link
- [ ] Cognito user created with password
- [ ] User receives single welcome email
- [ ] User can login via CCC CLI
- [ ] AWS credentials obtained successfully
- [ ] CLI commands work (s3 ls, etc.)
- [ ] Console access denied
- [ ] Credentials cached and refreshed

### Non-Functional Requirements

- [ ] Password plaintext exists < 200ms
- [ ] End-to-end flow < 5 minutes
- [ ] No passwords in logs
- [ ] TLS 1.2+ everywhere
- [ ] Cost ~$0.56/month
- [ ] All tests pass
- [ ] Documentation complete

### Security Requirements

- [ ] KMS encryption working
- [ ] JWT signature validated
- [ ] Token expiration enforced
- [ ] Idempotency working
- [ ] No plaintext storage
- [ ] Console access blocked
- [ ] Least privilege IAM policies

---

## Appendix

### A. Resource Naming Convention

```
CCA 0.2 Resources:
──────────────────
Cognito User Pool:     CCA-UserPool-v2
Cognito App Client:    CCA-CLI-Client
Cognito Group:         CCA-CLI-Users
Cognito Identity Pool: CCA-IdentityPool-v2
IAM Role (CLI):        CCA-Cognito-CLI-Access
IAM Role (Lambda):     CCA-Lambda-v2-ExecutionRole
Lambda Function:       cca-registration-v2
KMS Key Alias:         alias/cca-jwt-encryption
S3 Bucket:             cca-registration-v2-<timestamp>
```

### B. Environment Variables

**Lambda Function:**
```
USER_POOL_ID=<from Cognito>
KMS_KEY_ID=<from KMS>
FROM_EMAIL=info@2112-lab.com
ADMIN_EMAIL=info@2112-lab.com
SECRET_KEY=<random 64-char hex>
AWS_ACCOUNT_ID=211050572089
```

**CCC CLI Config:**
```
~/.ccc/config.json:
{
  "user_pool_id": "<USER_POOL_ID>",
  "client_id": "<CLIENT_ID>",
  "client_secret": "<CLIENT_SECRET>",
  "identity_pool_id": "<IDENTITY_POOL_ID>",
  "region": "us-east-1"
}
```

### C. Troubleshooting Guide

**Common Issues:**

1. **Lambda can't decrypt KMS:**
   - Check Lambda execution role has kms:Decrypt
   - Verify KMS key ID correct

2. **Cognito user creation fails:**
   - Check Lambda has cognito-idp:AdminCreateUser
   - Verify User Pool ID correct

3. **CCC CLI auth fails:**
   - Check USER_PASSWORD_AUTH enabled
   - Verify client ID and secret
   - Check username/password correct

4. **AWS credentials not working:**
   - Check Identity Pool linked to User Pool
   - Verify IAM role trust policy
   - Check role has required permissions

5. **Registration form not submitting:**
   - Check Lambda URL in form code
   - Verify CORS configured
   - Check browser console for errors

---

**Document Status:** Complete Implementation Plan
**Ready for Execution:** Yes
**Next Step:** Begin Phase 1 - AWS Resources Setup

---

**End of Document**
