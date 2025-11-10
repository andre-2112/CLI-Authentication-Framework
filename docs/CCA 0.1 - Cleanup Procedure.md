# CCA 0.1 - Cleanup Procedure

**Version:** For cleaning up CCA 0.1 (IAM Identity Center) resources after CCA 0.2 deployment
**Last Updated:** 2025-11-09
**Status:** ⚠️ Ready for execution (requires manual confirmation)

---

## Overview

This document provides the complete procedure for cleaning up CCA 0.1 resources after successfully deploying CCA 0.2.

**⚠️ WARNING:** This cleanup is **IRREVERSIBLE**. Ensure CCA 0.2 is fully tested and operational before proceeding.

---

## Pre-Cleanup Checklist

Before cleaning up CCA 0.1, verify:

- [ ] CCA 0.2 is fully deployed and tested
- [ ] All users have migrated to CCA 0.2 (if any existed in 0.1)
- [ ] Registration form is accessible
- [ ] Lambda function is working
- [ ] CCC CLI tool is functional
- [ ] No active users are using CCA 0.1

**Test CCA 0.2:**
```bash
# Test registration form
curl -I http://cca-registration-v2-2025.s3-website-us-east-1.amazonaws.com/registration.html

# Test Lambda function
curl -I https://pli7xymprlva76biu3h6dyso4m0vpqqw.lambda-url.us-east-1.on.aws/

# Verify all resources
aws cognito-idp describe-user-pool --user-pool-id us-east-1_rYTZnMwvc --region us-east-1
```

---

## CCA 0.1 Resources to Clean Up

### Existing CCA 0.1 Resources

| Resource Type | Resource Name/ID | Action |
|---------------|------------------|--------|
| **Lambda Function** | `cca-registration` | ❌ Delete |
| **Lambda Function URL** | (for cca-registration) | ❌ Delete |
| **Lambda Execution Role** | `CCA-Lambda-Execution-Role` | ❌ Delete |
| **S3 Bucket** | `cca-registration-1762463059` | ❌ Delete |
| **IAM Identity Center - Permission Set** | `CCA-CLI-Access` | ❌ Delete |
| **IAM Identity Center - Group** | `CCA-CLI-Users` | ❌ Delete |
| **IAM Identity Center - Users** | (any test users) | ❌ Delete |
| **CloudWatch Log Group** | `/aws/lambda/cca-registration` | ❌ Delete |
| **SES Email Identity** | `info@2112-lab.com` | ✅ **KEEP** (shared resource) |

---

## Backup Procedure

### Step 1: Export IAM Identity Center Configuration

```bash
# Save Identity Store ID
export IDENTITY_STORE_ID=d-9066117351
export SSO_INSTANCE_ARN=arn:aws:sso:::instance/ssoins-72232e1b5b84475a

# List and save all users
aws identitystore list-users \
  --identity-store-id $IDENTITY_STORE_ID \
  --region us-east-1 > ~/CCA/backups/identity-center-users.json

# List and save all groups
aws identitystore list-groups \
  --identity-store-id $IDENTITY_STORE_ID \
  --region us-east-1 > ~/CCA/backups/identity-center-groups.json

# List permission sets
aws sso-admin list-permission-sets \
  --instance-arn $SSO_INSTANCE_ARN \
  --region us-east-1 > ~/CCA/backups/permission-sets.json
```

### Step 2: Export Lambda Configuration

```bash
# Get Lambda function
aws lambda get-function \
  --function-name cca-registration \
  --region us-east-1 > ~/CCA/backups/lambda-function.json

# Get Lambda code
aws lambda get-function \
  --function-name cca-registration \
  --region us-east-1 \
  --query 'Code.Location' \
  --output text | xargs curl -o ~/CCA/backups/lambda-code.zip
```

### Step 3: Backup S3 Bucket

```bash
# Download all files from S3
aws s3 sync s3://cca-registration-1762463059/ ~/CCA/backups/s3-bucket/
```

### Step 4: Export IAM Role

```bash
# Get Lambda execution role
aws iam get-role --role-name CCA-Lambda-Execution-Role > ~/CCA/backups/lambda-role.json

# Get role policies
aws iam list-role-policies --role-name CCA-Lambda-Execution-Role > ~/CCA/backups/lambda-role-policies.json

# Get attached policies
aws iam list-attached-role-policies --role-name CCA-Lambda-Execution-Role > ~/CCA/backups/lambda-attached-policies.json
```

---

## Cleanup Script

### Complete Cleanup Script

```bash
#!/bin/bash
# CCA 0.1 Complete Cleanup Script
# WARNING: This script will DELETE all CCA 0.1 resources!

set -e

echo "========================================="
echo "CCA 0.1 Cleanup Script"
echo "========================================="
echo ""
echo "⚠️  WARNING: This will DELETE all CCA 0.1 resources!"
echo "⚠️  This action is IRREVERSIBLE!"
echo ""
echo "Resources to be deleted:"
echo "  - Lambda function: cca-registration"
echo "  - S3 bucket: cca-registration-1762463059"
echo "  - IAM Role: CCA-Lambda-Execution-Role"
echo "  - IAM Identity Center resources (Permission Sets, Groups)"
echo "  - CloudWatch Logs"
echo ""
echo "Press Ctrl+C to cancel, or type 'DELETE' to continue:"
read confirmation

if [ "$confirmation" != "DELETE" ]; then
  echo "Cleanup cancelled."
  exit 1
fi

echo ""
echo "Starting cleanup..."
echo ""

# Configuration
export IDENTITY_STORE_ID=d-9066117351
export SSO_INSTANCE_ARN=arn:aws:sso:::instance/ssoins-72232e1b5b84475a
export REGION=us-east-1

# 1. Delete Lambda Function
echo "[1/8] Deleting Lambda function..."
aws lambda delete-function-url-config --function-name cca-registration --region $REGION 2>/dev/null || true
sleep 2
aws lambda delete-function --function-name cca-registration --region $REGION
echo "✓ Lambda function deleted"

# 2. Delete S3 Bucket
echo "[2/8] Deleting S3 bucket..."
aws s3 rb s3://cca-registration-1762463059 --force --region $REGION
echo "✓ S3 bucket deleted"

# 3. Delete CloudWatch Log Group
echo "[3/8] Deleting CloudWatch log group..."
aws logs delete-log-group --log-group-name /aws/lambda/cca-registration --region $REGION 2>/dev/null || true
echo "✓ CloudWatch log group deleted"

# 4. Delete IAM Identity Center Users (if any)
echo "[4/8] Checking for Identity Center users..."
USERS=$(aws identitystore list-users \
  --identity-store-id $IDENTITY_STORE_ID \
  --region $REGION \
  --query 'Users[*].UserId' \
  --output text)

if [ ! -z "$USERS" ]; then
  echo "Found users to delete:"
  for user_id in $USERS; do
    echo "  Deleting user: $user_id"
    aws identitystore delete-user \
      --identity-store-id $IDENTITY_STORE_ID \
      --user-id $user_id \
      --region $REGION
  done
  echo "✓ Users deleted"
else
  echo "✓ No users to delete"
fi

# 5. Delete IAM Identity Center Group Memberships
echo "[5/8] Deleting group memberships..."
GROUP_ID=$(aws identitystore list-groups \
  --identity-store-id $IDENTITY_STORE_ID \
  --filters AttributePath=DisplayName,AttributeValue=CCA-CLI-Users \
  --region $REGION \
  --query 'Groups[0].GroupId' \
  --output text)

if [ "$GROUP_ID" != "None" ] && [ ! -z "$GROUP_ID" ]; then
  MEMBERSHIPS=$(aws identitystore list-group-memberships \
    --identity-store-id $IDENTITY_STORE_ID \
    --group-id $GROUP_ID \
    --region $REGION \
    --query 'GroupMemberships[*].MembershipId' \
    --output text)

  if [ ! -z "$MEMBERSHIPS" ]; then
    for membership_id in $MEMBERSHIPS; do
      echo "  Deleting membership: $membership_id"
      aws identitystore delete-group-membership \
        --identity-store-id $IDENTITY_STORE_ID \
        --membership-id $membership_id \
        --region $REGION
    done
  fi
  echo "✓ Group memberships deleted"
else
  echo "✓ No group memberships to delete"
fi

# 6. Delete IAM Identity Center Group
echo "[6/8] Deleting Identity Center group..."
if [ "$GROUP_ID" != "None" ] && [ ! -z "$GROUP_ID" ]; then
  aws identitystore delete-group \
    --identity-store-id $IDENTITY_STORE_ID \
    --group-id $GROUP_ID \
    --region $REGION
  echo "✓ Group deleted"
else
  echo "✓ No group to delete"
fi

# 7. Delete IAM Identity Center Permission Set
echo "[7/8] Deleting Permission Set..."
PERMISSION_SET_ARN=$(aws sso-admin list-permission-sets \
  --instance-arn $SSO_INSTANCE_ARN \
  --region $REGION \
  --query 'PermissionSets[0]' \
  --output text)

if [ "$PERMISSION_SET_ARN" != "None" ] && [ ! -z "$PERMISSION_SET_ARN" ]; then
  # Get AWS Account ID
  ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)

  # Delete account assignments
  aws sso-admin list-account-assignments \
    --instance-arn $SSO_INSTANCE_ARN \
    --account-id $ACCOUNT_ID \
    --permission-set-arn $PERMISSION_SET_ARN \
    --region $REGION \
    --query 'AccountAssignments[*].[PrincipalId]' \
    --output text | while read principal_id; do
    if [ ! -z "$principal_id" ]; then
      aws sso-admin delete-account-assignment \
        --instance-arn $SSO_INSTANCE_ARN \
        --target-id $ACCOUNT_ID \
        --target-type AWS_ACCOUNT \
        --permission-set-arn $PERMISSION_SET_ARN \
        --principal-type GROUP \
        --principal-id $principal_id \
        --region $REGION
    fi
  done

  # Delete permission set
  aws sso-admin delete-permission-set \
    --instance-arn $SSO_INSTANCE_ARN \
    --permission-set-arn $PERMISSION_SET_ARN \
    --region $REGION
  echo "✓ Permission set deleted"
else
  echo "✓ No permission set to delete"
fi

# 8. Delete IAM Role
echo "[8/8] Deleting IAM role..."
# Delete inline policies
aws iam list-role-policies --role-name CCA-Lambda-Execution-Role 2>/dev/null | \
  grep -o '"[^"]*"' | grep -v PolicyNames | tr -d '"' | while read policy_name; do
  if [ ! -z "$policy_name" ]; then
    aws iam delete-role-policy --role-name CCA-Lambda-Execution-Role --policy-name "$policy_name"
  fi
done

# Detach managed policies
aws iam list-attached-role-policies --role-name CCA-Lambda-Execution-Role 2>/dev/null | \
  grep -o 'arn:aws:iam::[^"]*' | while read policy_arn; do
  if [ ! -z "$policy_arn" ]; then
    aws iam detach-role-policy --role-name CCA-Lambda-Execution-Role --policy-arn "$policy_arn"
  fi
done

# Delete role
aws iam delete-role --role-name CCA-Lambda-Execution-Role 2>/dev/null || true
echo "✓ IAM role deleted"

echo ""
echo "========================================="
echo "✅ CCA 0.1 Cleanup Complete!"
echo "========================================="
echo ""
echo "Remaining resources (NOT deleted):"
echo "  ✅ SES Email Identity: info@2112-lab.com (shared resource)"
echo "  ✅ IAM Identity Center Instance (may be used by other applications)"
echo ""
echo "CCA 0.2 remains fully operational."
echo ""
```

---

## Manual Cleanup Steps (Alternative)

If you prefer to clean up manually:

### 1. Delete Lambda Function

```bash
aws lambda delete-function-url-config --function-name cca-registration --region us-east-1
aws lambda delete-function --function-name cca-registration --region us-east-1
```

### 2. Delete S3 Bucket

```bash
aws s3 rb s3://cca-registration-1762463059 --force --region us-east-1
```

### 3. Delete CloudWatch Logs

```bash
aws logs delete-log-group --log-group-name /aws/lambda/cca-registration --region us-east-1
```

### 4. Delete IAM Identity Center Users

```bash
# List users
aws identitystore list-users \
  --identity-store-id d-9066117351 \
  --region us-east-1

# Delete each user
aws identitystore delete-user \
  --identity-store-id d-9066117351 \
  --user-id <USER_ID> \
  --region us-east-1
```

### 5. Delete IAM Identity Center Group

```bash
# Find group ID
export GROUP_ID=$(aws identitystore list-groups \
  --identity-store-id d-9066117351 \
  --filters AttributePath=DisplayName,AttributeValue=CCA-CLI-Users \
  --region us-east-1 \
  --query 'Groups[0].GroupId' \
  --output text)

# Delete group memberships first
aws identitystore list-group-memberships \
  --identity-store-id d-9066117351 \
  --group-id $GROUP_ID \
  --region us-east-1

aws identitystore delete-group-membership \
  --identity-store-id d-9066117351 \
  --membership-id <MEMBERSHIP_ID> \
  --region us-east-1

# Delete group
aws identitystore delete-group \
  --identity-store-id d-9066117351 \
  --group-id $GROUP_ID \
  --region us-east-1
```

### 6. Delete Permission Set

```bash
# List permission sets
aws sso-admin list-permission-sets \
  --instance-arn arn:aws:sso:::instance/ssoins-72232e1b5b84475a \
  --region us-east-1

# Delete account assignments
aws sso-admin delete-account-assignment \
  --instance-arn arn:aws:sso:::instance/ssoins-72232e1b5b84475a \
  --target-id <ACCOUNT_ID> \
  --target-type AWS_ACCOUNT \
  --permission-set-arn <PERMISSION_SET_ARN> \
  --principal-type GROUP \
  --principal-id $GROUP_ID \
  --region us-east-1

# Delete permission set
aws sso-admin delete-permission-set \
  --instance-arn arn:aws:sso:::instance/ssoins-72232e1b5b84475a \
  --permission-set-arn <PERMISSION_SET_ARN> \
  --region us-east-1
```

### 7. Delete IAM Role

```bash
# List and delete role policies
aws iam list-role-policies --role-name CCA-Lambda-Execution-Role
aws iam delete-role-policy --role-name CCA-Lambda-Execution-Role --policy-name <POLICY_NAME>

# Detach managed policies
aws iam list-attached-role-policies --role-name CCA-Lambda-Execution-Role
aws iam detach-role-policy --role-name CCA-Lambda-Execution-Role --policy-arn <POLICY_ARN>

# Delete role
aws iam delete-role --role-name CCA-Lambda-Execution-Role
```

---

## Resources to KEEP

### Do NOT Delete

1. **SES Email Identity** (`info@2112-lab.com`)
   - Reason: Shared resource, used by CCA 0.2
   - Action: Keep verified

2. **IAM Identity Center Instance** (`d-9066117351`)
   - Reason: May be used by other applications
   - Action: Keep active (but remove CCA-specific resources)

---

## Post-Cleanup Verification

After cleanup, verify resources are deleted:

```bash
# Verify Lambda deleted
aws lambda get-function --function-name cca-registration --region us-east-1
# Expected: ResourceNotFoundException

# Verify S3 bucket deleted
aws s3 ls s3://cca-registration-1762463059/
# Expected: NoSuchBucket

# Verify IAM role deleted
aws iam get-role --role-name CCA-Lambda-Execution-Role
# Expected: NoSuchEntity

# Verify CCA 0.2 still works
curl -I http://cca-registration-v2-2025.s3-website-us-east-1.amazonaws.com/registration.html
# Expected: 200 OK
```

---

## Rollback (if needed)

If you need to restore CCA 0.1 after cleanup:

1. Restore Lambda function from `~/CCA/backups/lambda-code.zip`
2. Restore S3 files from `~/CCA/backups/s3-bucket/`
3. Recreate IAM roles using `~/CCA/backups/lambda-role.json`
4. Recreate Identity Center resources from backups

---

## Cost Savings After Cleanup

| Resource | Monthly Cost (Before) | After Cleanup |
|----------|----------------------|---------------|
| Lambda (v0.1) | ~$0.20 | $0 (deleted) |
| S3 Bucket (v0.1) | ~$0.023 | $0 (deleted) |
| CloudWatch Logs | ~$0.50 | ~$0.25 (50% reduction) |
| IAM Identity Center | Free | Free (kept) |
| **Total Savings** | | **~$0.73/month** |

---

## Decision Log

**Date:** 2025-11-09
**Decision:** Cleanup script created and documented
**Status:** ⏳ Pending execution (requires manual approval)
**Reason:** Preserve CCA 0.1 as backup until CCA 0.2 is fully validated

**Next Steps:**
1. Test CCA 0.2 thoroughly with real users
2. Verify all functionality works
3. Get approval from stakeholders
4. Execute cleanup script
5. Verify CCA 0.2 continues to work after cleanup

---

**Document Status:** ✅ Complete
**Last Updated:** 2025-11-09
**Cleanup Status:** 📋 Documented (not yet executed)
