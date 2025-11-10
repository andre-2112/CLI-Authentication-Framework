"""
AWS Resources Operations
Provides functions to list and query AWS resources using Resource Groups Tagging API.
"""

import json
from botocore.exceptions import ClientError, NoCredentialsError


def list_user_resources(session, username=None, filter_by_owner=False, limit=10, show_all=False, verbose=False):
    """
    List all AWS resources, optionally filtered by Owner tag.

    Args:
        session: boto3 Session object
        username: Username to filter by (for Owner tag)
        filter_by_owner: If True, filter resources by Owner tag matching username
        limit: Maximum number of resources to show per type
        show_all: If True, show all resources without limit
        verbose: Show detailed resource information including tags

    Returns:
        dict: {
            'total_resources': int,
            'resources_by_type': dict,
            'error': str (if error occurred)
        }
    """
    try:
        # Use Resource Groups Tagging API to find all resources
        tagging = session.client('resourcegroupstaggingapi')

        print("[INFO] Scanning for resources...")

        # Get all resources (optionally filter by Owner tag)
        paginator = tagging.get_paginator('get_resources')

        # Try to filter by Owner tag if requested
        tag_filters = []
        if filter_by_owner and username:
            tag_filters = [{'Key': 'Owner', 'Values': [username]}]

        all_resources = []
        for page in paginator.paginate(TagFilters=tag_filters):
            all_resources.extend(page['ResourceTagMappingList'])

        if not all_resources:
            return {
                'total_resources': 0,
                'resources_by_type': {},
                'message': 'No resources found'
            }

        # Group resources by type
        resources_by_type = {}
        for resource in all_resources:
            arn = resource['ResourceARN']
            # Extract service from ARN (format: arn:aws:service:region:account:resource)
            parts = arn.split(':')
            if len(parts) >= 6:
                service = parts[2]
                resource_type = parts[5].split('/')[0] if '/' in parts[5] else parts[5]
            else:
                service = 'unknown'
                resource_type = 'unknown'

            key = f"{service}/{resource_type}"
            if key not in resources_by_type:
                resources_by_type[key] = []
            resources_by_type[key].append(resource)

        return {
            'total_resources': len(all_resources),
            'resources_by_type': resources_by_type,
            'limit': limit,
            'show_all': show_all,
            'verbose': verbose
        }

    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']

        return {
            'total_resources': 0,
            'resources_by_type': {},
            'error': error_code,
            'error_message': error_msg
        }

    except NoCredentialsError:
        return {
            'total_resources': 0,
            'resources_by_type': {},
            'error': 'NoCredentials',
            'error_message': 'No credentials found. Run authentication first.'
        }

    except Exception as e:
        return {
            'total_resources': 0,
            'resources_by_type': {},
            'error': 'UnexpectedError',
            'error_message': str(e)
        }


def format_resources(result):
    """
    Format resource listing for display

    Args:
        result: Result dict from list_user_resources()

    Returns:
        str: Formatted output
    """
    if 'error' in result:
        error_code = result['error']
        error_msg = result.get('error_message', '')

        if error_code == 'AccessDeniedException' or 'not authorized' in error_msg:
            return (
                "[ERROR] Access denied to Resource Groups Tagging API\n\n"
                "Your IAM role does not have permission to query AWS resources.\n\n"
                "Required IAM permissions:\n"
                "  - tag:GetResources\n"
                "  - tag:GetTagKeys (optional)\n"
                "  - tag:GetTagValues (optional)\n\n"
                "To enable this feature, ask your administrator to add the following policy:\n" +
                json.dumps({
                    "Version": "2012-10-17",
                    "Statement": [{
                        "Effect": "Allow",
                        "Action": [
                            "tag:GetResources",
                            "tag:GetTagKeys",
                            "tag:GetTagValues"
                        ],
                        "Resource": "*"
                    }]
                }, indent=2)
            )
        elif error_code == 'InvalidClientTokenId':
            return "[ERROR] Invalid or expired credentials\n[INFO] Run authentication to renew your credentials"
        elif error_code == 'ExpiredToken':
            return "[ERROR] Your session has expired\n[INFO] Run authentication to obtain new credentials"
        elif error_code == 'NoCredentials':
            return "[ERROR] No credentials found\n[INFO] Run authentication first"
        else:
            return f"[ERROR] Failed to list resources: {error_msg}\n[ERROR CODE] {error_code}"

    if result['total_resources'] == 0:
        msg = result.get('message', 'No resources found')
        return f"[INFO] {msg}"

    resources_by_type = result['resources_by_type']
    limit = result.get('limit', 10)
    show_all = result.get('show_all', False)
    verbose = result.get('verbose', False)

    output = []
    output.append(f"\nFound {result['total_resources']} resources across {len(resources_by_type)} resource types:\n")

    for resource_type, resources in sorted(resources_by_type.items()):
        output.append(f"\n{resource_type} ({len(resources)} resources):")
        output.append("-" * 80)

        for resource in resources[:None if show_all else limit]:
            arn = resource['ResourceARN']
            tags = {tag['Key']: tag['Value'] for tag in resource.get('Tags', [])}

            # Extract resource name from ARN
            resource_name = arn.split('/')[-1] if '/' in arn else arn.split(':')[-1]

            output.append(f"  Resource: {resource_name}")
            output.append(f"  ARN: {arn}")

            if verbose and tags:
                output.append(f"  Tags:")
                for key, value in tags.items():
                    output.append(f"    {key}: {value}")

            output.append("")

        if not show_all and len(resources) > limit:
            output.append(f"  ... and {len(resources) - limit} more (use --all to see all)")

    output.append(f"\nTotal resources: {result['total_resources']}")

    return '\n'.join(output)
