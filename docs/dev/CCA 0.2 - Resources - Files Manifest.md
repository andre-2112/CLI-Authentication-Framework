# Files Manifest - CCA 0.2

**Version:** 0.2 (Cognito-based)
**Last Updated:** 2025-11-09

---

## Directory Structure

```
CCA-2/
├── ccc-cli/                          # CCC CLI Tool
│   ├── ccc.py                        # Main CLI script (563 lines)
│   ├── setup.py                      # Installation configuration
│   ├── requirements.txt              # Python dependencies (boto3>=1.26.0)
│   └── README.md                     # CLI documentation
│
├── docs/                             # Documentation
│   ├── CCA 0.2 - Cognito Design.md   # Architecture & design (1,820 lines)
│   ├── CCA 0.2 - Implementation Plan.md            # Step-by-step plan (1,500+ lines)
│   ├── CCA 0.2 - Password Security Considerations.md  # Password security
│   ├── CCA 0.2 - Implementation Changes Log.md     # This implementation log
│   ├── Addendum - AWS Resources Inventory - 0.2.md # Resource inventory
│   ├── Addendum - User Management Guide - 0.2.md   # Cognito user commands
│   └── Addendum - Files Manifest - 0.2.md         # This file
│
├── lambda/                           # Lambda Function
│   ├── lambda_function.py            # Registration/approval handler (687 lines)
│   └── requirements.txt              # Lambda dependencies (empty - boto3 included)
│
├── src/                              # Source/Scripts
│   └── (future deployment scripts)
│
└── tmp/                              # Temporary Files
    ├── cca-config.env                # All environment variables
    ├── registration.html             # Registration form (deployed to S3)
    ├── lambda-deployment.zip         # Lambda deployment package
    ├── kms-key.json                  # KMS key creation response
    ├── cognito-user-pool.json        # User Pool creation response
    ├── cognito-app-client.json       # App Client creation response
    ├── cognito-identity-pool.json    # Identity Pool creation response
    ├── iam-role.json                 # IAM role creation response
    ├── lambda-function.json          # Lambda function creation response
    ├── function-url.json             # Function URL creation response
    ├── trust-policy.json             # IAM trust policy (Cognito → Role)
    ├── permissions-policy.json       # IAM permissions policy (CLI access)
    ├── lambda-trust-policy.json      # Lambda execution trust policy
    ├── lambda-execution-policy.json  # Lambda execution permissions
    ├── lambda-execution-role.json    # Lambda role creation response
    ├── s3-public-policy.json         # S3 bucket public read policy
    └── secret-key.txt                # JWT secret key
```

---

## File Details

### CCC CLI Tool (`ccc-cli/`)

#### `ccc.py`
- **Purpose:** Main CLI tool for user authentication
- **Size:** 563 lines of Python
- **Key Features:**
  - USER_PASSWORD_AUTH authentication flow
  - Cognito token management
  - AWS credential exchange via Identity Pool
  - Credential caching in ~/.aws/credentials
  - Commands: configure, login, refresh, logout, whoami, version

#### `setup.py`
- **Purpose:** Python package installation configuration
- **Installation:** `pip3 install -e .`
- **Entry Point:** Creates `ccc` command

#### `requirements.txt`
- **Dependencies:** boto3>=1.26.0

#### `README.md`
- **Purpose:** CLI tool documentation
- **Contents:** Installation, usage, commands, troubleshooting

---

### Documentation (`docs/`)

#### `CCA 0.2 - Cognito Design.md`
- **Purpose:** Complete architectural design specification
- **Size:** 1,820 lines
- **Contents:**
  - System data flow diagrams
  - JWT token flow with KMS encryption
  - Architecture comparison (v0.1 vs v0.2)
  - Problems with v0.1
  - Security architecture (6 layers)
  - 7 possible security improvements with code

#### `CCA 0.2 - Implementation Plan.md`
- **Purpose:** Step-by-step implementation guide
- **Size:** 1,500+ lines
- **Contents:**
  - Phase 1-7 implementation steps
  - Complete bash commands for all resources
  - Testing procedures
  - Cleanup procedures
  - Rollback plan

#### `CCA 0.2 - Password Security Considerations.md`
- **Purpose:** Password security explanation
- **Contents:**
  - Why Cognito requires plaintext input
  - bcrypt hashing in Cognito
  - Brief plaintext moment (50-200ms)
  - Industry standard comparisons
  - Security best practices

#### `CCA 0.2 - Implementation Changes Log.md`
- **Purpose:** Complete record of all changes made
- **Size:** ~1,000 lines
- **Contents:**
  - Every AWS resource created
  - Code changes with examples
  - Configuration summary
  - Testing status
  - Rollback procedures

#### `Addendum - AWS Resources Inventory - 0.2.md`
- **Purpose:** Complete AWS resource inventory
- **Contents:**
  - All 6 main resources with full details
  - CLI commands for each resource
  - Complete cleanup script
  - Resource dependencies diagram

#### `Addendum - User Management Guide - 0.2.md`
- **Purpose:** Cognito user management commands
- **Contents:**
  - List, get, create, modify, delete users
  - Enable/disable users
  - Password management
  - Troubleshooting
  - v0.1 vs v0.2 command comparison

#### `Addendum - Files Manifest - 0.2.md`
- **Purpose:** This file - complete file structure documentation

---

### Lambda Function (`lambda/`)

#### `lambda_function.py`
- **Purpose:** Handle registration, approval, and user creation
- **Size:** 687 lines of Python
- **Key Changes from v0.1:**
  - Added password field validation
  - KMS encryption/decryption of passwords
  - Cognito API instead of Identity Center API
  - admin_set_user_password for permanent passwords
  - Enhanced logging with tags

**Endpoints:**
- `/register` - POST - User registration with password
- `/approve` - GET - Admin approval (creates Cognito user)
- `/deny` - GET - Admin denial

#### `requirements.txt`
- **Dependencies:** None (boto3 included in Lambda runtime)

---

### Temporary Files (`tmp/`)

#### `cca-config.env`
- **Purpose:** All environment variables for CCA 0.2
- **Contents:**
  ```bash
  export KMS_KEY_ID=3ec987ec-fbaf-4de9-bd39-9e1615976e08
  export KMS_KEY_ALIAS=alias/cca-jwt-encryption
  export USER_POOL_ID=us-east-1_rYTZnMwvc
  export APP_CLIENT_ID=1bga7o1j5vthc9gmfq7eeba3ti
  export IDENTITY_POOL_ID=us-east-1:0a656e9c-d356-4964-b6ba-610afb34cbb7
  export IAM_ROLE_ARN=arn:aws:iam::211050572089:role/CCA-Cognito-Auth-Role
  export LAMBDA_ROLE_ARN=arn:aws:iam::211050572089:role/CCA-Lambda-Execution-Role-v2
  export SECRET_KEY=5ab89f169f34cf50e27330b46ff69065b734cace7646a5241f93b9d25e776627
  export FROM_EMAIL="info@2112-lab.com"
  export ADMIN_EMAIL="info@2112-lab.com"
  export LAMBDA_URL=https://pli7xymprlva76biu3h6dyso4m0vpqqw.lambda-url.us-east-1.on.aws/
  export S3_BUCKET=cca-registration-v2-2025
  export REGISTRATION_URL=http://cca-registration-v2-2025.s3-website-us-east-1.amazonaws.com/registration.html
  ```

#### `registration.html`
- **Purpose:** User registration form with password field
- **Size:** 234 lines (11.3 KB)
- **Key Features:**
  - Password field with strength indicator
  - Password confirmation
  - Client-side validation
  - v0.2 badge
  - Visual step-by-step guidance

#### `lambda-deployment.zip`
- **Purpose:** Lambda deployment package
- **Contents:** lambda_function.py
- **Size:** 5,617 bytes

#### JSON Response Files
- **Purpose:** Store AWS CLI responses for reference
- **Files:**
  - `kms-key.json` - KMS key creation
  - `cognito-user-pool.json` - User Pool creation
  - `cognito-app-client.json` - App Client creation
  - `cognito-identity-pool.json` - Identity Pool creation
  - `iam-role.json` - IAM role creation
  - `lambda-execution-role.json` - Lambda role creation
  - `lambda-function.json` - Lambda function creation
  - `function-url.json` - Function URL creation

#### Policy Files
- **Purpose:** IAM and S3 policies
- **Files:**
  - `trust-policy.json` - Cognito → IAM role trust
  - `permissions-policy.json` - CLI access permissions
  - `lambda-trust-policy.json` - Lambda service trust
  - `lambda-execution-policy.json` - Lambda permissions
  - `s3-public-policy.json` - S3 public read policy

#### `secret-key.txt`
- **Purpose:** JWT signing secret (HMAC-SHA256)
- **Value:** 64-character hex string
- **Security:** Keep confidential, used in Lambda env vars

---

## File Size Summary

| Category | Files | Total Size | Lines of Code |
|----------|-------|------------|---------------|
| **CLI Tool** | 4 files | ~50 KB | 563 lines |
| **Lambda** | 2 files | ~25 KB | 687 lines |
| **Documentation** | 7 files | ~500 KB | ~8,000 lines |
| **Config/Temp** | 15+ files | ~50 KB | N/A |
| **Total** | ~28 files | ~625 KB | ~9,250 lines |

---

## Comparison: v0.1 vs v0.2 Files

| File Type | v0.1 | v0.2 | Change |
|-----------|------|------|--------|
| **CLI Tool** | 1 file (~300 lines) | 4 files (563 lines) | +263 lines (+87.7%) |
| **Lambda** | 1 file (609 lines) | 1 file (687 lines) | +78 lines (+12.8%) |
| **Registration Form** | 1 file (126 lines) | 1 file (234 lines) | +108 lines (+85.7%) |
| **Documentation** | 12 files | 7 files (v0.2 specific) | New architecture |
| **Config Files** | ~10 files | ~15 files | +5 files |

---

## Key Additions in 0.2

### New Files (Not in v0.1)
- `ccc-cli/ccc.py` - Complete rewrite for Cognito
- `CCA 0.2 - Cognito Design.md` - New architecture
- `CCA 0.2 - Implementation Plan.md` - Implementation guide
- `CCA 0.2 - Password Security Considerations.md` - Security explanation
- `CCA 0.2 - Implementation Changes Log.md` - Change tracking
- `Addendum - AWS Resources Inventory - 0.2.md` - Cognito resources
- `Addendum - User Management Guide - 0.2.md` - Cognito commands
- `tmp/kms-key.json` - KMS key (new resource)
- `tmp/cognito-*` files - Cognito resources

### Modified Files (from v0.1)
- `lambda/lambda_function.py` - Added password encryption/Cognito API
- `tmp/registration.html` - Added password fields
- `tmp/cca-config.env` - New environment variables

### Removed Files (from v0.1, not in v0.2)
- Identity Center configuration files
- SSO-related scripts
- Password setup portal (no longer needed)

---

## Deployment Files

### Files Deployed to AWS

| File | Deployed To | Purpose |
|------|-------------|---------|
| `lambda/lambda_function.py` | Lambda function `cca-registration-v2` | Registration/approval handler |
| `tmp/registration.html` | S3 bucket `cca-registration-v2-2025` | User registration form |

### Files for Local Installation

| File | Installation Method | Purpose |
|------|---------------------|---------|
| `ccc-cli/ccc.py` | `pip3 install -e ccc-cli/` | CLI tool |
| `ccc-cli/setup.py` | (used by pip) | Package configuration |

---

## File Usage Reference

### For Developers

**To understand the architecture:**
1. Read `docs/CCA 0.2 - Cognito Design.md`
2. Review `docs/CCA 0.2 - Implementation Changes Log.md`

**To implement changes:**
1. Follow `docs/CCA 0.2 - Implementation Plan.md`
2. Refer to `docs/Addendum - AWS Resources Inventory - 0.2.md`

**To manage users:**
1. Use `docs/Addendum - User Management Guide - 0.2.md`

### For Users

**To install CLI:**
```bash
cd CCA-2/ccc-cli
pip3 install -e .
```

**To configure CLI:**
```bash
ccc configure
# Use values from tmp/cca-config.env
```

**To register:**
Visit: `http://cca-registration-v2-2025.s3-website-us-east-1.amazonaws.com/registration.html`

---

## Configuration Reference

All configuration values are stored in `tmp/cca-config.env`. Source this file to set environment variables:

```bash
source tmp/cca-config.env
```

---

**Document Status:** ✅ Complete
**Last Updated:** 2025-11-09
