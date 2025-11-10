"""
CloudTrail Operations
Provides functions to query CloudTrail and CloudWatch Logs for user activity history.
"""

import json
import time
from datetime import datetime, timezone, timedelta
from botocore.exceptions import ClientError


def get_user_history(session, username, days=7, limit=50):
    """
    Get user activity history from CloudTrail and CloudWatch Logs (hybrid approach).
    Tries CloudTrail first for recent events, falls back to CloudWatch Logs.

    Args:
        session: boto3 Session object
        username: Username to filter events
        days: Number of days to look back
        limit: Maximum number of events to return

    Returns:
        tuple: (events list, source string)
    """
    events = []
    source = None

    # Try CloudTrail first (recent events, fast)
    try:
        start_time = datetime.now(timezone.utc) - timedelta(days=days)

        print("[INFO] Fetching events from CloudTrail...")
        cloudtrail = session.client('cloudtrail')

        response = cloudtrail.lookup_events(
            LookupAttributes=[
                {
                    'AttributeKey': 'Username',
                    'AttributeValue': username
                }
            ],
            StartTime=start_time,
            MaxResults=limit
        )

        ct_events = response.get('Events', [])

        if ct_events:
            # Convert CloudTrail events to common format
            for event in ct_events:
                events.append({
                    'time': event['EventTime'],
                    'event_name': event['EventName'],
                    'resources': event.get('Resources', []),
                    'error_code': event.get('ErrorCode', ''),
                    'event_id': event['EventId'],
                    'source': 'CloudTrail'
                })
            source = 'CloudTrail'
            print(f"[OK] Retrieved {len(events)} events from CloudTrail\n")

    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AccessDeniedException':
            print("[INFO] CloudTrail access denied, trying CloudWatch Logs...\n")
        else:
            print(f"[WARN] CloudTrail error: {error_code}, trying CloudWatch Logs...\n")
    except Exception as e:
        print(f"[WARN] CloudTrail unavailable: {e}, trying CloudWatch Logs...\n")

    # Fallback to CloudWatch Logs if CloudTrail failed or returned no events
    if not events:
        try:
            print("[INFO] Fetching events from CloudWatch Logs...")
            logs = session.client('logs')

            log_group_name = '/aws/cloudtrail/cca-users'

            # Calculate time range in milliseconds
            start_time = datetime.now(timezone.utc) - timedelta(days=days)
            start_time_ms = int(start_time.timestamp() * 1000)
            end_time_ms = int(time.time() * 1000)

            # Filter pattern to match events for this user
            filter_pattern = f'{{ $.userIdentity.arn = "*{username}*" }}'

            response = logs.filter_log_events(
                logGroupName=log_group_name,
                startTime=start_time_ms,
                endTime=end_time_ms,
                filterPattern=filter_pattern,
                limit=limit
            )

            log_events = response.get('events', [])

            if log_events:
                # Parse CloudWatch Logs events
                for log_event in log_events:
                    try:
                        event_data = json.loads(log_event['message'])
                        events.append({
                            'time': datetime.fromtimestamp(log_event['timestamp'] / 1000, tz=timezone.utc),
                            'event_name': event_data.get('eventName', 'Unknown'),
                            'resources': event_data.get('resources', []),
                            'error_code': event_data.get('errorCode', ''),
                            'event_id': event_data.get('eventID', 'N/A'),
                            'source': 'CloudWatch Logs'
                        })
                    except json.JSONDecodeError:
                        continue

                source = 'CloudWatch Logs'
                print(f"[OK] Retrieved {len(events)} events from CloudWatch Logs\n")

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceNotFoundException':
                print("[WARN] CloudWatch Logs group not found")
            elif error_code == 'AccessDeniedException':
                print("[ERROR] Access denied to CloudWatch Logs\n")
                print("Your IAM role does not have permission to view CloudWatch Logs.")
                print("\nRequired IAM permissions:")
                print("  - logs:FilterLogEvents")
                print("  - logs:GetLogEvents")
            else:
                print(f"[WARN] CloudWatch Logs error: {error_code}")
        except Exception as e:
            print(f"[WARN] CloudWatch Logs unavailable: {e}")

    return events, source


def format_events(events, limit=50, verbose=False):
    """
    Format events for display

    Args:
        events: List of event dicts
        limit: Maximum number of events to display
        verbose: Show detailed event information

    Returns:
        str: Formatted event table
    """
    if not events:
        return "[INFO] No events found in the specified time range\n\nTroubleshooting:\n  1. Make sure you have performed some AWS operations\n  2. Try increasing --days parameter\n  3. Check that CloudTrail is logging events\n  4. Verify IAM permissions for cloudtrail:LookupEvents or logs:FilterLogEvents"

    # Sort by time (most recent first)
    events.sort(key=lambda x: x['time'], reverse=True)

    output = []
    output.append(f"{'Time':<20} {'Event':<30} {'Resource':<40} {'Status':<15}")
    output.append("-" * 105)

    for event in events[:limit]:
        event_time = event['time'].strftime('%Y-%m-%d %H:%M:%S')
        event_name = event['event_name'][:29]

        # Extract resource info
        resources = event['resources']
        if resources and isinstance(resources, list) and len(resources) > 0:
            if isinstance(resources[0], dict):
                resource_name = resources[0].get('ResourceName', 'N/A')[:39]
            else:
                resource_name = str(resources[0])[:39]
        else:
            resource_name = 'N/A'

        # Get error status
        error_code = event['error_code']
        status = 'Error' if error_code else 'Success'

        output.append(f"{event_time:<20} {event_name:<30} {resource_name:<40} {status:<15}")

        if verbose:
            output.append(f"  Event ID: {event['event_id']}")
            output.append(f"  Source: {event['source']}")
            if error_code:
                output.append(f"  Error: {error_code}")
            output.append("")

    return '\n'.join(output)
