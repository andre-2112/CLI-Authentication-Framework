# CLI Authentication Framework - Installation Guide

Complete installation instructions for the CLI Authentication Framework SDK and CLI tool.

**Version**: 0.3.0
**Last Updated**: November 10, 2025

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation Methods](#installation-methods)
3. [Configuration](#configuration)
4. [Verification](#verification)
5. [Troubleshooting](#troubleshooting)
6. [Upgrading](#upgrading)
7. [Uninstallation](#uninstallation)

---

## Prerequisites

### System Requirements

- **Operating System**: Windows, macOS, or Linux
- **Python**: 3.8 or higher
- **pip**: Latest version recommended
- **Internet Connection**: Required for AWS API calls

### Check Python Version

```bash
python3 --version
# Should show Python 3.8.0 or higher
```

If Python is not installed or version is too old:
- **Windows**: Download from https://www.python.org/downloads/
- **macOS**: `brew install python3` or download from python.org
- **Linux**: `sudo apt-get install python3` (Ubuntu/Debian) or `sudo yum install python3` (RHEL/CentOS)

### Check pip Version

```bash
pip3 --version
# Should show pip version and Python 3.x location
```

If pip is not installed:
```bash
python3 -m ensurepip --upgrade
```

---

## Installation Methods

### Method 1: Install from Source (Recommended for Development)

This method installs the CCA SDK in "editable" mode, allowing you to modify the source code.

#### Step 1: Clone the Repository

```bash
# Using HTTPS
git clone https://github.com/andre-2112/CLI-Authentication-Framework.git
cd CLI-Authentication-Framework/ccc-cli

# Or using SSH
git clone git@github.com:andre-2112/CLI-Authentication-Framework.git
cd CLI-Authentication-Framework/ccc-cli
```

#### Step 2: Install in Editable Mode

```bash
pip3 install -e .
```

**What this does**:
- Installs the `cca` SDK package
- Installs the `ccc` CLI command
- Links to source directory (changes to code take effect immediately)
- Installs dependencies (boto3)

#### Step 3: Verify Installation

```bash
ccc version
# Output: CCC CLI v0.3.0 (Cognito)
```

---

### Method 2: Install from PyPI (When Published)

Once the package is published to PyPI, you can install it directly:

```bash
pip3 install cca-sdk
```

This installs the latest stable version from the Python Package Index.

---

### Method 3: Install from Wheel File

If you have a pre-built wheel file:

```bash
pip3 install cca_sdk-0.2.0-py3-none-any.whl
```

---

### Method 4: Install for Current User Only

If you don't have system-wide pip permissions:

```bash
pip3 install --user -e .
```

The `ccc` command will be installed to `~/.local/bin/` (Linux/macOS) or `%APPDATA%\Python\Scripts\` (Windows).

**Add to PATH** (if needed):

**Linux/macOS**:
```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

**Windows** (Git Bash):
```bash
echo 'export PATH="$APPDATA/Python/Python313/Scripts:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

---

## Configuration

After installation, you need to configure the CLI with your Cognito settings.

### Step 1: Obtain Cognito Configuration

Contact your CCA administrator for:
- **User Pool ID**: `us-east-1_XXXXXXXXX`
- **App Client ID**: `xxxxxxxxxxxxxxxxxxxxxxxxxxxx`
- **Identity Pool ID**: `us-east-1:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
- **AWS Region**: `us-east-1` (or your region)

### Step 2: Run Configuration Command

```bash
ccc configure
```

You'll be prompted for each value:

```
=== CCC CLI Configuration (v0.2 - Cognito) ===

Cognito User Pool ID []: us-east-1_iMy46bnz6
Cognito App Client ID []: 347g0jncdadgjqigz9ch34gZna
Cognito Identity Pool ID []: us-east-1:c7e5a1a1-77e7-422a-a67e-b44f05d4b4b4
AWS Region [us-east-1]: us-east-1
AWS Profile Name [cca]: cca

[OK] Configuration saved to /home/user/.ccc/config.json

[OK] Configuration complete!

You can now run: ccc login
```

### Step 2b: Add Lambda URL (Optional - Required for Registration)

If you want to use the `ccc register` command for CLI-based registration, you need to manually add the Lambda URL to your config file:

1. Open `~/.ccc/config.json` in a text editor
2. Add the `lambda_url` field (get this from your administrator):

```json
{
  "user_pool_id": "us-east-1_XXXXXXXXX",
  "app_client_id": "xxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "identity_pool_id": "us-east-1:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "region": "us-east-1",
  "profile": "cca",
  "lambda_url": "https://xxxxx.lambda-url.us-east-1.on.aws/"
}
```

**Note**: The Lambda URL is only needed if you want to register new users via CLI (`ccc register`). You can still use the web registration form without this.

### Step 3: Verify Configuration

```bash
cat ~/.ccc/config.json
```

Should show:
```json
{
  "user_pool_id": "us-east-1_XXXXXXXXX",
  "app_client_id": "xxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "identity_pool_id": "us-east-1:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "region": "us-east-1",
  "profile": "cca"
}
```

---

## Verification

### Test CLI Installation

```bash
# Check version
ccc version

# Check help
ccc --help

# Check configuration
ccc whoami
# Should show "Not logged in" if you haven't logged in yet
```

### Test SDK Installation

```bash
python3 -c "from cca import CognitoAuthenticator; print('SDK import successful')"
```

Should print: `SDK import successful`

### Test Full Authentication Flow

```bash
# Login with your credentials
ccc login
# Enter email and password when prompted

# Verify login
ccc whoami
# Should show your email, region, and AWS identity

# Test AWS CLI integration
aws --profile cca sts get-caller-identity
# Should show your AWS account info
```

---

## Troubleshooting

### Issue 1: "command not found: ccc"

**Cause**: The installation directory is not in your PATH.

**Solution**:

1. Find where pip installed the command:
```bash
pip3 show -f cca-sdk | grep "Location:"
```

2. Check if the bin directory is in PATH:
```bash
echo $PATH | grep -o "[^:]*bin[^:]*"
```

3. Add to PATH (Linux/macOS):
```bash
export PATH="$HOME/.local/bin:$PATH"
```

4. Add to PATH (Windows Git Bash):
```bash
export PATH="$APPDATA/Python/Python313/Scripts:$PATH"
```

5. Make permanent by adding to `~/.bashrc` or `~/.bash_profile`

---

### Issue 2: "ModuleNotFoundError: No module named 'cca'"

**Cause**: Package not installed or installed in different Python environment.

**Solution**:

1. Check which Python you're using:
```bash
which python3
python3 --version
```

2. Check which pip you're using:
```bash
which pip3
```

3. Ensure they match (should be in same directory or environment)

4. Reinstall with explicit Python:
```bash
python3 -m pip install -e .
```

---

### Issue 3: "boto3 not found" or ImportError

**Cause**: Dependencies not installed.

**Solution**:

```bash
pip3 install boto3>=1.26.0
```

Or reinstall the package:
```bash
pip3 install --force-reinstall -e .
```

---

### Issue 4: Permission Denied Errors

**Cause**: Insufficient permissions to install system-wide.

**Solution 1**: Install for current user only:
```bash
pip3 install --user -e .
```

**Solution 2**: Use virtual environment (recommended):
```bash
python3 -m venv cca-env
source cca-env/bin/activate  # Linux/macOS
# or
source cca-env/Scripts/activate  # Windows Git Bash

pip3 install -e .
```

---

### Issue 5: "Not configured" Error

**Cause**: Configuration not set up or corrupted.

**Solution**:
```bash
# Remove old config
rm ~/.ccc/config.json

# Reconfigure
ccc configure
```

---

### Issue 6: SSL Certificate Errors

**Cause**: Corporate proxy or firewall blocking AWS APIs.

**Solution**:

1. Set proxy environment variables:
```bash
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080
```

2. Configure AWS CLI to use proxy:
```bash
aws configure set default.proxy http://proxy.company.com:8080
```

3. If using self-signed certificates:
```bash
export AWS_CA_BUNDLE=/path/to/ca-bundle.crt
```

---

### Issue 7: Windows Path Conversion Issues

**Cause**: Git Bash converts Unix paths to Windows paths.

**Solution**: Use `MSYS_NO_PATHCONV=1` prefix:
```bash
MSYS_NO_PATHCONV=1 ccc configure
```

Or set permanently:
```bash
echo 'export MSYS_NO_PATHCONV=1' >> ~/.bashrc
source ~/.bashrc
```

---

## Upgrading

### Upgrade from Git Repository

```bash
cd CLI-Authentication-Framework/ccc-cli
git pull origin master
pip3 install --upgrade -e .
```

### Upgrade from PyPI (when available)

```bash
pip3 install --upgrade cca-sdk
```

### Check Installed Version

```bash
ccc version
pip3 show cca-sdk
```

---

## Uninstallation

### Remove CCA SDK

```bash
pip3 uninstall cca-sdk
```

### Remove Configuration Files

```bash
# Remove CCA configuration
rm -rf ~/.ccc/

# Remove AWS credentials profile (optional)
# Edit ~/.aws/credentials and remove [cca] section
```

### Remove from PATH

Remove the PATH export line from `~/.bashrc` or `~/.bash_profile`.

---

## Advanced Installation

### Virtual Environment (Recommended for Development)

```bash
# Create virtual environment
python3 -m venv cca-dev
source cca-dev/bin/activate

# Install in virtual environment
cd cca/ccc-cli
pip3 install -e .

# Use CLI
ccc version

# Deactivate when done
deactivate
```

### Docker Container

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy CCA code
COPY ccc-cli /app/ccc-cli

# Install
RUN cd ccc-cli && pip3 install -e .

# Set up entry point
ENTRYPOINT ["ccc"]
CMD ["--help"]
```

Build and run:
```bash
docker build -t cca-cli .
docker run -it cca-cli version
```

### Install Multiple Versions

Use virtual environments or specify install location:

```bash
# Version 1
python3 -m venv cca-v1
source cca-v1/bin/activate
cd cca-v1-code && pip3 install -e .

# Version 2
python3 -m venv cca-v2
source cca-v2/bin/activate
cd cca-v2-code && pip3 install -e .
```

---

## Post-Installation

### Register as a User

1. Go to the registration URL provided by your administrator:
   ```
   http://cca-registration-XXXXX.s3-website-us-east-1.amazonaws.com/registration.html
   ```

2. Fill in the registration form:
   - Email address
   - First name
   - Last name
   - Password (8+ characters)

3. Submit and wait for approval (usually within 24 hours)

4. Once approved, you'll receive a confirmation email

5. Login:
   ```bash
   ccc login
   ```

### First Login

```bash
# Login
ccc login
# Enter: your email
# Enter: your password

# Verify
ccc whoami

# Test AWS access
aws --profile cca sts get-caller-identity
```

### Recommended Next Steps

1. **Set Default Profile** (optional):
   ```bash
   export AWS_PROFILE=cca
   echo 'export AWS_PROFILE=cca' >> ~/.bashrc
   ```

2. **Test New Commands** (v0.2.3):
   ```bash
   # Test password management
   ccc forgot-password    # Reset password via email
   ccc change-password    # Change password (requires login)

   # Test CLI registration (requires lambda_url in config)
   ccc register          # Register new user via CLI
   ```

3. **Test History Command**:
   ```bash
   ccc history --days 7
   ```

4. **View Permissions**:
   ```bash
   ccc permissions
   ```

5. **Read Documentation**:
   - [SDK Integration Guide](../docs/CCA%200.2%20-%20SDK%20Integration%20Guide.md)
   - [Hybrid CloudTrail Implementation](../docs/CCA%200.2%20-%20Hybrid%20CloudTrail%20Implementation.md)
   - [Test Report](../docs/CCA_0.2.3_Test_Report.md)

---

## Platform-Specific Notes

### Windows

- Use Git Bash or PowerShell
- Path separators: Use forward slashes (`/`) or escape backslashes (`\\`)
- Set `MSYS_NO_PATHCONV=1` for Git Bash
- Python may be installed as `python` instead of `python3`

### macOS

- May need to use `python3` explicitly
- HomeBrew installation recommended for Python
- XCode Command Line Tools may be required

### Linux

- Different distributions have different package managers
- May need `python3-pip` package installed separately
- Check if `~/.local/bin` is in PATH

---

## Getting Help

If you encounter issues not covered here:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review the [README.md](README.md)
3. Check documentation in `/docs` directory
4. Contact your administrator
5. Open an issue: https://github.com/andre-2112/CLI-Authentication-Framework/issues
6. Email: info@2112-lab.com

---

## Summary of Installation Commands

**Quick Install (Most Users)**:
```bash
git clone https://github.com/andre-2112/CLI-Authentication-Framework.git
cd CLI-Authentication-Framework/ccc-cli
pip3 install -e .
ccc configure
ccc login
```

**With Virtual Environment (Recommended)**:
```bash
python3 -m venv cca-env
source cca-env/bin/activate
git clone https://github.com/andre-2112/CLI-Authentication-Framework.git
cd CLI-Authentication-Framework/ccc-cli
pip3 install -e .
ccc configure
ccc login
```

---

**Installation Guide Version**: 1.2
**Last Updated**: November 10, 2025
**Framework Version**: 0.3.0
