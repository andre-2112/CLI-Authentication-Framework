# AWS Resources Inventory - CCA 0.2.1

**Version:** 0.2.1 (Cognito + Enhancements)
**Last Updated:** 2025-11-10
**Status:** ✅ Active

---

## Overview

This document provides a complete inventory of all AWS resources deployed for Cloud CLI Access (CCA) version 0.2.1. Use this for:
- Resource auditing
- Cost tracking
- Cleanup/teardown procedures
- Troubleshooting

---

## Version History

| Version | Date | Resources | Monthly Cost |
|---------|------|-----------|--------------|
| 0.2.0 | 2025-11-09 | 8 resources | ~$1-2/month |
| 0.2.1 | 2025-11-10 | 13 resources | ~$4-5/month |

---

## Resource Summary (v0.2.1)

| Service | Resource Count | Monthly Cost (Est.) |
|---------|----------------|---------------------|
| **KMS** | 1 key | $1.00 |
| **Cognito User Pools** | 1 pool + 1 client | Free tier (50k MAUs) |
| **Cognito Identity Pools** | 1 pool | Free |
| **IAM Roles** | 3 roles | Free |
| **IAM Policies** | 7 policies (inline) | Free |
| **Lambda** | 1 function | Free tier (1M requests) |
| **S3** | 2 buckets | $0.05/GB |
| **SES** | 1 verified identity | $0.10/1000 emails |
| **CloudTrail** | 1 trail | Free (first trail) |
| **CloudWatch Logs** | 2 log groups | $0.50/GB ingested + $0.50/GB stored |
| **Total** | **13 resources** | **~$4-5/month** |

---

## Quick Reference

### Resource ARNs

```bash
# Core Resources
KMS_KEY=3ec987ec-fbaf-4de9-bd39-9e1615976e08
USER_POOL_ID=us-east-1_rYTZnMwvc
APP_CLIENT_ID=1bga7o1j5vthc9gmfq7eeba3ti
IDENTITY_POOL_ID=us-east-1:0a656e9c-d356-4964-b6ba-610afb34cbb7
LAMBDA_FUNCTION=cca-registration-v2
LAMBDA_URL=https://pli7xymprlva76biu3h6dyso4m0vpqqw.lambda-url.us-east-1.on.aws/

# IAM Roles
CCA_AUTH_ROLE=arn:aws:iam::211050572089:role/CCA-Cognito-Auth-Role
CCA_LAMBDA_ROLE=arn:aws:iam::211050572089:role/CCA-Lambda-Execution-Role-v2
CLOUDTRAIL_ROLE=arn:aws:iam::211050572089:role/CCACloudTrailToCloudWatchLogs

# S3 Buckets
REGISTRATION_BUCKET=cca-registration-v2-2025
CLOUDTRAIL_BUCKET=cca-cloudtrail-logs-211050572089

# CloudTrail & Logs
CLOUDTRAIL_NAME=cca-audit-trail
LOG_GROUP_CLOUDTRAIL=/aws/cloudtrail/cca-users
LOG_GROUP_LAMBDA=/aws/lambda/cca-registration-v2
```

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

# Test authentication
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

**Inline Policies:**

**1. CCA-CLI-Access-Policy** (Core permissions)
- **Deny:** Console access (via signin.amazonaws.com)
- **Allow:** S3 (all actions), EC2 Describe/Get, Lambda List/Get, CloudWatch Logs, IAM read-only, STS GetCallerIdentity

**2. CCACloudTrailRead** ⭐ NEW in v0.2.1
- **Allow:** cloudtrail:LookupEvents

**3. CCACloudWatchLogsRead** ⭐ NEW in v0.2.1
- **Allow:** logs:FilterLogEvents, logs:GetLogEvents, logs:DescribeLogStreams
- **Resource:** arn:aws:logs:*:*:log-group:/aws/cloudtrail/cca-users:*

**CLI Commands:**
```bash
# Get role
aws iam get-role --role-name CCA-Cognito-Auth-Role

# List all policies
aws iam list-role-policies --role-name CCA-Cognito-Auth-Role

# Get specific policy
aws iam get-role-policy \
  --role-name CCA-Cognito-Auth-Role \
  --policy-name CCA-CLI-Access-Policy

# Delete role (for cleanup - delete policies first)
aws iam delete-role-policy --role-name CCA-Cognito-Auth-Role --policy-name CCA-CLI-Access-Policy
aws iam delete-role-policy --role-name CCA-Cognito-Auth-Role --policy-name CCACloudTrailRead
aws iam delete-role-policy --role-name CCA-Cognito-Auth-Role --policy-name CCACloudWatchLogsRead
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

# Delete role (for cleanup)
aws iam delete-role-policy \
  --role-name CCA-Lambda-Execution-Role-v2 \
  --policy-name CCA-Lambda-Execution-Policy
aws iam delete-role --role-name CCA-Lambda-Execution-Role-v2
```

### Role 3: CCACloudTrailToCloudWatchLogs ⭐ NEW in v0.2.1

**Purpose:** Allows CloudTrail to write logs to CloudWatch Logs

| Property | Value |
|----------|-------|
| **Role Name** | `CCACloudTrailToCloudWatchLogs` |
| **Role ARN** | `arn:aws:iam::211050572089:role/CCACloudTrailToCloudWatchLogs` |
| **Path** | `/` |
| **Creation Date** | 2025-11-10 |
| **Tags** | Project=CCA, Version=0.2.1 |

**Trust Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "cloudtrail.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

**Inline Policy: CloudWatchLogsWrite**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:log-group:/aws/cloudtrail/cca-users:*"
    }
  ]
}
```

**CLI Commands:**
```bash
# Get role
aws iam get-role --role-name CCACloudTrailToCloudWatchLogs

# Get role policy
aws iam get-role-policy \
  --role-name CCACloudTrailToCloudWatchLogs \
  --policy-name CloudWatchLogsWrite

# Delete role (for cleanup)
aws iam delete-role-policy \
  --role-name CCACloudTrailToCloudWatchLogs \
  --policy-name CloudWatchLogsWrite
aws iam delete-role --role-name CCACloudTrailToCloudWatchLogs
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
| **Code Size** | 5,575 bytes (v0.2.1 - username removed) |
| **Region** | us-east-1 |
| **Tags** | Project=CCA, Version=0.2.1 |

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
- `/register` - POST - User registration with password (NO username field in v0.2.1)
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

### Bucket 1: Registration Form Bucket

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
- `registration.html` (10.4 KB - v0.2.1, username field removed)

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

### Bucket 2: CloudTrail Logs Bucket ⭐ NEW in v0.2.1

**Purpose:** Store CloudTrail audit logs

| Property | Value |
|----------|-------|
| **Bucket Name** | `cca-cloudtrail-logs-211050572089` |
| **Region** | us-east-1 |
| **Versioning** | Disabled |
| **Encryption** | AES256 (default) |
| **Public Access** | Blocked (private) |
| **Purpose** | CloudTrail log storage |

**Bucket Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AWSCloudTrailAclCheck",
      "Effect": "Allow",
      "Principal": {
        "Service": "cloudtrail.amazonaws.com"
      },
      "Action": "s3:GetBucketAcl",
      "Resource": "arn:aws:s3:::cca-cloudtrail-logs-211050572089"
    },
    {
      "Sid": "AWSCloudTrailWrite",
      "Effect": "Allow",
      "Principal": {
        "Service": "cloudtrail.amazonaws.com"
      },
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::cca-cloudtrail-logs-211050572089/AWSLogs/211050572089/*",
      "Condition": {
        "StringEquals": {
          "s3:x-amz-acl": "bucket-owner-full-control"
        }
      }
    }
  ]
}
```

**CLI Commands:**
```bash
# List objects
aws s3 ls s3://cca-cloudtrail-logs-211050572089/ --region us-east-1 --recursive

# Get bucket policy
aws s3api get-bucket-policy --bucket cca-cloudtrail-logs-211050572089 --region us-east-1

# Delete bucket (for cleanup - must be empty)
aws s3 rb s3://cca-cloudtrail-logs-211050572089 --force --region us-east-1
```

---

## 7. CloudTrail ⭐ NEW in v0.2.1

### CCA Audit Trail

**Purpose:** Log all AWS API activity for auditing and user history

| Property | Value |
|----------|-------|
| **Trail Name** | `cca-audit-trail` |
| **Trail ARN** | `arn:aws:cloudtrail:us-east-1:211050572089:trail/cca-audit-trail` |
| **Region** | us-east-1 |
| **S3 Bucket** | `cca-cloudtrail-logs-211050572089` |
| **CloudWatch Logs** | `/aws/cloudtrail/cca-users` |
| **CloudWatch Logs Role** | `CCACloudTrailToCloudWatchLogs` |
| **Multi-Region Trail** | Yes |
| **Include Global Services** | Yes |
| **Log File Validation** | No |
| **Status** | ✅ Logging |

**Features:**
- Records all AWS API calls
- Streams to CloudWatch Logs in real-time
- Stores logs in S3 for long-term retention
- Multi-region coverage
- Global service event logging

**CLI Commands:**
```bash
# Get trail status
aws cloudtrail get-trail-status --name cca-audit-trail --region us-east-1

# Describe trail
aws cloudtrail describe-trails --trail-name-list cca-audit-trail --region us-east-1

# Lookup recent events
aws cloudtrail lookup-events --max-results 10 --region us-east-1

# Stop logging (for maintenance)
aws cloudtrail stop-logging --name cca-audit-trail --region us-east-1

# Start logging
aws cloudtrail start-logging --name cca-audit-trail --region us-east-1

# Delete trail (for cleanup)
aws cloudtrail delete-trail --name cca-audit-trail --region us-east-1
```

---

## 8. CloudWatch Logs

### Log Group 1: Lambda Logs

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

# Set retention (optional)
aws logs put-retention-policy \
  --log-group-name /aws/lambda/cca-registration-v2 \
  --retention-in-days 30 \
  --region us-east-1

# Delete log group (for cleanup)
aws logs delete-log-group \
  --log-group-name /aws/lambda/cca-registration-v2 \
  --region us-east-1
```

### Log Group 2: CloudTrail Logs ⭐ NEW in v0.2.1

**Purpose:** Store CloudTrail events for user operation history

| Property | Value |
|----------|-------|
| **Log Group** | `/aws/cloudtrail/cca-users` |
| **ARN** | `arn:aws:logs:us-east-1:211050572089:log-group:/aws/cloudtrail/cca-users:*` |
| **Region** | us-east-1 |
| **Retention** | Never expire (can be configured) |
| **Stored Bytes** | (varies) |

**CLI Commands:**
```bash
# Tail logs in real-time
MSYS_NO_PATHCONV=1 aws logs tail /aws/cloudtrail/cca-users --region us-east-1 --follow

# Filter by user ARN
MSYS_NO_PATHCONV=1 aws logs filter-log-events \
  --log-group-name /aws/cloudtrail/cca-users \
  --filter-pattern '{ $.userIdentity.arn = "*CognitoIdentityCredentials*" }' \
  --region us-east-1

# Set retention (recommended)
MSYS_NO_PATHCONV=1 aws logs put-retention-policy \
  --log-group-name /aws/cloudtrail/cca-users \
  --retention-in-days 90 \
  --region us-east-1

# Delete log group (for cleanup)
MSYS_NO_PATHCONV=1 aws logs delete-log-group \
  --log-group-name /aws/cloudtrail/cca-users \
  --region us-east-1
```

---

## 9. SES (Simple Email Service)

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

## Complete Cleanup Script (v0.2.1)

To completely remove all CCA 0.2.1 resources:

```bash
#!/bin/bash
# CCA 0.2.1 Complete Cleanup Script

set -e

echo "=== CCA 0.2.1 Cleanup Script ==="
echo ""
echo "⚠️  WARNING: This will delete ALL CCA 0.2.1 resources!"
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

# 1. Stop and delete CloudTrail
echo "[1/13] Stopping CloudTrail..."
aws cloudtrail stop-logging --name cca-audit-trail --region us-east-1 2>/dev/null || true
aws cloudtrail delete-trail --name cca-audit-trail --region us-east-1

# 2. Delete CloudTrail S3 bucket
echo "[2/13] Deleting CloudTrail S3 bucket..."
aws s3 rb s3://cca-cloudtrail-logs-211050572089 --force --region us-east-1

# 3. Delete CloudWatch log groups
echo "[3/13] Deleting CloudWatch log groups..."
MSYS_NO_PATHCONV=1 aws logs delete-log-group --log-group-name /aws/cloudtrail/cca-users --region us-east-1 2>/dev/null || true
aws logs delete-log-group --log-group-name /aws/lambda/cca-registration-v2 --region us-east-1 2>/dev/null || true

# 4. Delete Lambda function
echo "[4/13] Deleting Lambda function..."
aws lambda delete-function-url-config --function-name cca-registration-v2 --region us-east-1 2>/dev/null || true
aws lambda delete-function --function-name cca-registration-v2 --region us-east-1

# 5. Delete registration S3 bucket
echo "[5/13] Deleting registration S3 bucket..."
aws s3 rb s3://cca-registration-v2-2025 --force --region us-east-1

# 6. Delete Cognito Identity Pool
echo "[6/13] Deleting Cognito Identity Pool..."
aws cognito-identity delete-identity-pool --identity-pool-id us-east-1:0a656e9c-d356-4964-b6ba-610afb34cbb7 --region us-east-1

# 7. Delete Cognito User Pool
echo "[7/13] Deleting Cognito User Pool..."
aws cognito-idp delete-user-pool --user-pool-id us-east-1_rYTZnMwvc --region us-east-1

# 8. Delete IAM role: CCA-Cognito-Auth-Role
echo "[8/13] Deleting IAM role: CCA-Cognito-Auth-Role..."
aws iam delete-role-policy --role-name CCA-Cognito-Auth-Role --policy-name CCA-CLI-Access-Policy
aws iam delete-role-policy --role-name CCA-Cognito-Auth-Role --policy-name CCACloudTrailRead 2>/dev/null || true
aws iam delete-role-policy --role-name CCA-Cognito-Auth-Role --policy-name CCACloudWatchLogsRead 2>/dev/null || true
aws iam delete-role --role-name CCA-Cognito-Auth-Role

# 9. Delete IAM role: CCA-Lambda-Execution-Role-v2
echo "[9/13] Deleting IAM role: CCA-Lambda-Execution-Role-v2..."
aws iam delete-role-policy --role-name CCA-Lambda-Execution-Role-v2 --policy-name CCA-Lambda-Execution-Policy
aws iam delete-role --role-name CCA-Lambda-Execution-Role-v2

# 10. Delete IAM role: CCACloudTrailToCloudWatchLogs
echo "[10/13] Deleting IAM role: CCACloudTrailToCloudWatchLogs..."
aws iam delete-role-policy --role-name CCACloudTrailToCloudWatchLogs --policy-name CloudWatchLogsWrite 2>/dev/null || true
aws iam delete-role --role-name CCACloudTrailToCloudWatchLogs 2>/dev/null || true

# 11. Disable and schedule KMS key deletion
echo "[11/13] Scheduling KMS key deletion..."
aws kms disable-key --key-id 3ec987ec-fbaf-4de9-bd39-9e1615976e08 --region us-east-1
aws kms schedule-key-deletion --key-id 3ec987ec-fbaf-4de9-bd39-9e1615976e08 --pending-window-in-days 7 --region us-east-1

# 12. Delete KMS alias
echo "[12/13] Deleting KMS alias..."
aws kms delete-alias --alias-name alias/cca-jwt-encryption --region us-east-1

# 13. Confirmation
echo "[13/13] Cleanup commands executed!"
echo ""
echo "✅ CCA 0.2.1 cleanup complete!"
echo "Note: KMS key will be deleted after 7-day waiting period"
echo "Note: SES identity (info@2112-lab.com) was not deleted (may be shared)"
```

---

## Resource Dependencies (v0.2.1)

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
│ + CloudTrail Read       │ ⭐ NEW
│ + CloudWatch Logs Read  │ ⭐ NEW
└─────────────────────────┘

┌─────────────────────────┐
│ CloudTrail Trail        │ ⭐ NEW
│ ├─ S3 Bucket            │
│ ├─ CloudWatch Logs      │
│ └─ IAM Role             │
└─────────────────────────┘

┌─────────────────┐
│ S3 Bucket       │ ← independent (static website)
│ (registration)  │
└─────────────────┘
```

**Deletion Order (to avoid dependency errors):**
1. CloudTrail Trail (stop logging first)
2. CloudTrail S3 Bucket (empty first)
3. CloudWatch Log Groups
4. Lambda Function & Function URL
5. Registration S3 Bucket
6. Cognito Identity Pool
7. Cognito User Pool
8. IAM Roles (delete after Cognito resources)
   - CCA-Cognito-Auth-Role (delete policies first)
   - CCA-Lambda-Execution-Role-v2 (delete policies first)
   - CCACloudTrailToCloudWatchLogs (delete policies first)
9. KMS Key (7-30 day waiting period)
10. SES Identity (optional, may be shared)

---

## Cost Breakdown (v0.2.1)

| Resource | Unit Cost | Estimated Usage | Monthly Cost |
|----------|-----------|-----------------|--------------|
| **KMS Key** | $1.00/month | 1 key | $1.00 |
| **KMS Requests** | $0.03/10k requests | ~1k/month | $0.003 |
| **Cognito User Pool** | Free tier | <50k MAUs | $0.00 |
| **Cognito Identity Pool** | Free | All usage | $0.00 |
| **Lambda Invocations** | Free tier | <1M/month | $0.00 |
| **Lambda Compute** | Free tier | <400k GB-sec/month | $0.00 |
| **S3 Storage** | $0.023/GB | 1 GB | $0.023 |
| **S3 Requests** | $0.004/10k GET | 1k/month | $0.0004 |
| **SES Emails** | $0.10/1000 | ~100/month | $0.01 |
| **CloudTrail** | Free | First trail free | $0.00 |
| **CloudWatch Logs Ingestion** | $0.50/GB | ~2 GB/month | $1.00 |
| **CloudWatch Logs Storage** | $0.50/GB | ~5 GB | $2.50 |
| **Total (10 users)** | | | **$4.54/month** |
| **Per User** | | | **$0.45/month** |

**Notes:**
- Costs assume 10 active users
- CloudWatch Logs is the largest cost component (~77% of total)
- Setting retention policy (e.g., 90 days) can reduce storage costs
- Free tier covers Cognito, Lambda, and first CloudTrail trail

---

**Document Status:** ✅ Complete
**Last Updated:** 2025-11-10
**Version:** 0.2.1
**Maintained By:** CCA Team
