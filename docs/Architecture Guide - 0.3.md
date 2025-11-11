# CLI Authentication Framework v0.3 - Architectural Design

**Version**: 0.3
**Date**: November 10, 2025
**Status**: Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Component Architecture](#component-architecture)
4. [Authentication Flows](#authentication-flows)
5. [Registration Flows](#registration-flows)
6. [Password Management Flows](#password-management-flows)
7. [AWS Operations Flows](#aws-operations-flows)
8. [Security Architecture](#security-architecture)
9. [Data Flow Diagrams](#data-flow-diagrams)
10. [Deployment Architecture](#deployment-architecture)

---

## Overview

### Purpose

The CLI Authentication Framework provides secure, self-service command-line authentication for AWS resources using Amazon Cognito, with optional user names, comprehensive password management, and full AWS operations visibility.

### Key Characteristics

- **Authentication**: Password-based via Amazon Cognito User Pools
- **Authorization**: Temporary AWS credentials (60-minute sessions)
- **CLI-First**: Command-line interface with web fallback
- **Self-Service**: User registration, password management, approval workflow
- **Minimal Infrastructure**: 3 core AWS services
- **Audit Trail**: CloudTrail + CloudWatch Logs integration

---

## System Architecture

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         USER LAYER                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  CLI Tool    │  │ Web Browser  │  │  SDK Apps    │          │
│  │    (ccc)     │  │ (Reg Form)   │  │  (Python)    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼──────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌──────────────────────────────────────────────────────────────────┐
│                    AUTHENTICATION LAYER                          │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │           Amazon Cognito User Pools                        │ │
│  │  • Password-based authentication                           │ │
│  │  • User management (optional names)                        │ │
│  │  • Password policies & forgot password                     │ │
│  │  • Token generation (ID, Access, Refresh)                  │ │
│  └───────────────────────┬────────────────────────────────────┘ │
└──────────────────────────┼───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                    FEDERATION LAYER                              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │         Amazon Cognito Identity Pools                      │ │
│  │  • ID Token → AWS Credentials exchange                     │ │
│  │  • Temporary credentials (60 minutes)                      │ │
│  │  • IAM role assumption                                     │ │
│  └───────────────────────┬────────────────────────────────────┘ │
└──────────────────────────┼───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                       AWS SERVICES                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │    S3    │  │   EC2    │  │ Lambda   │  │   Logs   │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└──────────────────────────────────────────────────────────────────┘
          ▲                  ▲                  ▲
          │                  │                  │
          └──────────────────┴──────────────────┘
                    Authorized Access
           (via temporary IAM role credentials)
```

### Registration & Approval System

```
┌──────────────────────────────────────────────────────────────────┐
│                    REGISTRATION SYSTEM                           │
│                                                                  │
│  ┌───────────────┐                    ┌───────────────┐        │
│  │  CLI or Web   │─────Register───────▶│    Lambda     │        │
│  │   Frontend    │                    │   Function    │        │
│  └───────────────┘                    └───────┬───────┘        │
│                                                │                │
│                                                ▼                │
│                                       ┌────────────────┐        │
│                                       │  Encrypted JWT │        │
│                                       │  (Pending User)│        │
│                                       └────────┬───────┘        │
│                                                │                │
│                                                ▼                │
│                                       ┌────────────────┐        │
│                                       │  Admin Email   │        │
│                                       │  with Links    │        │
│                                       └───┬────────┬───┘        │
│                                           │        │            │
│                            ┌──────────────┘        └────────────┐
│                            │                                    │
│                            ▼                                    ▼
│                    ┌───────────────┐                  ┌─────────────┐
│                    │   Approve     │                  │    Deny     │
│                    │   (Lambda)    │                  │  (Lambda)   │
│                    └───────┬───────┘                  └──────┬──────┘
│                            │                                 │
│                            ▼                                 ▼
│                    ┌───────────────┐                  ┌─────────────┐
│                    │ Create User   │                  │   Delete    │
│                    │  in Cognito   │                  │    JWT      │
│                    └───────┬───────┘                  └─────────────┘
│                            │
│                            ▼
│                    ┌───────────────┐
│                    │ Welcome Email │
│                    │   to User     │
│                    └───────────────┘
└──────────────────────────────────────────────────────────────────┘
```

---

## Component Architecture

### CLI Tool Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       CLI Tool (ccc)                            │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    Command Layer                          │ │
│  │  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐      │ │
│  │  │cfg │ │reg │ │log │ │rfr │ │lgo │ │who │ │ver │ ...  │ │
│  │  └─┬──┘ └─┬──┘ └─┬──┘ └─┬──┘ └─┬──┘ └─┬──┘ └─┬──┘      │ │
│  └────┼──────┼──────┼──────┼──────┼──────┼──────┼────────────┘ │
│       │      │      │      │      │      │      │              │
│       └──────┴──────┴──────┴──────┴──────┴──────┘              │
│                            │                                    │
│  ┌────────────────────────┼────────────────────────────────┐  │
│  │                  SDK Layer                               │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │  │
│  │  │    Config    │  │     Auth     │  │  AWS Ops     │  │  │
│  │  │   Module     │  │   Module     │  │   Module     │  │  │
│  │  │              │  │              │  │              │  │  │
│  │  │ • Load/Save  │  │ • Cognito    │  │ • CloudTrail │  │  │
│  │  │ • Validate   │  │ • Creds      │  │ • Resources  │  │  │
│  │  │              │  │ • Refresh    │  │ • Permissions│  │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘ │
│                            │                                    │
│  ┌────────────────────────┼────────────────────────────────┐  │
│  │                  Client Libraries                        │  │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐       │  │
│  │  │ Boto3  │  │Request │  │Getpass │  │  JSON  │       │  │
│  │  └────────┘  └────────┘  └────────┘  └────────┘       │  │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### SDK Module Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      SDK Package (cca)                          │
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │  cca/__init__.py │  │   cca/config.py  │  │ cca/auth/    │ │
│  │                  │  │                  │  │              │ │
│  │  • Version       │  │  • load_config() │  │  • cognito.py│ │
│  │  • Exports       │  │  • save_config() │  │  • creds.py  │ │
│  │  • Public API    │  │  • Validation    │  │  • __init__  │ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
│                                                                 │
│  ┌──────────────────┐                                          │
│  │   cca/aws/       │                                          │
│  │                  │                                          │
│  │  • cloudtrail.py ├─ History tracking                       │
│  │  • resources.py  ├─ Resource listing                       │
│  │  • permissions.py├─ Permission inspection                  │
│  │  • __init__.py   │                                          │
│  └──────────────────┘                                          │
└─────────────────────────────────────────────────────────────────┘
```

### Lambda Function Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Lambda Function Handler                      │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │            HTTP Event Router                              │ │
│  │  ┌─────────────┬─────────────┬─────────────┐            │ │
│  │  │ /register   │  /approve   │   /deny     │            │ │
│  │  └──────┬──────┴──────┬──────┴──────┬──────┘            │ │
│  └─────────┼─────────────┼─────────────┼────────────────────┘ │
│            │             │             │                      │
│            ▼             ▼             ▼                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  Register   │  │  Approve    │  │    Deny     │          │
│  │  Handler    │  │  Handler    │  │   Handler   │          │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘          │
│         │                │                │                  │
│         ▼                ▼                ▼                  │
│  ┌────────────────────────────────────────────────────┐     │
│  │           Shared Utilities                         │     │
│  │  • JWT encryption/decryption                       │     │
│  │  • Email templates & sending                       │     │
│  │  • Cognito user creation                           │     │
│  │  • Display name helpers (optional names)           │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │           Environment Variables                    │     │
│  │  • USER_POOL_ID                                    │     │
│  │  • KMS_KEY_ID                                      │     │
│  │  • SECRET_KEY                                      │     │
│  │  • ADMIN_EMAIL                                     │     │
│  │  • FROM_EMAIL                                      │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Authentication Flows

### 1. Initial Login Flow

```
┌────────┐                                                    ┌────────┐
│  User  │                                                    │Cognito │
│  (CLI) │                                                    │  Pool  │
└───┬────┘                                                    └────┬───┘
    │                                                              │
    │ 1. ccc login                                                 │
    │────────────────────────────────────────────────────▶        │
    │                                                              │
    │ 2. Prompt: Email                                             │
    │◀────────────────────────────────────────────────────        │
    │                                                              │
    │ 3. Enter: user@example.com                                   │
    │────────────────────────────────────────────────────▶        │
    │                                                              │
    │ 4. Prompt: Password                                          │
    │◀────────────────────────────────────────────────────        │
    │                                                              │
    │ 5. Enter: ••••••••••                                         │
    │────────────────────────────────────────────────────▶        │
    │                                                              │
    │                        6. Authenticate (USER_PASSWORD_AUTH)  │
    │                        ─────────────────────────────────────▶│
    │                                                              │
    │                        7. Return Tokens                      │
    │                        ◀─────────────────────────────────────│
    │                           • ID Token                         │
    │                           • Access Token                     │
    │                           • Refresh Token                    │
    │                                                              │
┌───┴────┐                                                    ┌────┴───┐
│Identity│                                                    │AWS     │
│  Pool  │                                                    │  STS   │
└───┬────┘                                                    └────┬───┘
    │                                                              │
    │ 8. Exchange ID Token for AWS Credentials                     │
    │─────────────────────────────────────────────────────────────▶│
    │                                                              │
    │ 9. Return Temporary Credentials                              │
    │◀─────────────────────────────────────────────────────────────│
    │    • AccessKeyId (ASIA...)                                   │
    │    • SecretAccessKey                                         │
    │    • SessionToken                                            │
    │    • Expiration (60 minutes)                                 │
    │                                                              │
┌───┴────┐                                                         │
│  User  │                                                         │
│  (CLI) │                                                         │
└───┬────┘                                                         │
    │                                                              │
    │ 10. Save to ~/.aws/credentials                               │
    │     [cca]                                                    │
    │     aws_access_key_id = ASIA...                              │
    │     aws_secret_access_key = ...                              │
    │     aws_session_token = ...                                  │
    │                                                              │
    │ 11. Save tokens to ~/.ccc/config.json                        │
    │     { "tokens": { ... } }                                    │
    │                                                              │
    │ 12. Display: "Login successful!"                             │
    │                                                              │
    ▼                                                              │
[Ready to use AWS CLI]                                             │
```

### 2. Token Refresh Flow

```
┌────────┐                    ┌────────┐                    ┌────────┐
│  User  │                    │Cognito │                    │Identity│
│  (CLI) │                    │  Pool  │                    │  Pool  │
└───┬────┘                    └────┬───┘                    └────┬───┘
    │                              │                              │
    │ 1. ccc refresh               │                              │
    │─────────────────────▶        │                              │
    │                              │                              │
    │ 2. Read refresh token        │                              │
    │    from ~/.ccc/config.json   │                              │
    │                              │                              │
    │ 3. Refresh tokens            │                              │
    │──────────────────────────────▶│                              │
    │  (REFRESH_TOKEN_AUTH)        │                              │
    │                              │                              │
    │ 4. New ID + Access tokens    │                              │
    │◀──────────────────────────────│                              │
    │  (Refresh token reused)      │                              │
    │                              │                              │
    │ 5. Exchange for new AWS creds│                              │
    │──────────────────────────────────────────────────────────────▶│
    │                              │                              │
    │ 6. New temporary credentials │                              │
    │◀──────────────────────────────────────────────────────────────│
    │  (60 minutes)                │                              │
    │                              │                              │
    │ 7. Update ~/.aws/credentials │                              │
    │ 8. Update ~/.ccc/config.json │                              │
    │                              │                              │
    ▼                              │                              │
[Credentials refreshed]            │                              │
```

---

## Registration Flows

### 1. CLI Registration Flow (With Optional Names)

```
┌────────┐                  ┌────────┐                  ┌────────┐
│  User  │                  │ Lambda │                  │ Admin  │
│  (CLI) │                  │Function│                  │ Email  │
└───┬────┘                  └────┬───┘                  └────┬───┘
    │                            │                            │
    │ 1. ccc register            │                            │
    │───────────────────▶        │                            │
    │                            │                            │
    │ 2. Prompt: Email           │                            │
    │◀───────────────────        │                            │
    │                            │                            │
    │ 3. Enter: user@example.com │                            │
    │───────────────────▶        │                            │
    │                            │                            │
    │ 4. Prompt: First Name      │                            │
    │    (optional, press Enter) │                            │
    │◀───────────────────        │                            │
    │                            │                            │
    │ 5. Enter: John OR [Enter]  │                            │
    │───────────────────▶        │                            │
    │                            │                            │
    │ 6. Prompt: Last Name       │                            │
    │    (optional, press Enter) │                            │
    │◀───────────────────        │                            │
    │                            │                            │
    │ 7. Enter: Doe OR [Enter]   │                            │
    │───────────────────▶        │                            │
    │                            │                            │
    │ 8. Prompt: Password        │                            │
    │◀───────────────────        │                            │
    │                            │                            │
    │ 9. Enter: ••••••••         │                            │
    │───────────────────▶        │                            │
    │                            │                            │
    │ 10. Validate password      │                            │
    │     (8+ chars, upper,      │                            │
    │      lower, number, symbol)│                            │
    │                            │                            │
    │ 11. Prompt: Confirm        │                            │
    │◀───────────────────        │                            │
    │                            │                            │
    │ 12. Enter: ••••••••        │                            │
    │───────────────────▶        │                            │
    │                            │                            │
    │ 13. POST to Lambda         │                            │
    │────────────────────────────▶│                            │
    │    {                       │                            │
    │      email,                │                            │
    │      first_name (optional),│                            │
    │      last_name (optional), │                            │
    │      password              │                            │
    │    }                       │                            │
    │                            │                            │
    │                            │ 14. Encrypt password       │
    │                            │     (JWT with KMS)         │
    │                            │                            │
    │                            │ 15. Send approval email    │
    │                            │────────────────────────────▶│
    │                            │    With approve/deny links │
    │                            │    Display name fallback:  │
    │                            │    "John Doe" OR "user"    │
    │                            │                            │
    │ 16. Success response       │                            │
    │◀────────────────────────────│                            │
    │    "Registration submitted"│                            │
    │    "Pending approval"      │                            │
    │                            │                            │
    ▼                            │                            │
[Wait for approval]              │                            │
```

### 2. Admin Approval Flow

```
┌────────┐                  ┌────────┐                  ┌────────┐
│ Admin  │                  │ Lambda │                  │Cognito │
│ Email  │                  │Function│                  │  Pool  │
└───┬────┘                  └────┬───┘                  └────┬───┘
    │                            │                            │
    │ 1. Click "Approve" link    │                            │
    │────────────────────────────▶│                            │
    │   (includes encrypted JWT) │                            │
    │                            │                            │
    │                            │ 2. Decrypt JWT             │
    │                            │    (KMS key)               │
    │                            │    Extract:                │
    │                            │    • email                 │
    │                            │    • names (optional)      │
    │                            │    • password              │
    │                            │                            │
    │                            │ 3. Create user in Cognito  │
    │                            │────────────────────────────▶│
    │                            │    admin_create_user()     │
    │                            │    • email (required)      │
    │                            │    • names (if provided)   │
    │                            │    • email_verified: true  │
    │                            │                            │
    │                            │ 4. User created            │
    │                            │◀────────────────────────────│
    │                            │                            │
    │                            │ 5. Set password            │
    │                            │────────────────────────────▶│
    │                            │    admin_set_user_password()│
    │                            │    (permanent)             │
    │                            │                            │
    │                            │ 6. Password set            │
    │                            │◀────────────────────────────│
    │                            │                            │
    │ 7. Approval page (HTML)    │                            │
    │◀────────────────────────────│                            │
    │   "User approved!"         │                            │
    │                            │                            │
    │                            │ 8. Send welcome email      │
    │                            │    to user                 │
    │                            │    "Your account is ready" │
    │                            │    "Run: ccc login"        │
    │                            │                            │
    ▼                            │                            │
[User can now login]             │                            │
```

---

## Password Management Flows

### 1. Forgot Password Flow

```
┌────────┐                  ┌────────┐                  ┌────────┐
│  User  │                  │Cognito │                  │  Email │
│  (CLI) │                  │  Pool  │                  │        │
└───┬────┘                  └────┬───┘                  └────┬───┘
    │                            │                            │
    │ 1. ccc forgot-password     │                            │
    │───────────────────▶        │                            │
    │                            │                            │
    │ 2. Prompt: Email           │                            │
    │◀───────────────────        │                            │
    │                            │                            │
    │ 3. Enter: user@example.com │                            │
    │───────────────────▶        │                            │
    │                            │                            │
    │ 4. Request code            │                            │
    │────────────────────────────▶│                            │
    │    forgot_password()       │                            │
    │                            │                            │
    │                            │ 5. Send verification code  │
    │                            │────────────────────────────▶│
    │                            │    "Code: 123456"          │
    │                            │    (Expires in 24 hours)   │
    │                            │                            │
    │ 6. "Code sent to email"    │                            │
    │◀────────────────────────────│                            │
    │                            │                            │
    │ 7. Prompt: Verification Code│                           │
    │◀───────────────────        │                            │
    │                            │                            │
    │ 8. Enter: 123456           │                            │
    │───────────────────▶        │                            │
    │                            │                            │
    │ 9. Prompt: New Password    │                            │
    │◀───────────────────        │                            │
    │                            │                            │
    │ 10. Enter: ••••••••        │                            │
    │───────────────────▶        │                            │
    │                            │                            │
    │ 11. Validate password      │                            │
    │                            │                            │
    │ 12. Prompt: Confirm        │                            │
    │◀───────────────────        │                            │
    │                            │                            │
    │ 13. Enter: ••••••••        │                            │
    │───────────────────▶        │                            │
    │                            │                            │
    │ 14. Confirm password reset │                            │
    │────────────────────────────▶│                            │
    │    confirm_forgot_password()│                           │
    │    code + new password     │                            │
    │                            │                            │
    │ 15. "Password changed!"    │                            │
    │◀────────────────────────────│                            │
    │    "Run: ccc login"        │                            │
    │                            │                            │
    ▼                            │                            │
[Can login with new password]    │                            │
```

### 2. Change Password Flow (While Logged In)

```
┌────────┐                  ┌────────┐
│  User  │                  │Cognito │
│  (CLI) │                  │  Pool  │
└───┬────┘                  └────┬───┘
    │                            │
    │ 1. ccc change-password     │
    │───────────────────▶        │
    │                            │
    │ 2. Check if logged in      │
    │    (access token exists)   │
    │                            │
    │ 3. Prompt: Current Password│
    │◀───────────────────        │
    │                            │
    │ 4. Enter: ••••••••         │
    │───────────────────▶        │
    │                            │
    │ 5. Prompt: New Password    │
    │◀───────────────────        │
    │                            │
    │ 6. Enter: ••••••••         │
    │───────────────────▶        │
    │                            │
    │ 7. Validate password       │
    │                            │
    │ 8. Prompt: Confirm         │
    │◀───────────────────        │
    │                            │
    │ 9. Enter: ••••••••         │
    │───────────────────▶        │
    │                            │
    │ 10. Change password        │
    │────────────────────────────▶│
    │    change_password()       │
    │    access_token +          │
    │    old_password +          │
    │    new_password            │
    │                            │
    │ 11. Verify old password    │
    │     and set new password   │
    │                            │
    │ 12. "Password changed!"    │
    │◀────────────────────────────│
    │    "Session still valid"   │
    │                            │
    ▼                            │
[Continue using current session] │
```

---

## AWS Operations Flows

### 1. Resource Listing Flow

```
┌────────┐                  ┌────────┐                  ┌────────┐
│  User  │                  │   CLI  │                  │AWS API │
│        │                  │  (SDK) │                  │        │
└───┬────┘                  └────┬───┘                  └────┬───┘
    │                            │                            │
    │ 1. ccc resources           │                            │
    │───────────────────▶        │                            │
    │                            │                            │
    │                            │ 2. Load credentials        │
    │                            │    from ~/.aws/credentials │
    │                            │                            │
    │                            │ 3. Get caller identity     │
    │                            │────────────────────────────▶│
    │                            │    sts:GetCallerIdentity   │
    │                            │                            │
    │                            │ 4. Return user info        │
    │                            │◀────────────────────────────│
    │                            │    Account, ARN            │
    │                            │                            │
    │                            │ 5. List resources          │
    │                            │────────────────────────────▶│
    │                            │    tag:GetResources        │
    │                            │                            │
    │                            │ 6. Return resources        │
    │                            │◀────────────────────────────│
    │                            │    {S3, EC2, Lambda, ...}  │
    │                            │                            │
    │                            │ 7. Format by resource type │
    │                            │    Group by service        │
    │                            │    Apply limits (--limit)  │
    │                            │                            │
    │ 8. Display resources       │                            │
    │◀───────────────────        │                            │
    │    93 resources            │                            │
    │    26 resource types       │                            │
    │    S3, EC2, Lambda, etc.   │                            │
    │                            │                            │
    ▼                            │                            │
```

### 2. Activity History Flow

```
┌────────┐                  ┌────────┐                  ┌────────┐
│  User  │                  │   CLI  │                  │AWS API │
│        │                  │  (SDK) │                  │        │
└───┬────┘                  └────┬───┘                  └────┬───┘
    │                            │                            │
    │ 1. ccc history --days 7    │                            │
    │───────────────────▶        │                            │
    │                            │                            │
    │                            │ 2. Get user ARN            │
    │                            │────────────────────────────▶│
    │                            │    sts:GetCallerIdentity   │
    │                            │                            │
    │                            │ 3. Return ARN              │
    │                            │◀────────────────────────────│
    │                            │    Extract username        │
    │                            │                            │
    │                            │ 4. Try CloudWatch Logs     │
    │                            │────────────────────────────▶│
    │                            │    logs:FilterLogEvents    │
    │                            │    Filter by username      │
    │                            │    Last 7 days             │
    │                            │                            │
    │                            │ 5. Return events (or empty)│
    │                            │◀────────────────────────────│
    │                            │                            │
    │                            │ 6. If empty, try CloudTrail│
    │                            │────────────────────────────▶│
    │                            │    cloudtrail:LookupEvents │
    │                            │                            │
    │                            │ 7. Return events           │
    │                            │◀────────────────────────────│
    │                            │                            │
    │                            │ 8. Format events           │
    │                            │    Timestamp, Service,     │
    │                            │    Action, Resource        │
    │                            │                            │
    │ 9. Display history         │                            │
    │◀───────────────────        │                            │
    │    15 events found         │                            │
    │    Source: CloudWatch Logs │                            │
    │                            │                            │
    ▼                            │                            │
```

---

## Security Architecture

### Authentication Security Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                     SECURITY LAYERS                             │
│                                                                 │
│  Layer 1: Password Security                                     │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  • 8+ characters minimum                                  │ │
│  │  • Uppercase + lowercase required                         │ │
│  │  • Numbers + special characters required                  │ │
│  │  • Never stored in plaintext                              │ │
│  │  • JWT encryption for pending registrations               │ │
│  └───────────────────────────────────────────────────────────┘ │
│                          ▼                                      │
│  Layer 2: Cognito Authentication                                │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  • Secure password hashing (bcrypt)                       │ │
│  │  • Rate limiting on login attempts                        │ │
│  │  • Account lockout after failures                         │ │
│  │  • MFA support (optional)                                 │ │
│  │  • Session token generation                               │ │
│  └───────────────────────────────────────────────────────────┘ │
│                          ▼                                      │
│  Layer 3: Temporary Credentials                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  • 60-minute session duration                             │ │
│  │  • Temporary keys (ASIA... not AKIA...)                   │ │
│  │  • Auto-expiration                                        │ │
│  │  • Refresh token valid for 30 days                        │ │
│  └───────────────────────────────────────────────────────────┘ │
│                          ▼                                      │
│  Layer 4: IAM Role Permissions                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  • Explicit deny for console access                       │ │
│  │  • Least privilege principle                              │ │
│  │  • Resource-level permissions                             │ │
│  │  • Action-level restrictions                              │ │
│  └───────────────────────────────────────────────────────────┘ │
│                          ▼                                      │
│  Layer 5: Audit Trail                                           │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  • CloudTrail event logging                               │ │
│  │  • CloudWatch Logs aggregation                            │ │
│  │  • User activity tracking                                 │ │
│  │  • Admin visibility via ccc history                       │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow Security

```
┌─────────────────────────────────────────────────────────────────┐
│                   DATA PROTECTION                               │
│                                                                 │
│  Passwords in Transit:                                          │
│  ┌───────────┐   HTTPS   ┌───────────┐   HTTPS   ┌──────────┐ │
│  │    CLI    │─────────▶│  Lambda   │─────────▶│ Cognito  │ │
│  │           │  TLS 1.2+ │  Function │  TLS 1.2+ │   API    │ │
│  └───────────┘           └───────────┘           └──────────┘ │
│                                                                 │
│  Passwords at Rest (Pending Approval):                          │
│  ┌───────────┐           ┌───────────┐           ┌──────────┐ │
│  │  Password │─Encrypt──▶│    JWT    │─KMS Key──▶│ Email    │ │
│  │ Plaintext │  AES-256  │ (Temporary)│  Wrapped  │ (Admin)  │ │
│  └───────────┘           └───────────┘           └──────────┘ │
│                                                                 │
│  AWS Credentials Storage:                                       │
│  ┌───────────┐           ┌───────────┐                         │
│  │Credentials│──Write───▶│  ~/.aws/  │                         │
│  │Temporary  │ chmod 600 │credentials│                         │
│  │  (60 min) │           │  (Local)  │                         │
│  └───────────┘           └───────────┘                         │
│                                                                 │
│  Tokens Storage:                                                │
│  ┌───────────┐           ┌───────────┐                         │
│  │  Tokens   │──Write───▶│  ~/.ccc/  │                         │
│  │ ID/Access │ chmod 600 │config.json│                         │
│  │  Refresh  │           │  (Local)  │                         │
│  └───────────┘           └───────────┘                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Deployment Architecture

### AWS Infrastructure

```
┌─────────────────────────────────────────────────────────────────┐
│                       AWS ACCOUNT                               │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                 Cognito User Pool                        │  │
│  │  • User database                                         │  │
│  │  • Password policies                                     │  │
│  │  • Token generation                                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │               Cognito Identity Pool                      │  │
│  │  • Federation with User Pool                             │  │
│  │  • IAM role assumption                                   │  │
│  │  • Temporary credential generation                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │               Lambda Function                            │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  Function: cca-registration-v2                     │  │  │
│  │  │  Runtime: Python 3.12                              │  │  │
│  │  │  Memory: 256 MB                                    │  │  │
│  │  │  Timeout: 30 seconds                               │  │  │
│  │  │  Function URL: HTTPS (public)                      │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  Environment Variables:                            │  │  │
│  │  │  • USER_POOL_ID                                    │  │  │
│  │  │  • KMS_KEY_ID                                      │  │  │
│  │  │  • SECRET_KEY                                      │  │  │
│  │  │  • ADMIN_EMAIL                                     │  │  │
│  │  │  • FROM_EMAIL                                      │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  IAM Role: CCA-Lambda-Execution-Role-v2           │  │  │
│  │  │  • Cognito: CreateUser, SetPassword               │  │  │
│  │  │  • SES: SendEmail                                  │  │  │
│  │  │  • KMS: Decrypt                                    │  │  │
│  │  │  • CloudWatch: PutLogs                             │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    S3 Bucket                             │  │
│  │  • Static website hosting                                │  │
│  │  • registration.html (public read)                       │  │
│  │  • Bucket: cca-registration-v2-2025                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  IAM Role                                │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  Role: CCA-Cognito-Auth-Role                       │  │  │
│  │  │  • Trust: Cognito Identity Pool                    │  │  │
│  │  │  • Assumed by: Authenticated users                 │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  Permissions:                                      │  │  │
│  │  │  • S3: Full access                                 │  │  │
│  │  │  • EC2: Describe, Get                              │  │  │
│  │  │  • Lambda: List, Get                               │  │  │
│  │  │  • Logs: Describe, Get, Filter                     │  │  │
│  │  │  • IAM: Get role info                              │  │  │
│  │  │  • STS: GetCallerIdentity                          │  │  │
│  │  │  • Tags: GetResources                              │  │  │
│  │  │  • CloudTrail: LookupEvents                        │  │  │
│  │  │  • DENY: Console access                            │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                CloudWatch Logs                           │  │
│  │  • Lambda function logs                                  │  │
│  │  • VPC Flow Logs (optional)                              │  │
│  │  • Used by: ccc history command                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  CloudTrail                              │  │
│  │  • API call logging                                      │  │
│  │  • User activity tracking                                │  │
│  │  • Used by: ccc history command                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    KMS Key                               │  │
│  │  • JWT password encryption                               │  │
│  │  • Used by Lambda function                               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    SES                                   │  │
│  │  • Email sending                                         │  │
│  │  • Verified identity: info@2112-lab.com                  │  │
│  │  • Used by Lambda for notifications                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Client Installation

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER WORKSTATION                             │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                Python Environment                        │  │
│  │  • Python 3.8+                                           │  │
│  │  • pip                                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          │                                      │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  CCA SDK Package                         │  │
│  │  • Install: pip3 install -e .                            │  │
│  │  • Location: ccc-cli/                                    │  │
│  │  • Modules: cca.auth, cca.aws, cca.config               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          │                                      │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    CLI Command                           │  │
│  │  • Binary: ccc                                           │  │
│  │  • Location: ~/.local/bin/ccc (Linux/Mac)                │  │
│  │            or %APPDATA%\\Scripts\\ccc (Windows)          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          │                                      │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Configuration Files                         │  │
│  │  ~/.ccc/config.json:                                     │  │
│  │  • user_pool_id                                          │  │
│  │  • app_client_id                                         │  │
│  │  • identity_pool_id                                      │  │
│  │  • region                                                │  │
│  │  • profile                                               │  │
│  │  • lambda_url                                            │  │
│  │  • tokens (after login)                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          │                                      │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              AWS Credentials File                        │  │
│  │  ~/.aws/credentials:                                     │  │
│  │  [cca]                                                   │  │
│  │  aws_access_key_id = ASIA...                             │  │
│  │  aws_secret_access_key = ...                             │  │
│  │  aws_session_token = ...                                 │  │
│  │  # expires_at = 2025-11-10T18:30:00Z                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Appendix: Supported Commands

| Command | Purpose | Authentication Required |
|---------|---------|------------------------|
| `ccc configure` | Configure CLI settings | No |
| `ccc register` | Register new user (CLI) | No |
| `ccc login` | Authenticate and get credentials | No |
| `ccc refresh` | Refresh expired credentials | Yes (refresh token) |
| `ccc logout` | Clear credentials and tokens | No |
| `ccc forgot-password` | Reset password via email | No |
| `ccc change-password` | Change password | Yes (access token) |
| `ccc whoami` | Display user information | Yes |
| `ccc version` | Display CLI version | No |
| `ccc history` | View operation history | Yes |
| `ccc resources` | List AWS resources | Yes |
| `ccc permissions` | View IAM permissions | Yes |

---

**Document Version**: 1.0
**Framework Version**: 0.3
**Last Updated**: November 10, 2025
