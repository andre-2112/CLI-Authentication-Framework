# CLI Authentication Framework v0.3 - User Guide

**Version**: 0.3
**Last Updated**: November 10, 2025
**Purpose**: Quick start guide for end users

---

## What Is This?

The CLI Authentication Framework provides **secure, self-service access** to AWS services through the command line. No need to wait for IT to create accounts or manage credentials manually.

**Key Benefits**:
- Register yourself in minutes
- Reset your own password anytime
- Get temporary AWS credentials (no permanent keys)
- Access AWS CLI commands securely
- Track your AWS activity

---

## Quick Start (5 Minutes)

### 1. Register Your Account

```
ccc register
```

You'll be prompted for:
- Email address
- First name (optional)
- Last name (optional)
- Password

**Wait for admin approval email** (usually within 24 hours)

### 2. Login

```
ccc login
```

Enter your email and password when prompted.

### 3. Use AWS CLI

```
aws s3 ls
aws ec2 describe-instances
aws lambda list-functions
```

Your AWS credentials are automatically configured!

### 4. Logout When Done

```
ccc logout
```

---

## Registration Flow

```
┌─────────┐
│  Start  │
└────┬────┘
     │
     ▼
┌────────────────┐
│  ccc register  │  ◄── Enter: email, names (optional), password
└────┬───────────┘
     │
     ▼
┌──────────────────┐
│ Submitted!       │
│ Wait for email   │  ◄── Admin will approve/deny
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ Approval Email   │  ◄── "You've been approved!"
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│   ccc login      │  ◄── You can now login
└────┬─────────────┘
     │
     ▼
┌─────────┐
│  Ready! │
└─────────┘
```

**Timeline**:
- Registration: 2 minutes
- Admin approval: Up to 24 hours
- First login: 1 minute

---

## Login Flow

```
┌─────────┐
│  Start  │
└────┬────┘
     │
     ▼
┌──────────────┐
│  ccc login   │  ◄── Enter: email, password
└────┬─────────┘
     │
     ▼
┌──────────────────────┐
│ Get AWS Credentials  │  ◄── Valid for 60 minutes
└────┬─────────────────┘
     │
     ▼
┌──────────────────────┐
│ Credentials Saved    │  ◄── Stored in ~/.aws/credentials
└────┬─────────────────┘
     │
     ▼
┌─────────────────┐
│  Use AWS CLI    │  ◄── aws s3 ls, aws ec2 describe-instances, etc.
└────┬────────────┘
     │
     │ (After 60 minutes)
     ▼
┌──────────────────┐
│  ccc refresh     │  ◄── Get new credentials
└────┬─────────────┘
     │
     ▼
┌─────────────────┐
│  Continue Work  │
└─────────────────┘
```

**Important**: Credentials expire after 60 minutes. Run `ccc refresh` to get new ones.

---

## Password Management

### Forgot Your Password?

```
┌─────────────────────┐
│ ccc forgot-password │  ◄── Enter your email
└────┬────────────────┘
     │
     ▼
┌──────────────────────┐
│ Check Your Email     │  ◄── You'll receive a verification code
└────┬─────────────────┘
     │
     ▼
┌──────────────────────┐
│ Enter Code           │  ◄── Type the 6-digit code
└────┬─────────────────┘
     │
     ▼
┌──────────────────────┐
│ Enter New Password   │  ◄── Choose a strong password
└────┬─────────────────┘
     │
     ▼
┌─────────┐
│  Done!  │  ◄── Login with new password
└─────────┘
```

### Change Your Password (When Logged In)

```
┌─────────────────────┐
│ ccc change-password │  ◄── Must be logged in
└────┬────────────────┘
     │
     ▼
┌──────────────────────┐
│ Enter Current        │  ◄── Verify your identity
│ Password             │
└────┬─────────────────┘
     │
     ▼
┌──────────────────────┐
│ Enter New Password   │  ◄── Choose a strong password
└────┬─────────────────┘
     │
     ▼
┌─────────┐
│  Done!  │
└─────────┘
```

---

## Common Workflows

### Workflow 1: Daily AWS Work

```
Morning:
  ccc login          → Get credentials (valid 60 minutes)
  aws s3 ls          → Work with AWS
  aws ec2 ...

After 60 minutes:
  ccc refresh        → Renew credentials (no password needed)

Continue working...

End of day:
  ccc logout         → Clear credentials
```

### Workflow 2: Check What You Did Today

```
ccc history         → See all AWS operations

Example output:
  2025-11-10 14:23:45 | ListBuckets | s3.amazonaws.com
  2025-11-10 14:24:12 | DescribeInstances | ec2.amazonaws.com
  2025-11-10 14:25:30 | ListFunctions | lambda.amazonaws.com
```

### Workflow 3: Check Your Permissions

```
ccc permissions     → See what AWS actions you can perform

Example output:
  s3:*                     ✅ Full S3 access
  ec2:Describe*            ✅ Read EC2 info
  ec2:StartInstances       ❌ Cannot start EC2
  lambda:List*             ✅ Read Lambda info
```

### Workflow 4: Find AWS Resources

```
ccc resources       → List all AWS resources you have access to

Example output:
  Found 93 resources across 26 types:
    - S3 buckets: 5
    - EC2 instances: 3
    - Lambda functions: 8
    - ...
```

---

## Command Reference

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `ccc register` | Create new account | First time only |
| `ccc login` | Get AWS credentials | Start of work session |
| `ccc refresh` | Renew credentials | Every 60 minutes |
| `ccc logout` | Clear credentials | End of work session |
| `ccc forgot-password` | Reset forgotten password | When you can't login |
| `ccc change-password` | Change password | When logged in |
| `ccc whoami` | Show current user info | Check who you're logged in as |
| `ccc history` | Show AWS activity | Review what you did |
| `ccc resources` | List AWS resources | Discover what's available |
| `ccc permissions` | Show AWS permissions | Check what you can do |
| `ccc version` | Show CLI version | Troubleshooting |

---

## Typical Day Example

**Sarah's Morning**:

```
8:00 AM  → ccc login
         → Email: sarah@example.com
         → Password: ****
         → ✅ Login successful!

8:05 AM  → aws s3 ls
         → Lists all S3 buckets

8:30 AM  → aws ec2 describe-instances
         → Shows EC2 instances

9:15 AM  → Credentials expired (60 min)
         → ccc refresh
         → ✅ Credentials renewed!

10:00 AM → aws lambda list-functions
         → Shows Lambda functions

12:00 PM → Lunch break
         → ccc logout

1:00 PM  → Back from lunch
         → ccc login

5:00 PM  → End of day
         → ccc logout
         → ✅ Session cleared!
```

---

## Understanding Credentials

### What Are Temporary Credentials?

- **Valid for**: 60 minutes
- **Stored in**: `~/.aws/credentials`
- **Format**: `[cca]` profile
- **Type**: Temporary (start with ASIA*, not AKIA*)

### When Do They Expire?

```
Login at 9:00 AM  → Valid until 10:00 AM
Refresh at 9:55 AM → Valid until 10:55 AM
Refresh at 10:50 AM → Valid until 11:50 AM
```

### What Happens When Expired?

```
$ aws s3 ls

Error: The security token included in the request is expired

Solution:
$ ccc refresh
✅ Credentials renewed!
```

---

## Security Best Practices

### Do's ✅

- **Use strong passwords** (8+ chars, upper, lower, number, symbol)
- **Logout when done** (`ccc logout`)
- **Refresh before expiration** (run `ccc refresh` every 50 minutes)
- **Keep your password private** (never share it)
- **Use forgot-password** if compromised

### Don'ts ❌

- **Don't share your credentials** (each user gets their own)
- **Don't commit credentials to Git** (they're temporary anyway)
- **Don't login on shared computers** (or logout after)
- **Don't use same password everywhere** (unique password for this)

---

## Troubleshooting

### Problem: "User does not exist"

**Cause**: Not registered or registration not approved yet

**Solution**:
1. Run `ccc register` if you haven't
2. Check email for approval notification
3. Wait for admin to approve (up to 24 hours)

---

### Problem: "Incorrect username or password"

**Cause**: Wrong email or password

**Solution**:
1. Double-check your email address
2. Try `ccc forgot-password` to reset
3. Contact admin if still stuck

---

### Problem: "Token expired"

**Cause**: Credentials expired (60 minutes passed)

**Solution**:
```
ccc refresh
```

If refresh fails:
```
ccc login
```

---

### Problem: "Access Denied" on AWS command

**Cause**: You don't have permission for that action

**Solution**:
1. Check your permissions: `ccc permissions`
2. Verify what you can do
3. Contact admin if you need more access

Example:
```
$ aws ec2 start-instances --instance-id i-1234

Error: Access Denied

$ ccc permissions | grep ec2
ec2:Describe*  ✅
ec2:Get*       ✅
ec2:Start*     ❌  ← You can't start instances
```

---

### Problem: Can't find AWS resources

**Cause**: Looking in wrong region

**Solution**:
```
ccc resources --region us-west-2
```

Default region is `us-east-1`. Use `--region` flag to check other regions.

---

### Problem: "Command not found: ccc"

**Cause**: CLI not installed or not in PATH

**Solution**:
1. Check installation: `which ccc`
2. Reinstall if needed
3. Contact admin for installation help

---

## Web Registration Alternative

Don't like the CLI? Use the web form instead!

**URL**: (Provided by your admin)

**Process**:
1. Open registration URL in browser
2. Fill out form (email, names, password)
3. Submit
4. Wait for approval email
5. Use `ccc login` from CLI

Same result, different interface!

---

## Getting Help

### Built-in Help

```
ccc --help              → List all commands
ccc login --help        → Help for specific command
ccc version             → Show version
```

### Command Examples

Every command shows examples:

```
$ ccc history --help

Usage: ccc history [OPTIONS]

Options:
  --days INTEGER  Number of days to look back
  --limit INTEGER Maximum number of events
  --help          Show this message and exit

Examples:
  ccc history                  # Last 7 days
  ccc history --days 30        # Last 30 days
  ccc history --limit 10       # Last 10 events
```

### Contact Admin

If you're stuck:
1. Check this guide first
2. Run `ccc --help`
3. Contact your admin with:
   - What command you ran
   - What error you saw
   - Output of `ccc version`

---

## Appendix: Password Requirements

### Minimum Requirements

- **Length**: 8 characters minimum
- **Uppercase**: At least 1 (A-Z)
- **Lowercase**: At least 1 (a-z)
- **Number**: At least 1 (0-9)
- **Symbol**: At least 1 (!@#$%^&*)

### Good Password Examples

- `MyAws2025!`
- `Secure@Pass123`
- `Work$Cloud99`

### Bad Password Examples

- `password` (no uppercase, number, or symbol)
- `12345678` (no letters or symbols)
- `PASSWORD` (no lowercase, number, or symbol)

---

## Appendix: Session Lifecycle

```
┌──────────────┐
│ Not Logged In│
└──────┬───────┘
       │
       │ ccc login
       ▼
┌──────────────┐
│ Logged In    │ ◄─────────┐
│ (60 min)     │            │
└──────┬───────┘            │
       │                    │
       │ After 60 min       │ ccc refresh
       ▼                    │
┌──────────────┐            │
│ Expired      │────────────┘
└──────┬───────┘
       │
       │ ccc logout
       ▼
┌──────────────┐
│ Not Logged In│
└──────────────┘
```

**Key Points**:
- Login gives you 60 minutes
- Refresh extends another 60 minutes (no password needed)
- Logout clears credentials immediately
- Expired credentials require login or refresh

---

## Appendix: What Commands Can I Run?

### Always Available (No Login Required)

```
ccc register
ccc forgot-password
ccc version
ccc --help
```

### Requires Login

```
ccc refresh          → Renew credentials
ccc logout           → Clear credentials
ccc change-password  → Change password
ccc whoami          → Show user info
ccc history         → Show AWS activity
ccc resources       → List AWS resources
ccc permissions     → Show AWS permissions
```

### After Login (AWS CLI)

```
aws s3 ls
aws s3 cp file.txt s3://bucket/
aws ec2 describe-instances
aws ec2 describe-vpcs
aws lambda list-functions
aws lambda get-function --function-name my-function
aws logs describe-log-groups
aws logs tail /aws/lambda/my-function
```

---

## Appendix: Configuration Files

### Where Are My Credentials Stored?

**Linux/Mac**: `~/.aws/credentials`
**Windows**: `C:\Users\YourName\.aws\credentials`

### What's in the File?

```
[cca]
aws_access_key_id = ASIA...
aws_secret_access_key = ...
aws_session_token = ...
```

These are **temporary credentials** that expire after 60 minutes.

### Can I Delete This File?

Yes! Run `ccc logout` to safely remove credentials.

---

## Appendix: First-Time Setup Checklist

- [ ] Received registration URL from admin
- [ ] Ran `ccc register` or used web form
- [ ] Provided email address
- [ ] Created strong password (8+ chars, upper, lower, number, symbol)
- [ ] Received approval email from admin
- [ ] Ran `ccc login` successfully
- [ ] Tested AWS CLI command (`aws s3 ls`)
- [ ] Bookmarked this guide
- [ ] Know how to run `ccc refresh` before expiration
- [ ] Know how to run `ccc logout` when done

---

**End of User Guide**

For technical details and architecture, see:
- `CLI_Authentication_Framework_v0.3_Architecture.md`

For installation instructions, see:
- `CCA-2/INSTALL.md`

**Questions?** Contact your administrator or check `ccc --help`
