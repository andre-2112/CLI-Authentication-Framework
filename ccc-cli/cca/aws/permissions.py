"""
AWS Permissions Operations
Provides functions to inspect user permissions and test common AWS actions.
"""

import json
from botocore.exceptions import ClientError, NoCredentialsError


def get_user_permissions(session, verbose=False):
    """
    Get information about user's AWS permissions

    Args:
        session: boto3 Session object
        verbose: Show detailed policy documents

    Returns:
        dict: {
            'arn': str,
            'account': str,
            'user_id': str,
            'role_name': str (if using assumed role),
            'session_name': str (if using assumed role),
            'role_info': dict (if available),
            'attached_policies': list,
            'inline_policies': list,
            'error': str (if error occurred)
        }
    """
    try:
        sts = session.client('sts')
        iam = session.client('iam')

        # Get caller identity
        identity = sts.get_caller_identity()
        arn = identity['Arn']

        result = {
            'arn': arn,
            'account': identity['Account'],
            'user_id': identity['UserId']
        }

        # Determine if using assumed role
        if ':assumed-role/' in arn:
            role_name = arn.split('/')[-2]
            session_name = arn.split('/')[-1]

            result['role_name'] = role_name
            result['session_name'] = session_name

            # Get role details
            try:
                role_response = iam.get_role(RoleName=role_name)
                role = role_response['Role']

                result['role_info'] = {
                    'created': role['CreateDate'].isoformat(),
                    'max_session_duration': role['MaxSessionDuration'],
                    'assume_role_policy': role['AssumeRolePolicyDocument']
                }

                if 'PermissionsBoundary' in role:
                    result['role_info']['permission_boundary'] = role['PermissionsBoundary']['PermissionsBoundaryArn']

                # List attached policies
                attached_policies_response = iam.list_attached_role_policies(RoleName=role_name)
                attached_policies = []

                for policy in attached_policies_response['AttachedPolicies']:
                    policy_info = {
                        'name': policy['PolicyName'],
                        'arn': policy['PolicyArn']
                    }

                    if verbose:
                        # Get policy details
                        policy_response = iam.get_policy(PolicyArn=policy['PolicyArn'])
                        default_version = policy_response['Policy']['DefaultVersionId']

                        version_response = iam.get_policy_version(
                            PolicyArn=policy['PolicyArn'],
                            VersionId=default_version
                        )

                        policy_info['document'] = version_response['PolicyVersion']['Document']

                    attached_policies.append(policy_info)

                result['attached_policies'] = attached_policies

                # List inline policies
                inline_policies_response = iam.list_role_policies(RoleName=role_name)
                inline_policies = []

                for policy_name in inline_policies_response['PolicyNames']:
                    policy_info = {'name': policy_name}

                    if verbose:
                        policy_response = iam.get_role_policy(
                            RoleName=role_name,
                            PolicyName=policy_name
                        )
                        policy_info['document'] = policy_response['PolicyDocument']

                    inline_policies.append(policy_info)

                result['inline_policies'] = inline_policies

            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == 'AccessDenied':
                    result['role_info'] = {'error': 'AccessDenied'}
                else:
                    result['role_info'] = {'error': error_code}

        return result

    except ClientError as e:
        return {
            'error': e.response['Error']['Code'],
            'error_message': e.response['Error']['Message']
        }

    except NoCredentialsError:
        return {
            'error': 'NoCredentials',
            'error_message': 'No credentials found'
        }

    except Exception as e:
        return {
            'error': 'UnexpectedError',
            'error_message': str(e)
        }


def test_permissions(session):
    """
    Test common AWS permissions

    Args:
        session: boto3 Session object

    Returns:
        list: List of tuples (action, description, result)
    """
    test_permissions = [
        ('ec2:DescribeInstances', 'List EC2 instances'),
        ('s3:ListAllMyBuckets', 'List S3 buckets'),
        ('lambda:ListFunctions', 'List Lambda functions'),
        ('dynamodb:ListTables', 'List DynamoDB tables'),
        ('cloudwatch:DescribeAlarms', 'List CloudWatch alarms'),
        ('iam:GetUser', 'Get IAM user details'),
        ('iam:CreateUser', 'Create IAM users'),
    ]

    results = []

    for action, description in test_permissions:
        try:
            service = action.split(':')[0]
            operation = action.split(':')[1]

            if service == 'ec2' and operation == 'DescribeInstances':
                ec2 = session.client('ec2')
                ec2.describe_instances(MaxResults=5)
                result = "[+] Allowed"
            elif service == 's3' and operation == 'ListAllMyBuckets':
                s3 = session.client('s3')
                s3.list_buckets()
                result = "[+] Allowed"
            elif service == 'lambda' and operation == 'ListFunctions':
                lambda_client = session.client('lambda')
                lambda_client.list_functions(MaxItems=5)
                result = "[+] Allowed"
            elif service == 'dynamodb' and operation == 'ListTables':
                dynamodb = session.client('dynamodb')
                dynamodb.list_tables(Limit=5)
                result = "[+] Allowed"
            elif service == 'cloudwatch' and operation == 'DescribeAlarms':
                cloudwatch = session.client('cloudwatch')
                cloudwatch.describe_alarms(MaxRecords=5)
                result = "[+] Allowed"
            elif service == 'iam' and operation == 'GetUser':
                iam = session.client('iam')
                iam.get_user()
                result = "[+] Allowed"
            elif service == 'iam' and operation == 'CreateUser':
                # Don't actually create, just test with simulate
                result = "[x] Not tested (dangerous)"
            else:
                result = "[?] Unknown"

        except ClientError as e:
            if e.response['Error']['Code'] in ['AccessDenied', 'UnauthorizedOperation']:
                result = "[x] Denied"
            else:
                result = f"[?] {e.response['Error']['Code']}"
        except Exception as e:
            result = f"[?] Error: {str(e)[:30]}"

        results.append((action, description, result))

    return results


def format_permissions(result, test_results=None):
    """
    Format permissions information for display

    Args:
        result: Result dict from get_user_permissions()
        test_results: Optional test results from test_permissions()

    Returns:
        str: Formatted output
    """
    if 'error' in result:
        error_code = result['error']
        error_msg = result.get('error_message', '')

        if error_code in ['AccessDenied', 'AccessDeniedException']:
            return (
                "[ERROR] Access denied\n\n"
                "Your IAM role does not have permission to retrieve identity information.\n\n"
                "Required IAM permissions:\n"
                "  - sts:GetCallerIdentity (usually always available)\n"
                "  - iam:GetRole (to view role configuration)\n"
                "  - iam:ListAttachedRolePolicies (to view policies)"
            )
        elif error_code == 'InvalidClientTokenId':
            return "[ERROR] Invalid or expired credentials\n[INFO] Run authentication to renew your credentials"
        elif error_code == 'ExpiredToken':
            return "[ERROR] Your session has expired\n[INFO] Run authentication to obtain new credentials"
        elif error_code == 'NoCredentials':
            return "[ERROR] No credentials found\n[INFO] Run authentication first"
        else:
            return f"[ERROR] Failed to get permissions: {error_msg}\n[ERROR CODE] {error_code}"

    output = []
    output.append(f"User ARN: {result['arn']}")
    output.append(f"Account: {result['account']}")
    output.append(f"User ID: {result['user_id']}\n")

    if 'role_name' in result:
        output.append(f"Role: {result['role_name']}")
        output.append(f"Session: {result['session_name']}\n")

        if 'role_info' in result:
            role_info = result['role_info']

            if 'error' in role_info:
                if role_info['error'] == 'AccessDenied':
                    output.append("[ERROR] Access denied to IAM role details\n")
                    output.append("Your role does not have permission to view IAM role configurations.\n")
                    output.append("Required IAM permissions:")
                    output.append("  - iam:GetRole")
                    output.append("  - iam:ListAttachedRolePolicies")
                    output.append("  - iam:ListRolePolicies")
                    output.append("  - iam:GetPolicy (for --verbose)")
                    output.append("  - iam:GetPolicyVersion (for --verbose)")
                    output.append("  - iam:GetRolePolicy (for --verbose)\n")
                    output.append("Note: You can still see your effective permissions, just not the role details.")
                else:
                    output.append(f"[ERROR] Failed to get role details: {role_info['error']}")
            else:
                output.append(f"Role Created: {role_info['created']}")
                output.append(f"Max Session Duration: {role_info['max_session_duration']} seconds")

                if 'permission_boundary' in role_info:
                    output.append(f"\nPermission Boundary: {role_info['permission_boundary']}")

                output.append("\nAssumeRole Policy:")
                output.append(json.dumps(role_info['assume_role_policy'], indent=2))

                # Attached policies
                output.append("\nAttached Policies:")
                if result.get('attached_policies'):
                    for policy in result['attached_policies']:
                        output.append(f"  - {policy['name']} ({policy['arn']})")

                        if 'document' in policy:
                            output.append(f"\n    Policy Document:")
                            output.append(json.dumps(policy['document'], indent=6))
                            output.append("")
                else:
                    output.append("  (None)")

                # Inline policies
                output.append("\nInline Policies:")
                if result.get('inline_policies'):
                    for policy in result['inline_policies']:
                        output.append(f"  - {policy['name']}")

                        if 'document' in policy:
                            output.append(f"\n    Policy Document:")
                            output.append(json.dumps(policy['document'], indent=6))
                            output.append("")
                else:
                    output.append("  (None)")

    # Test results
    if test_results:
        output.append("\n\nTesting Common Permissions:")
        output.append("-" * 80)

        for action, description, test_result in test_results:
            output.append(f"  {action:<30} {description:<30} {test_result}")

    return '\n'.join(output)
