# CCA 0.2 - AWS Credentials Security Considerations

**Version:** 0.2 (Cognito-based)
**Last Updated:** 2025-11-09
**Purpose:** Clarify security model for AWS credentials in CCA 0.2

---

## Context

This document addresses important questions about the AWS credentials used in CCA 0.2, specifically regarding lines 341-344 from "CCA 0.2 - Cognito Design.md":

```
│  │ 5. Configure AWS CLI environment                     │ │
│  │    - Set AWS_ACCESS_KEY_ID                           │ │
│  │    - Set AWS_SECRET_ACCESS_KEY                       │ │
│  │    - Set AWS_SESSION_TOKEN                           │ │
```

---

## Questions and Answers

### Question 1: Explain why is the AWS CLI environment necessary?

**Answer:**

The AWS CLI environment (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN) is necessary so that when users run standard AWS CLI commands (like `aws s3 ls`, `aws ec2 describe-instances`, etc.), the AWS CLI knows **what credentials to use** to authenticate API calls to AWS services.

Without these environment variables or credentials in `~/.aws/credentials`, the AWS CLI would fail with "Unable to locate credentials" errors.

---

### Question 2: Are the referred AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY, the AWS accounts' AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY? Yes/No?

**Answer: NO**

These are **NOT** the AWS account's root or IAM user credentials. They are **TEMPORARY STS credentials** generated dynamically for each user session.

---

### Question 2.1: Explain why are they necessary for our sample cli too, if its supposed to rely on a temporary access token?

**Answer:**

There are actually **TWO separate tools** involved:

1. **CCC CLI** (`ccc` command) - Our custom authentication tool
   - Purpose: Authenticate with Cognito, obtain temporary AWS credentials
   - User runs: `ccc login`
   - Stores credentials in `~/.aws/credentials`

2. **AWS CLI** (`aws` command) - Standard AWS CLI tool
   - Purpose: Make API calls to AWS services (S3, EC2, Lambda, etc.)
   - User runs: `aws s3 ls`, `aws ec2 describe-instances`, etc.
   - Reads credentials from `~/.aws/credentials`

**The flow:**
```
User runs: ccc login
  └─> CCC CLI authenticates with Cognito
  └─> Gets temporary AWS credentials from Identity Pool
  └─> Saves to ~/.aws/credentials

User runs: aws s3 ls
  └─> AWS CLI reads credentials from ~/.aws/credentials
  └─> Uses those credentials to call S3 API
```

So the temporary credentials are necessary because the **standard AWS CLI needs credentials** to make API calls. The CCC CLI is just the authentication layer that obtains and manages those credentials.

---

### Question 2.2: Isn't dangerous to expose the AWS accounts' AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY to users of a cli?

**Answer: NO, it's NOT dangerous, because:**

#### These are NOT permanent account credentials

They are **temporary STS credentials** with the following characteristics:

1. **Time-limited**: Expire after 12 hours
2. **Scoped permissions**: Restricted to specific IAM role permissions (defined in `CCA-Cognito-Auth-Role`)
3. **User-specific**: Each user gets their own unique temporary credentials
4. **Console access denied**: Explicitly blocked from using AWS Console (only CLI access)
5. **Revocable**: Admin can disable the user in Cognito, invalidating all their credentials
6. **Auditable**: All actions logged in CloudTrail with the user's identity

#### How they're generated:

```
User authenticates → Cognito ID Token
                  → Identity Pool exchanges token with STS
                  → STS calls AssumeRoleWithWebIdentity
                  → STS generates TEMPORARY credentials (12 hours)
                  → Credentials returned to user
```

#### What they look like:

```ini
[cca]
aws_access_key_id = ASIA...              ← Starts with "ASIA" (temporary)
aws_secret_access_key = ...               ← Temporary secret
aws_session_token = ...                   ← Required for temporary credentials
# expires_at = 2025-11-10T07:30:00+00:00  ← 12-hour expiration
```

**Contrast with permanent credentials:**
- Permanent credentials start with `AKIA` (not `ASIA`)
- No session token
- No expiration
- Full account access (if root)

#### Why this is secure:

If a user's temporary credentials are compromised:
- Attacker has only 12 hours (or less if partially expired)
- Attacker has only CLI access (limited permissions)
- Attacker cannot escalate privileges
- Attacker cannot access console
- Admin can revoke user, invalidating credentials

---

## Summary

The confusion in the documentation wording comes from using "AWS_ACCESS_KEY_ID" and "AWS_SECRET_ACCESS_KEY" which **sounds like** permanent account credentials, but they are actually **temporary STS credentials**.

**The design is secure** - users never receive or have access to the AWS account's permanent credentials. They only receive temporary, limited-scope credentials that expire after 12 hours.

---

## Detailed Security Model

### Credential Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│ AWS Account Root Credentials                                │
│ - NEVER shared with users                                   │
│ - NEVER used by CCA                                         │
│ - Only for account administration                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ IAM Role: CCA-Cognito-Auth-Role                             │
│ - Defines permissions for CCA users                         │
│ - Assumed via STS AssumeRoleWithWebIdentity                 │
│ - Trust policy: Only Cognito Identity Pool can assume      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Temporary STS Credentials (per user, per session)          │
│ - ASIA... (temporary access key ID)                        │
│ - Temporary secret access key                              │
│ - Session token (required)                                 │
│ - 12-hour expiration                                        │
│ - Limited permissions (from IAM role)                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ User's ~/.aws/credentials file                              │
│ [cca]                                                        │
│ aws_access_key_id = ASIA...                                 │
│ aws_secret_access_key = ...                                 │
│ aws_session_token = ...                                     │
└─────────────────────────────────────────────────────────────┘
```

### Authentication Flow with Credential Types

```
┌──────────────┐
│ User         │
│ ccc login    │
└──────┬───────┘
       │ Email + Password
       ▼
┌──────────────────┐
│ Cognito          │
│ User Pool        │
└──────┬───────────┘
       │ ID Token (JWT)
       ▼
┌──────────────────┐
│ Cognito          │
│ Identity Pool    │
└──────┬───────────┘
       │ "Give me credentials for this user"
       ▼
┌──────────────────┐
│ AWS STS          │
│ AssumeRole       │
│ WithWebIdentity  │
└──────┬───────────┘
       │ TEMPORARY credentials
       │ - Access Key ID: ASIA... (not AKIA...)
       │ - Secret Access Key: (temporary)
       │ - Session Token: (required)
       │ - Expiration: 12 hours
       ▼
┌──────────────────┐
│ ~/.aws/          │
│ credentials      │
│ [cca] profile    │
└──────────────────┘
       │
       ▼
┌──────────────────┐
│ User runs:       │
│ aws s3 ls        │
│ --profile cca    │
└──────────────────┘
```

---

## Permissions Scope

### What Users CAN Do

With their temporary credentials, users can:

- ✅ List S3 buckets and objects (`s3:*`)
- ✅ Describe EC2 instances (`ec2:Describe*`, `ec2:Get*`)
- ✅ List Lambda functions (`lambda:List*`, `lambda:Get*`)
- ✅ View CloudWatch logs (`logs:Describe*`, `logs:Get*`, `logs:FilterLogEvents`)
- ✅ Check their identity (`sts:GetCallerIdentity`)
- ✅ View IAM roles (read-only: `iam:GetRole`, `iam:ListRoles`)

**Duration:** 12 hours, then must refresh

### What Users CANNOT Do

With their temporary credentials, users **cannot**:

- ❌ Access AWS Console (signin.amazonaws.com blocked)
- ❌ Create or delete IAM users/roles
- ❌ Modify account settings
- ❌ Access billing information
- ❌ Create or delete EC2 instances (no write permissions)
- ❌ Delete S3 buckets or objects (read-only in most cases)
- ❌ Escalate privileges
- ❌ Assume other roles (not granted `sts:AssumeRole`)

**These restrictions are enforced by the IAM role policy attached to `CCA-Cognito-Auth-Role`.**

---

## Credential Identification

### How to Identify Temporary vs Permanent Credentials

| Property | Temporary (STS) | Permanent (IAM User) |
|----------|-----------------|----------------------|
| **Access Key Prefix** | `ASIA...` | `AKIA...` |
| **Session Token** | ✅ Required | ❌ Not present |
| **Expiration** | ✅ Yes (12 hours) | ❌ No expiration |
| **Source** | STS AssumeRole | IAM User creation |
| **Revocable** | Yes (disable Cognito user) | Yes (delete IAM user) |
| **Scope** | Limited to role permissions | Full IAM user permissions |

### Example: Temporary Credentials (CCA 0.2)

```ini
[cca]
aws_access_key_id = ASIATEMP1234567890AB          ← Starts with "ASIA"
aws_secret_access_key = abc123...                  ← Temporary secret
aws_session_token = IQoJb3JpZ2luX2VjEDc...       ← Session token REQUIRED
# expires_at = 2025-11-10T07:30:00+00:00           ← Expires in 12 hours
```

### Example: Permanent Credentials (NOT used in CCA)

```ini
[default]
aws_access_key_id = AKIAPERM1234567890CD          ← Starts with "AKIA"
aws_secret_access_key = xyz789...                  ← Permanent secret
# No session token                                 ← No session token
# No expiration                                    ← Never expires
```

---

## Security Comparison

### CCA 0.2 (Temporary Credentials) vs Traditional IAM User Approach

| Security Aspect | CCA 0.2 (Temporary) | Traditional IAM Users |
|-----------------|---------------------|----------------------|
| **Credential Lifetime** | 12 hours | Indefinite (until manually rotated) |
| **Rotation** | Automatic (refresh token) | Manual (90-day policy) |
| **Blast Radius** | Single user, 12 hours | All users, indefinite |
| **Revocation** | Instant (disable Cognito user) | Manual (delete IAM user) |
| **Audit Trail** | Cognito identity in CloudTrail | IAM user name |
| **Console Access** | Explicitly denied | Allowed (unless denied) |
| **Privilege Escalation** | Not possible | Possible (if IAM write access) |
| **Credential Leak Risk** | Low (expires in 12 hours) | High (valid until rotated) |

---

## Common Misconceptions

### Misconception 1: "Users have access to the AWS account credentials"

**Reality:** Users NEVER have access to the AWS account's permanent credentials. They receive temporary, scoped credentials generated by STS.

### Misconception 2: "Credentials in ~/.aws/credentials are dangerous to expose"

**Reality:** Temporary credentials with limited scope and 12-hour expiration are safe to store locally. Even if stolen, attacker has:
- Only 12 hours (or less)
- Limited permissions (no console, no IAM write, no billing)
- Auditable actions (CloudTrail logs everything)

### Misconception 3: "AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are always permanent"

**Reality:** These environment variable names are used for BOTH permanent and temporary credentials. The presence of `AWS_SESSION_TOKEN` indicates temporary credentials.

### Misconception 4: "CCA users can access the AWS Console"

**Reality:** Console access is explicitly denied in the IAM role policy via:
```json
{
  "Condition": {
    "StringEquals": {
      "aws:via": "signin.amazonaws.com"
    }
  }
}
```

---

## Best Practices

### For Administrators

1. **Never share permanent credentials**
   - Never give users IAM user credentials
   - Always use STS temporary credentials

2. **Monitor credential usage**
   ```bash
   # Check CloudTrail for user activity
   aws cloudtrail lookup-events \
     --lookup-attributes AttributeKey=Username,AttributeValue=<cognito-identity-id> \
     --region us-east-1
   ```

3. **Set appropriate session duration**
   - 12 hours is a good balance
   - Too short: Users frustrated by constant re-auth
   - Too long: Increased risk if credentials leaked

4. **Implement least privilege**
   - Only grant permissions users actually need
   - Review IAM role policy regularly

5. **Enable CloudTrail logging**
   - Audit all API calls
   - Alert on suspicious activity

### For Users

1. **Keep credentials secure**
   - Don't share `~/.aws/credentials` file
   - Don't commit credentials to Git
   - Use file permissions: `chmod 600 ~/.aws/credentials`

2. **Use refresh tokens**
   ```bash
   ccc refresh  # Refresh without re-entering password
   ```

3. **Logout when done**
   ```bash
   ccc logout  # Clear stored tokens and credentials
   ```

4. **Monitor expiration**
   ```bash
   ccc whoami  # Check credential expiration time
   ```

---

## Technical Deep Dive: STS AssumeRoleWithWebIdentity

### How CCA 0.2 Obtains Temporary Credentials

#### Step 1: User Authentication
```python
# User provides email + password
tokens = cognito_client.initiate_auth(
    ClientId=app_client_id,
    AuthFlow='USER_PASSWORD_AUTH',
    AuthParameters={
        'USERNAME': email,
        'PASSWORD': password
    }
)
# Returns: IdToken, AccessToken, RefreshToken
```

#### Step 2: Get Cognito Identity ID
```python
# Exchange ID token for Cognito Identity ID
identity_response = identity_client.get_id(
    IdentityPoolId=identity_pool_id,
    Logins={
        f'cognito-idp.us-east-1.amazonaws.com/{user_pool_id}': id_token
    }
)
identity_id = identity_response['IdentityId']
# Returns: "us-east-1:abcd1234-..." (Cognito Identity ID)
```

#### Step 3: Get Temporary AWS Credentials (STS)
```python
# Exchange Cognito Identity for AWS credentials
# This internally calls STS AssumeRoleWithWebIdentity
credentials_response = identity_client.get_credentials_for_identity(
    IdentityId=identity_id,
    Logins={
        f'cognito-idp.us-east-1.amazonaws.com/{user_pool_id}': id_token
    }
)

credentials = credentials_response['Credentials']
# Returns:
# {
#   'AccessKeyId': 'ASIATEMP...',      ← Temporary access key
#   'SecretKey': '...',                 ← Temporary secret
#   'SessionToken': '...',              ← Session token
#   'Expiration': datetime(2025, 11, 10, 7, 30, 0)
# }
```

#### Step 4: Save to ~/.aws/credentials
```python
# Write to credentials file
config_content = {
    'cca': {
        'aws_access_key_id': credentials['AccessKeyId'],
        'aws_secret_access_key': credentials['SecretKey'],
        'aws_session_token': credentials['SessionToken']
    }
}
# User can now run: aws --profile cca s3 ls
```

### What Happens Behind the Scenes

When `get_credentials_for_identity` is called, Cognito Identity Pool internally calls:

```
STS.AssumeRoleWithWebIdentity(
    RoleArn='arn:aws:iam::211050572089:role/CCA-Cognito-Auth-Role',
    WebIdentityToken=<Cognito ID Token>,
    RoleSessionName='CognitoIdentityCredentials'
)
```

This returns temporary credentials scoped to the `CCA-Cognito-Auth-Role` permissions.

---

## CloudTrail Logging

### User Activity Tracking

All API calls made with temporary credentials are logged in CloudTrail with:

```json
{
  "eventName": "ListBuckets",
  "userIdentity": {
    "type": "AssumedRole",
    "principalId": "AROATCI4YFE4WD6FVPRMA:CognitoIdentityCredentials",
    "arn": "arn:aws:sts::211050572089:assumed-role/CCA-Cognito-Auth-Role/CognitoIdentityCredentials",
    "accountId": "211050572089",
    "accessKeyId": "ASIATEMP1234567890AB",
    "sessionContext": {
      "attributes": {
        "creationDate": "2025-11-09T19:30:00Z",
        "mfaAuthenticated": "false"
      },
      "sessionIssuer": {
        "type": "Role",
        "principalId": "AROATCI4YFE4WD6FVPRMA",
        "arn": "arn:aws:iam::211050572089:role/CCA-Cognito-Auth-Role",
        "accountId": "211050572089",
        "userName": "CCA-Cognito-Auth-Role"
      },
      "webIdFederationData": {
        "federatedProvider": "cognito-identity.amazonaws.com",
        "attributes": {
          "cognito-identity.amazonaws.com:aud": "us-east-1:0a656e9c-d356-4964-b6ba-610afb34cbb7",
          "cognito-identity.amazonaws.com:sub": "us-east-1:user-identity-id"
        }
      }
    }
  },
  "eventTime": "2025-11-09T19:35:00Z",
  "eventSource": "s3.amazonaws.com",
  "eventName": "ListBuckets",
  "sourceIPAddress": "203.0.113.1",
  "userAgent": "aws-cli/2.13.0"
}
```

**Key fields for tracking:**
- `userIdentity.accessKeyId`: Temporary access key (ASIA...)
- `userIdentity.sessionContext.webIdFederationData`: Cognito identity details
- `eventTime`: When the action occurred
- `sourceIPAddress`: User's IP address

---

## Conclusion

**CCA 0.2 is designed with security as a top priority:**

✅ **No permanent credentials exposed to users**
✅ **Time-limited sessions (12 hours)**
✅ **Scoped permissions (least privilege)**
✅ **Console access denied**
✅ **Full audit trail in CloudTrail**
✅ **Revocable at any time**

The temporary credentials stored in `~/.aws/credentials` are safe because:
1. They expire after 12 hours
2. They have limited permissions
3. They can be revoked instantly
4. All actions are auditable
5. They cannot access the console

**This is industry standard practice used by AWS organizations worldwide for secure, temporary access to AWS resources.**

---

**Document Status:** ✅ Complete
**Last Updated:** 2025-11-09
**Purpose:** Security clarification and education
