# AWS Resources Inventory - CCA 0.2

**Version:** 0.2 (Cognito-based)
**Last Updated:** 2025-11-09
**Status:** ✅ Active

---

## Overview

This document provides a complete inventory of all AWS resources deployed for Cloud CLI Access (CCA) version 0.2. Use this for:
- Resource auditing
- Cost tracking
- Cleanup/teardown procedures
- Troubleshooting

---

## Resource Summary

| Service | Resource Count | Monthly Cost (Est.) |
|---------|----------------|---------------------|
| **KMS** | 1 key | $1.00 |
| **Cognito User Pools** | 1 pool | Free tier (50k MAUs) |
| **Cognito Identity Pools** | 1 pool | Free |
| **IAM Roles** | 2 roles | Free |
| **Lambda** | 1 function | Free tier (1M requests) |
| **S3** | 1 bucket | $0.023/GB |
| **SES** | Email sending | $0.10/1000 emails |
| **CloudWatch Logs** | Lambda logs | $0.50/GB ingested |
| **Total** | | **~$2-3/month** |

---

## 1. KMS (Key Management Service)

### KMS Key for Password Encryption

**Purpose:** Encrypts user passwords in JWT tokens during admin approval flow

| Property | Value |
|----------|-------|
| **Key ID** | `3ec987ec-fbaf-4de9-bd39-9e1615976e08` |
| **ARN** | `arn:aws:kms:us-east-1:211050572089:key/3ec987ec-fbaf-4de9-bd39-9e1615976e08` |
| **Alias** | `alias/cca-jwt-encryption` |
| **Key Usage** | ENCRYPT_DECRYPT |
| **Key Spec** | SYMMETRIC_DEFAULT |
| **Origin** | AWS_KMS |
| **Key State** | Enabled |
| **Rotation** | ✅ Enabled (automatic annual rotation) |
| **Region** | us-east-1 |
| **Tags** | Project=CCA, Version=0.2 |

**CLI Commands:**
```bash
# Describe key
aws kms describe-key --key-id alias/cca-jwt-encryption --region us-east-1

# Check rotation status
aws kms get-key-rotation-status --key-id 3ec987ec-fbaf-4de9-bd39-9e1615976e08 --region us-east-1

# Encrypt test
aws kms encrypt --key-id alias/cca-jwt-encryption --plaintext "test" --region us-east-1

# Disable key (for cleanup)
aws kms disable-key --key-id 3ec987ec-fbaf-4de9-bd39-9e1615976e08 --region us-east-1
```

---

## 2. Cognito User Pools

### CCA User Pool

**Purpose:** User directory and authentication service for CCA users

| Property | Value |
|----------|-------|
| **Pool ID** | `us-east-1_rYTZnMwvc` |
| **Pool Name** | `CCA-UserPool-v2` |
| **ARN** | `arn:aws:cognito-idp:us-east-1:211050572089:userpool/us-east-1_rYTZnMwvc` |
| **Region** | us-east-1 |
| **Status** | ACTIVE |
| **Username Attributes** | email |
| **Auto-Verified Attributes** | email |
| **MFA Configuration** | OFF |
| **Email Sending** | COGNITO_DEFAULT |
| **Deletion Protection** | INACTIVE |
| **Tags** | Project=CCA, Version=0.2 |

**Password Policy:**
- Minimum length: 8 characters
- Requires: uppercase, lowercase, numbers, symbols
- Temporary password validity: 7 days

**CLI Commands:**
```bash
# Describe user pool
aws cognito-idp describe-user-pool --user-pool-id us-east-1_rYTZnMwvc --region us-east-1

# List users
aws cognito-idp list-users --user-pool-id us-east-1_rYTZnMwvc --region us-east-1

# Get user
aws cognito-idp admin-get-user --user-pool-id us-east-1_rYTZnMwvc --username user@example.com --region us-east-1

# Delete user pool (for cleanup)
aws cognito-idp delete-user-pool --user-pool-id us-east-1_rYTZnMwvc --region us-east-1
```

### App Client

**Purpose:** CLI authentication client for CCA

| Property | Value |
|----------|-------|
| **Client ID** | `1bga7o1j5vthc9gmfq7eeba3ti` |
| **Client Name** | `CCA-CLI-Client` |
| **User Pool ID** | `us-east-1_rYTZnMwvc` |
| **Client Secret** | None (public client) |
| **Auth Flows** | ALLOW_USER_PASSWORD_AUTH, ALLOW_REFRESH_TOKEN_AUTH |
| **Access Token Validity** | 12 hours |
| **ID Token Validity** | 12 hours |
| **Refresh Token Validity** | 30 days |
| **Token Revocation** | Enabled |
| **Prevent User Existence Errors** | Enabled |

**CLI Commands:**
```bash
# Describe app client
aws cognito-idp describe-user-pool-client \
  --user-pool-id us-east-1_rYTZnMwvc \
  --client-id 1bga7o1j5vthc9gmfq7eeba3ti \
  --region us-east-1

# Test authentication (replace with actual credentials)
aws cognito-idp initiate-auth \
  --client-id 1bga7o1j5vthc9gmfq7eeba3ti \
  --auth-flow USER_PASSWORD_AUTH \
  --auth-parameters USERNAME=user@example.com,PASSWORD=password \
  --region us-east-1
```

---

## 3. Cognito Identity Pools

### CCA Identity Pool

**Purpose:** Federate Cognito users to AWS IAM roles for CLI access

| Property | Value |
|----------|-------|
| **Identity Pool ID** | `us-east-1:0a656e9c-d356-4964-b6ba-610afb34cbb7` |
| **Identity Pool Name** | `CCA-IdentityPool-v2` |
| **Region** | us-east-1 |
| **Allow Unauthenticated** | false |
| **Identity Providers** | Cognito User Pool (us-east-1_rYTZnMwvc) |
| **Server-Side Token Check** | Enabled |

**Identity Provider Configuration:**
- **Provider Name:** `cognito-idp.us-east-1.amazonaws.com/us-east-1_rYTZnMwvc`
- **Client ID:** `1bga7o1j5vthc9gmfq7eeba3ti`
- **Server-Side Token Check:** true

**Role Mappings:**
- **Authenticated Role:** `arn:aws:iam::211050572089:role/CCA-Cognito-Auth-Role`

**CLI Commands:**
```bash
# Describe identity pool
aws cognito-identity describe-identity-pool \
  --identity-pool-id us-east-1:0a656e9c-d356-4964-b6ba-610afb34cbb7 \
  --region us-east-1

# Get identity pool roles
aws cognito-identity get-identity-pool-roles \
  --identity-pool-id us-east-1:0a656e9c-d356-4964-b6ba-610afb34cbb7 \
  --region us-east-1

# Delete identity pool (for cleanup)
aws cognito-identity delete-identity-pool \
  --identity-pool-id us-east-1:0a656e9c-d356-4964-b6ba-610afb34cbb7 \
  --region us-east-1
```

---

## 4. IAM Roles

### Role 1: CCA-Cognito-Auth-Role

**Purpose:** IAM role assumed by authenticated Cognito users for CLI access

| Property | Value |
|----------|-------|
| **Role Name** | `CCA-Cognito-Auth-Role` |
| **Role ARN** | `arn:aws:iam::211050572089:role/CCA-Cognito-Auth-Role` |
| **Max Session Duration** | 43200 seconds (12 hours) |
| **Path** | `/` |
| **Creation Date** | 2025-11-09 |
| **Tags** | Project=CCA, Version=0.2 |

**Trust Policy:**
```json
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
          "cognito-identity.amazonaws.com:aud": "us-east-1:0a656e9c-d356-4964-b6ba-610afb34cbb7"
        },
        "ForAnyValue:StringLike": {
          "cognito-identity.amazonaws.com:amr": "authenticated"
        }
      }
    }
  ]
}
```

**Inline Policy: CCA-CLI-Access-Policy**
- **Deny:** Console access (via signin.amazonaws.com)
- **Allow:** S3 (all actions), EC2 Describe/Get, Lambda List/Get, CloudWatch Logs, IAM read-only, STS GetCallerIdentity

**CLI Commands:**
```bash
# Get role
aws iam get-role --role-name CCA-Cognito-Auth-Role

# Get role policy
aws iam get-role-policy \
  --role-name CCA-Cognito-Auth-Role \
  --policy-name CCA-CLI-Access-Policy

# Delete role (for cleanup - delete policies first)
aws iam delete-role-policy \
  --role-name CCA-Cognito-Auth-Role \
  --policy-name CCA-CLI-Access-Policy
aws iam delete-role --role-name CCA-Cognito-Auth-Role
```

### Role 2: CCA-Lambda-Execution-Role-v2

**Purpose:** Lambda execution role for registration/approval function

| Property | Value |
|----------|-------|
| **Role Name** | `CCA-Lambda-Execution-Role-v2` |
| **Role ARN** | `arn:aws:iam::211050572089:role/CCA-Lambda-Execution-Role-v2` |
| **Path** | `/` |
| **Creation Date** | 2025-11-09 |
| **Tags** | Project=CCA, Version=0.2 |

**Trust Policy:**
```json
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
```

**Inline Policy: CCA-Lambda-Execution-Policy**
- **CloudWatch Logs:** CreateLogGroup, CreateLogStream, PutLogEvents
- **SES:** SendEmail, SendRawEmail
- **Cognito:** AdminCreateUser, AdminSetUserPassword, AdminGetUser, ListUsers
- **KMS:** Encrypt, Decrypt, DescribeKey (on CCA key only)

**CLI Commands:**
```bash
# Get role
aws iam get-role --role-name CCA-Lambda-Execution-Role-v2

# Get role policy
aws iam get-role-policy \
  --role-name CCA-Lambda-Execution-Role-v2 \
  --policy-name CCA-Lambda-Execution-Policy

# Delete role (for cleanup - delete policies first)
aws iam delete-role-policy \
  --role-name CCA-Lambda-Execution-Role-v2 \
  --policy-name CCA-Lambda-Execution-Policy
aws iam delete-role --role-name CCA-Lambda-Execution-Role-v2
```

---

## 5. Lambda Functions

### CCA Registration Function v2

**Purpose:** Handle user registration, admin approval, and Cognito user creation

| Property | Value |
|----------|-------|
| **Function Name** | `cca-registration-v2` |
| **Function ARN** | `arn:aws:lambda:us-east-1:211050572089:function:cca-registration-v2` |
| **Runtime** | Python 3.12 |
| **Handler** | `lambda_function.lambda_handler` |
| **Memory** | 256 MB |
| **Timeout** | 30 seconds |
| **Execution Role** | `CCA-Lambda-Execution-Role-v2` |
| **Code Size** | 5,617 bytes |
| **Region** | us-east-1 |
| **Tags** | Project=CCA, Version=0.2 |

**Function URL:**
- **URL:** `https://pli7xymprlva76biu3h6dyso4m0vpqqw.lambda-url.us-east-1.on.aws/`
- **Auth Type:** NONE (public access)
- **CORS:** AllowOrigins=*, AllowMethods=*, AllowHeaders=*

**Environment Variables:**
- `USER_POOL_ID`: `us-east-1_rYTZnMwvc`
- `KMS_KEY_ID`: `3ec987ec-fbaf-4de9-bd39-9e1615976e08`
- `FROM_EMAIL`: `info@2112-lab.com`
- `ADMIN_EMAIL`: `info@2112-lab.com`
- `SECRET_KEY`: `5ab89f169f34cf50e27330b46ff69065b734cace7646a5241f93b9d25e776627`

**Endpoints:**
- `/register` - POST - User registration with password
- `/approve` - GET - Admin approval (creates Cognito user)
- `/deny` - GET - Admin denial

**CLI Commands:**
```bash
# Get function
aws lambda get-function --function-name cca-registration-v2 --region us-east-1

# Invoke function (test)
aws lambda invoke \
  --function-name cca-registration-v2 \
  --payload '{"rawPath":"/register","body":"{}"}' \
  --region us-east-1 \
  /tmp/response.json

# Get function URL
aws lambda get-function-url-config \
  --function-name cca-registration-v2 \
  --region us-east-1

# View logs
aws logs tail /aws/lambda/cca-registration-v2 --region us-east-1 --follow

# Delete function (for cleanup)
aws lambda delete-function-url-config --function-name cca-registration-v2 --region us-east-1
aws lambda delete-function --function-name cca-registration-v2 --region us-east-1
```

---

## 6. S3 Buckets

### Registration Form Bucket

**Purpose:** Host static registration form with password field

| Property | Value |
|----------|-------|
| **Bucket Name** | `cca-registration-v2-2025` |
| **Region** | us-east-1 |
| **Versioning** | Disabled |
| **Encryption** | AES256 (default) |
| **Public Access** | Enabled (for static website) |
| **Static Website Hosting** | Enabled |
| **Index Document** | `registration.html` |
| **Website URL** | `http://cca-registration-v2-2025.s3-website-us-east-1.amazonaws.com/registration.html` |

**Objects:**
- `registration.html` (11.3 KB)

**Bucket Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::cca-registration-v2-2025/*"
    }
  ]
}
```

**CLI Commands:**
```bash
# List objects
aws s3 ls s3://cca-registration-v2-2025/ --region us-east-1

# Get bucket policy
aws s3api get-bucket-policy --bucket cca-registration-v2-2025 --region us-east-1

# Get website configuration
aws s3api get-bucket-website --bucket cca-registration-v2-2025 --region us-east-1

# Delete bucket (for cleanup)
aws s3 rb s3://cca-registration-v2-2025 --force --region us-east-1
```

---

## 7. SES (Simple Email Service)

### Email Identity

**Purpose:** Send registration and approval emails

| Property | Value |
|----------|-------|
| **Identity** | `info@2112-lab.com` |
| **Type** | Email Address |
| **Status** | Verified ✅ |
| **Region** | us-east-1 |
| **Sandbox Mode** | ⚠️ ENABLED (can only send to verified addresses) |

**Sending Statistics:**
- **Max 24 Hour Send:** 200 emails
- **Max Send Rate:** 1 email/second
- **Sent Last 24 Hours:** (varies)

**CLI Commands:**
```bash
# Get identity verification status
aws ses get-identity-verification-attributes \
  --identities info@2112-lab.com \
  --region us-east-1

# Get send statistics
aws ses get-send-statistics --region us-east-1

# Get send quota
aws ses get-send-quota --region us-east-1

# Request production access (to send to any email)
aws sesv2 put-account-details \
  --production-access-enabled \
  --mail-type TRANSACTIONAL \
  --website-url "https://your-company.com" \
  --use-case-description "CCA user registration emails" \
  --region us-east-1
```

---

## 8. CloudWatch Logs

### Lambda Log Group

**Purpose:** Store Lambda function execution logs

| Property | Value |
|----------|-------|
| **Log Group** | `/aws/lambda/cca-registration-v2` |
| **Region** | us-east-1 |
| **Retention** | Never expire (default) |
| **Stored Bytes** | (varies) |

**CLI Commands:**
```bash
# Tail logs in real-time
aws logs tail /aws/lambda/cca-registration-v2 --region us-east-1 --follow

# Search logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/cca-registration-v2 \
  --filter-pattern "ERROR" \
  --region us-east-1

# Set retention
aws logs put-retention-policy \
  --log-group-name /aws/lambda/cca-registration-v2 \
  --retention-in-days 30 \
  --region us-east-1

# Delete log group (for cleanup)
aws logs delete-log-group \
  --log-group-name /aws/lambda/cca-registration-v2 \
  --region us-east-1
```

---

## Complete Cleanup Script

To completely remove all CCA 0.2 resources:

```bash
#!/bin/bash
# CCA 0.2 Complete Cleanup Script

set -e

echo "=== CCA 0.2 Cleanup Script ==="
echo ""
echo "⚠️  WARNING: This will delete ALL CCA 0.2 resources!"
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

# 1. Delete Lambda Function
echo "[1/9] Deleting Lambda function..."
aws lambda delete-function-url-config --function-name cca-registration-v2 --region us-east-1 2>/dev/null || true
aws lambda delete-function --function-name cca-registration-v2 --region us-east-1

# 2. Delete S3 Bucket
echo "[2/9] Deleting S3 bucket..."
aws s3 rb s3://cca-registration-v2-2025 --force --region us-east-1

# 3. Delete CloudWatch Log Group
echo "[3/9] Deleting CloudWatch log group..."
aws logs delete-log-group --log-group-name /aws/lambda/cca-registration-v2 --region us-east-1 2>/dev/null || true

# 4. Delete Cognito Identity Pool
echo "[4/9] Deleting Cognito Identity Pool..."
aws cognito-identity delete-identity-pool --identity-pool-id us-east-1:0a656e9c-d356-4964-b6ba-610afb34cbb7 --region us-east-1

# 5. Delete Cognito User Pool
echo "[5/9] Deleting Cognito User Pool..."
aws cognito-idp delete-user-pool --user-pool-id us-east-1_rYTZnMwvc --region us-east-1

# 6. Delete IAM Role: CCA-Cognito-Auth-Role
echo "[6/9] Deleting IAM role: CCA-Cognito-Auth-Role..."
aws iam delete-role-policy --role-name CCA-Cognito-Auth-Role --policy-name CCA-CLI-Access-Policy
aws iam delete-role --role-name CCA-Cognito-Auth-Role

# 7. Delete IAM Role: CCA-Lambda-Execution-Role-v2
echo "[7/9] Deleting IAM role: CCA-Lambda-Execution-Role-v2..."
aws iam delete-role-policy --role-name CCA-Lambda-Execution-Role-v2 --policy-name CCA-Lambda-Execution-Policy
aws iam delete-role --role-name CCA-Lambda-Execution-Role-v2

# 8. Disable and schedule KMS key deletion
echo "[8/9] Scheduling KMS key deletion..."
aws kms disable-key --key-id 3ec987ec-fbaf-4de9-bd39-9e1615976e08 --region us-east-1
aws kms schedule-key-deletion --key-id 3ec987ec-fbaf-4de9-bd39-9e1615976e08 --pending-window-in-days 7 --region us-east-1

# 9. Delete KMS alias
echo "[9/9] Deleting KMS alias..."
aws kms delete-alias --alias-name alias/cca-jwt-encryption --region us-east-1

echo ""
echo "✅ CCA 0.2 cleanup complete!"
echo "Note: KMS key will be deleted after 7-day waiting period"
echo "Note: SES identity (info@2112-lab.com) was not deleted (may be shared)"
```

---

## Resource Dependencies

```
┌─────────────────┐
│ KMS Key         │
│ (encryption)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Lambda Function │ ← needs KMS key
│ (registration)  │ ← needs IAM execution role
└────────┬────────┘ ← needs Cognito User Pool
         │          ← needs SES identity
         ▼
┌─────────────────────────┐
│ Cognito User Pool       │
│ + App Client            │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Cognito Identity Pool   │ ← links to User Pool
└────────┬────────────────┘ ← needs Auth IAM role
         │
         ▼
┌─────────────────────────┐
│ IAM Role (Auth)         │ ← assumed by users
└─────────────────────────┘

┌─────────────────┐
│ S3 Bucket       │ ← independent (static website)
└─────────────────┘
```

**Deletion Order (to avoid dependency errors):**
1. Lambda Function & Function URL
2. S3 Bucket
3. CloudWatch Logs
4. Cognito Identity Pool (depends on IAM role)
5. Cognito User Pool (can be deleted before Identity Pool)
6. IAM Roles (delete after Cognito resources)
7. KMS Key (can be deleted last, has 7-30 day waiting period)
8. SES Identity (optional, may be shared with other apps)

---

**Document Status:** ✅ Complete
**Last Updated:** 2025-11-09
**Maintained By:** CCA Team
