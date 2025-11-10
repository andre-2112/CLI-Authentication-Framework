# User Management Guide - CCA 0.2

**Version:** 0.2 (Cognito-based)
**Last Updated:** 2025-11-09

---

## Overview

This guide provides CLI commands for managing users in CCA 0.2 (Cognito-based). All commands require proper AWS credentials with Cognito admin permissions.

**Key Changes from v0.1:**
- Uses `cognito-idp` commands instead of `identitystore`
- Users identified by email (not username)
- Direct password management via Cognito API
- No "group" concept (roles handled via Identity Pool)

---

## Prerequisites

```bash
# Set environment variables
export USER_POOL_ID=us-east-1_rYTZnMwvc
export REGION=us-east-1

# Verify access
aws cognito-idp describe-user-pool --user-pool-id $USER_POOL_ID --region $REGION
```

---

## List Users

### List All Users

```bash
aws cognito-idp list-users \
  --user-pool-id $USER_POOL_ID \
  --region $REGION
```

### List Users (Table Format)

```bash
aws cognito-idp list-users \
  --user-pool-id $USER_POOL_ID \
  --region $REGION \
  --query 'Users[*].[Username,UserStatus,Enabled,UserCreateDate]' \
  --output table
```

### List Users with Email

```bash
aws cognito-idp list-users \
  --user-pool-id $USER_POOL_ID \
  --region $REGION \
  --query 'Users[*].[Username,Attributes[?Name==`email`].Value|[0],UserStatus,Enabled]' \
  --output table
```

### Filter Users by Status

```bash
# Only confirmed users
aws cognito-idp list-users \
  --user-pool-id $USER_POOL_ID \
  --filter "status = \"CONFIRMED\"" \
  --region $REGION

# Only unconfirmed users
aws cognito-idp list-users \
  --user-pool-id $USER_POOL_ID \
  --filter "status = \"UNCONFIRMED\"" \
  --region $REGION
```

---

## Get User Information

### Get Specific User

```bash
aws cognito-idp admin-get-user \
  --user-pool-id $USER_POOL_ID \
  --username user@example.com \
  --region $REGION
```

### Get User Attributes Only

```bash
aws cognito-idp admin-get-user \
  --user-pool-id $USER_POOL_ID \
  --username user@example.com \
  --region $REGION \
  --query 'UserAttributes'
```

### Check if User Exists

```bash
aws cognito-idp admin-get-user \
  --user-pool-id $USER_POOL_ID \
  --username user@example.com \
  --region $REGION \
  --query 'Username' \
  --output text 2>/dev/null && echo "User exists" || echo "User not found"
```

---

## Create Users (Manual)

### Create User with Permanent Password

```bash
# Create user
aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username user@example.com \
  --user-attributes \
    Name=email,Value=user@example.com \
    Name=email_verified,Value=true \
    Name=given_name,Value=John \
    Name=family_name,Value=Doe \
    Name=name,Value="John Doe" \
  --message-action SUPPRESS \
  --region $REGION

# Set permanent password
aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL_ID \
  --username user@example.com \
  --password "YourSecurePassword123!" \
  --permanent \
  --region $REGION
```

### Create User with Temporary Password

```bash
aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username user@example.com \
  --user-attributes \
    Name=email,Value=user@example.com \
    Name=email_verified,Value=true \
  --temporary-password "TempPass123!" \
  --region $REGION
```

---

## Modify Users

### Update User Attributes

```bash
aws cognito-idp admin-update-user-attributes \
  --user-pool-id $USER_POOL_ID \
  --username user@example.com \
  --user-attributes \
    Name=given_name,Value=Jane \
    Name=family_name,Value=Smith \
  --region $REGION
```

### Verify User Email

```bash
aws cognito-idp admin-update-user-attributes \
  --user-pool-id $USER_POOL_ID \
  --username user@example.com \
  --user-attributes Name=email_verified,Value=true \
  --region $REGION
```

### Reset User Password (Admin)

```bash
aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL_ID \
  --username user@example.com \
  --password "NewSecurePassword123!" \
  --permanent \
  --region $REGION
```

---

## Enable/Disable Users

### Disable User

```bash
aws cognito-idp admin-disable-user \
  --user-pool-id $USER_POOL_ID \
  --username user@example.com \
  --region $REGION
```

### Enable User

```bash
aws cognito-idp admin-enable-user \
  --user-pool-id $USER_POOL_ID \
  --username user@example.com \
  --region $REGION
```

### Check User Status

```bash
aws cognito-idp admin-get-user \
  --user-pool-id $USER_POOL_ID \
  --username user@example.com \
  --region $REGION \
  --query '[UserStatus,Enabled]' \
  --output table
```

---

## Delete Users

### Delete Specific User

```bash
aws cognito-idp admin-delete-user \
  --user-pool-id $USER_POOL_ID \
  --username user@example.com \
  --region $REGION
```

### Delete User with Confirmation

```bash
echo "Delete user user@example.com? (yes/no)"
read confirmation
if [ "$confirmation" = "yes" ]; then
  aws cognito-idp admin-delete-user \
    --user-pool-id $USER_POOL_ID \
    --username user@example.com \
    --region $REGION
  echo "User deleted"
else
  echo "Cancelled"
fi
```

---

## Sign Out Users

### Sign Out User from All Devices

```bash
aws cognito-idp admin-user-global-sign-out \
  --user-pool-id $USER_POOL_ID \
  --username user@example.com \
  --region $REGION
```

---

## User Authentication

### Test User Authentication

```bash
export APP_CLIENT_ID=1bga7o1j5vthc9gmfq7eeba3ti

aws cognito-idp admin-initiate-auth \
  --user-pool-id $USER_POOL_ID \
  --client-id $APP_CLIENT_ID \
  --auth-flow ADMIN_NO_SRP_AUTH \
  --auth-parameters \
    USERNAME=user@example.com,PASSWORD="UserPassword123!" \
  --region $REGION
```

### Initiate Password Reset (Send Email)

```bash
aws cognito-idp forgot-password \
  --client-id $APP_CLIENT_ID \
  --username user@example.com \
  --region $REGION
```

### Confirm Password Reset

```bash
aws cognito-idp confirm-forgot-password \
  --client-id $APP_CLIENT_ID \
  --username user@example.com \
  --confirmation-code "123456" \
  --password "NewPassword123!" \
  --region $REGION
```

---

## Bulk Operations

### List All User Emails

```bash
aws cognito-idp list-users \
  --user-pool-id $USER_POOL_ID \
  --region $REGION \
  --query 'Users[*].Attributes[?Name==`email`].Value' \
  --output text | tr '\t' '\n'
```

### Count Users

```bash
aws cognito-idp list-users \
  --user-pool-id $USER_POOL_ID \
  --region $REGION \
  --query 'length(Users)'
```

### Export All Users to CSV

```bash
echo "Username,Email,Status,Enabled,Created" > users.csv

aws cognito-idp list-users \
  --user-pool-id $USER_POOL_ID \
  --region $REGION \
  --query 'Users[*].[Username,Attributes[?Name==`email`].Value|[0],UserStatus,Enabled,UserCreateDate]' \
  --output text | while read line; do
  echo "$line" | tr '\t' ',' >> users.csv
done

echo "Users exported to users.csv"
```

---

## User Pool Statistics

### Get User Pool Info

```bash
aws cognito-idp describe-user-pool \
  --user-pool-id $USER_POOL_ID \
  --region $REGION \
  --query 'UserPool.[Id,Name,EstimatedNumberOfUsers,CreationDate]' \
  --output table
```

### Get Estimated User Count

```bash
aws cognito-idp describe-user-pool \
  --user-pool-id $USER_POOL_ID \
  --region $REGION \
  --query 'UserPool.EstimatedNumberOfUsers'
```

---

## Troubleshooting

### User Can't Login

**Check 1: User exists and is enabled**
```bash
aws cognito-idp admin-get-user \
  --user-pool-id $USER_POOL_ID \
  --username user@example.com \
  --region $REGION \
  --query '[Username,UserStatus,Enabled]'
```

**Check 2: Email is verified**
```bash
aws cognito-idp admin-get-user \
  --user-pool-id $USER_POOL_ID \
  --username user@example.com \
  --region $REGION \
  --query 'UserAttributes[?Name==`email_verified`]'
```

**Check 3: Password is set (status should be CONFIRMED)**
```bash
aws cognito-idp admin-get-user \
  --user-pool-id $USER_POOL_ID \
  --username user@example.com \
  --region $REGION \
  --query 'UserStatus'
  # Should return: "CONFIRMED"
```

**Fix: Reset password**
```bash
aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL_ID \
  --username user@example.com \
  --password "NewPassword123!" \
  --permanent \
  --region $REGION
```

### User Account Locked

**Check account status**
```bash
aws cognito-idp admin-get-user \
  --user-pool-id $USER_POOL_ID \
  --username user@example.com \
  --region $REGION \
  --query '[UserStatus,Enabled]'
```

**Unlock by resetting password**
```bash
aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL_ID \
  --username user@example.com \
  --password "NewPassword123!" \
  --permanent \
  --region $REGION
```

---

## Identity Pool Management

### Get Identity ID for User

Users don't have a pre-existing Identity ID in Cognito Identity Pools. Identity IDs are created dynamically when users authenticate with the CLI.

To see what Identity ID a user would get:

```bash
export IDENTITY_POOL_ID=us-east-1:0a656e9c-d356-4964-b6ba-610afb34cbb7
export ID_TOKEN="<user's ID token from CCC login>"

aws cognito-identity get-id \
  --identity-pool-id $IDENTITY_POOL_ID \
  --logins cognito-idp.us-east-1.amazonaws.com/$USER_POOL_ID=$ID_TOKEN \
  --region $REGION
```

### List All Identities (all authenticated users)

```bash
aws cognito-identity list-identities \
  --identity-pool-id $IDENTITY_POOL_ID \
  --max-results 60 \
  --region $REGION
```

---

## Common Tasks

### Approve New User (Manually)

If a user registered but wasn't approved via Lambda:

```bash
# 1. Create the user
aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username user@example.com \
  --user-attributes \
    Name=email,Value=user@example.com \
    Name=email_verified,Value=true \
    Name=given_name,Value=John \
    Name=family_name,Value=Doe \
  --message-action SUPPRESS \
  --region $REGION

# 2. Set their password (from registration)
aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL_ID \
  --username user@example.com \
  --password "TheirRegistrationPassword123!" \
  --permanent \
  --region $REGION

# 3. Notify user (send email manually or via SES)
echo "User user@example.com has been approved"
```

### Revoke User Access

```bash
# Option 1: Disable user (can be re-enabled)
aws cognito-idp admin-disable-user \
  --user-pool-id $USER_POOL_ID \
  --username user@example.com \
  --region $REGION

# Option 2: Delete user (permanent)
aws cognito-idp admin-delete-user \
  --user-pool-id $USER_POOL_ID \
  --username user@example.com \
  --region $REGION

# Option 3: Sign out all devices + disable
aws cognito-idp admin-user-global-sign-out \
  --user-pool-id $USER_POOL_ID \
  --username user@example.com \
  --region $REGION

aws cognito-idp admin-disable-user \
  --user-pool-id $USER_POOL_ID \
  --username user@example.com \
  --region $REGION
```

---

## Comparison: v0.1 vs v0.2 Commands

| Task | CCA 0.1 (Identity Center) | CCA 0.2 (Cognito) |
|------|---------------------------|-------------------|
| **List users** | `aws identitystore list-users` | `aws cognito-idp list-users` |
| **Get user** | `aws identitystore describe-user` | `aws cognito-idp admin-get-user` |
| **Create user** | `aws identitystore create-user` | `aws cognito-idp admin-create-user` |
| **Delete user** | `aws identitystore delete-user` | `aws cognito-idp admin-delete-user` |
| **Set password** | ❌ No API | ✅ `aws cognito-idp admin-set-user-password` |
| **Disable user** | ❌ No direct API | ✅ `aws cognito-idp admin-disable-user` |
| **User ID format** | UUID (e.g., 9408a4a8-...) | Email (e.g., user@example.com) |

---

## Quick Reference

```bash
# Environment Setup
export USER_POOL_ID=us-east-1_rYTZnMwvc
export APP_CLIENT_ID=1bga7o1j5vthc9gmfq7eeba3ti
export IDENTITY_POOL_ID=us-east-1:0a656e9c-d356-4964-b6ba-610afb34cbb7
export REGION=us-east-1

# Most Common Commands
aws cognito-idp list-users --user-pool-id $USER_POOL_ID --region $REGION
aws cognito-idp admin-get-user --user-pool-id $USER_POOL_ID --username user@example.com --region $REGION
aws cognito-idp admin-set-user-password --user-pool-id $USER_POOL_ID --username user@example.com --password "NewPass123!" --permanent --region $REGION
aws cognito-idp admin-disable-user --user-pool-id $USER_POOL_ID --username user@example.com --region $REGION
aws cognito-idp admin-delete-user --user-pool-id $USER_POOL_ID --username user@example.com --region $REGION
```

---

**Document Status:** ✅ Complete
**Last Updated:** 2025-11-09
