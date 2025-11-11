# CCA 0.2 - CCC CLI Configuration Parameters

**Version:** 0.2 (Cognito-based)
**Last Updated:** 2025-11-09
**Purpose:** Reference guide for configuring the CCC CLI tool

---

## CCC Configure Parameters (CCA 0.2)

```bash
ccc configure
```

**When prompted, enter:**

| Parameter | Value |
|-----------|-------|
| **Cognito User Pool ID** | `us-east-1_rYTZnMwvc` |
| **Cognito App Client ID** | `1bga7o1j5vthc9gmfq7eeba3ti` |
| **Cognito Identity Pool ID** | `us-east-1:0a656e9c-d356-4964-b6ba-610afb34cbb7` |
| **AWS Region** | `us-east-1` |
| **AWS Profile Name** | `cca` (or press Enter for default) |

---

## Example Configuration Session

```bash
$ ccc configure
=== CCC CLI Configuration (v0.2 - Cognito) ===

Cognito User Pool ID []: us-east-1_rYTZnMwvc
Cognito App Client ID []: 1bga7o1j5vthc9gmfq7eeba3ti
Cognito Identity Pool ID []: us-east-1:0a656e9c-d356-4964-b6ba-610afb34cbb7
AWS Region [us-east-1]: us-east-1
AWS Profile Name [cca]: cca

[✓] Configuration saved to /home/user/.ccc/config.json

[✓] Configuration complete!

You can now run: ccc login
```

---

## Quick Copy-Paste Format

```
User Pool ID: us-east-1_rYTZnMwvc
App Client ID: 1bga7o1j5vthc9gmfq7eeba3ti
Identity Pool ID: us-east-1:0a656e9c-d356-4964-b6ba-610afb34cbb7
Region: us-east-1
Profile: cca
```

---

## Configuration File Location

After running `ccc configure`, the configuration is saved to:

**Linux/Mac:**
```
~/.ccc/config.json
```

**Windows:**
```
C:\Users\<USERNAME>\.ccc\config.json
```

---

## Configuration File Format

```json
{
  "user_pool_id": "us-east-1_rYTZnMwvc",
  "app_client_id": "1bga7o1j5vthc9gmfq7eeba3ti",
  "identity_pool_id": "us-east-1:0a656e9c-d356-4964-b6ba-610afb34cbb7",
  "region": "us-east-1",
  "profile": "cca"
}
```

---

## Alternative: Get Values from Environment File

All these values are stored in the deployment environment file:

```bash
# View all configuration values
cat CCA-2/tmp/cca-config.env
```

Or source them directly:

```bash
# Load environment variables
source CCA-2/tmp/cca-config.env

# Display configuration values
echo "User Pool ID: $USER_POOL_ID"
echo "App Client ID: $APP_CLIENT_ID"
echo "Identity Pool ID: $IDENTITY_POOL_ID"
```

---

## Verification

After configuration, verify the settings:

```bash
# Check configuration file
cat ~/.ccc/config.json

# Or use ccc to verify (after first login)
ccc whoami
```

---

## Next Steps

After configuring, proceed to login:

```bash
ccc login
```

You'll be prompted for:
- **Email:** Your registered email address
- **Password:** The password you set during registration

---

## Reconfiguration

To change configuration values, simply run `ccc configure` again. The current values will be shown in brackets `[current_value]`, and you can:
- Press Enter to keep the current value
- Type a new value to change it

Example:
```bash
$ ccc configure
Cognito User Pool ID [us-east-1_rYTZnMwvc]: ← Press Enter to keep
Cognito App Client ID [1bga7o1j5vthc9gmfq7eeba3ti]: ← Press Enter to keep
...
```

---

## Troubleshooting

### Error: "Not configured. Run 'ccc configure' first"

**Cause:** Configuration file doesn't exist or is invalid

**Solution:**
```bash
ccc configure
# Enter all required values
```

### Error: "User Pool ID is required"

**Cause:** User Pool ID was not provided during configuration

**Solution:** Run `ccc configure` again and ensure you enter the User Pool ID:
```
us-east-1_rYTZnMwvc
```

### Error: "App Client ID is required"

**Cause:** App Client ID was not provided during configuration

**Solution:** Run `ccc configure` again and ensure you enter the App Client ID:
```
1bga7o1j5vthc9gmfq7eeba3ti
```

### Error: "Identity Pool ID is required"

**Cause:** Identity Pool ID was not provided during configuration

**Solution:** Run `ccc configure` again and ensure you enter the Identity Pool ID:
```
us-east-1:0a656e9c-d356-4964-b6ba-610afb34cbb7
```

---

## Resource ARNs (For Reference)

| Resource | ARN |
|----------|-----|
| **User Pool** | `arn:aws:cognito-idp:us-east-1:211050572089:userpool/us-east-1_rYTZnMwvc` |
| **Identity Pool** | `arn:aws:cognito-identity:us-east-1:211050572089:identitypool/us-east-1:0a656e9c-d356-4964-b6ba-610afb34cbb7` |
| **IAM Role** | `arn:aws:iam::211050572089:role/CCA-Cognito-Auth-Role` |

---

## Administrator Commands

### Get Current Configuration Values (AWS CLI)

```bash
# Describe User Pool
aws cognito-idp describe-user-pool \
  --user-pool-id us-east-1_rYTZnMwvc \
  --region us-east-1

# Describe App Client
aws cognito-idp describe-user-pool-client \
  --user-pool-id us-east-1_rYTZnMwvc \
  --client-id 1bga7o1j5vthc9gmfq7eeba3ti \
  --region us-east-1

# Describe Identity Pool
aws cognito-identity describe-identity-pool \
  --identity-pool-id us-east-1:0a656e9c-d356-4964-b6ba-610afb34cbb7 \
  --region us-east-1
```

---

## Complete User Setup Flow

### Step 1: Install CCC CLI

```bash
cd CCA-2/ccc-cli
pip3 install -e .
```

### Step 2: Configure

```bash
ccc configure
```

Enter the values from the table at the top of this document.

### Step 3: Login

```bash
ccc login
```

Enter your email and password.

### Step 4: Verify

```bash
ccc whoami
```

### Step 5: Use AWS CLI

```bash
aws --profile cca s3 ls
```

Or:

```bash
export AWS_PROFILE=cca
aws s3 ls
```

---

## Related Documentation

- **Installation Guide:** `CCA-2/ccc-cli/README.md`
- **User Management:** `docs/Addendum - User Management Guide - 0.2.md`
- **AWS Resources:** `docs/Addendum - AWS Resources Inventory - 0.2.md`
- **Security Model:** `docs/CCA 0.2 - AWS Credentials Security Considerations.md`

---

**Document Status:** ✅ Complete
**Last Updated:** 2025-11-09
**Maintained By:** CCA Team
