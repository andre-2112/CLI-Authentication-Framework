# CCA 0.2 - CloudTrail Access for Users

**Date:** 2025-11-10
**Status:** Implementation Guide

---

## Overview

This document explains different approaches to give CCA users access to their AWS CloudTrail logs for viewing operation history.

---

## Background

The `ccc history` command needs to query AWS CloudTrail to show users their operation history. However, CloudTrail access requires specific IAM permissions, and we need to ensure users can only see their own events, not other users' activities.

---

## Option 1: Grant LookupEvents with Client-Side Filtering (Simple)

### How It Works

The `ccc history` command already filters events by the user's ARN, so you can safely grant `cloudtrail:LookupEvents` to all CCA users. Each user will only see their own events.

**Client-side filtering in CLI:**
```python
response = cloudtrail.lookup_events(
    LookupAttributes=[
        {
            'AttributeKey': 'Username',
            'AttributeValue': user_arn.split('/')[-1]
        }
    ],
    StartTime=start_time,
    MaxResults=args.limit
)
```

### IAM Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["cloudtrail:LookupEvents"],
      "Resource": "*"
    }
  ]
}
```

### Pros & Cons

**Pros:**
- ✅ Simple to implement
- ✅ Already works with current CLI code
- ✅ No additional AWS resources needed
- ✅ Users automatically see only their own events
- ✅ No additional costs

**Cons:**
- ⚠️ Users can technically query other usernames (but would need to modify the CLI)
- ⚠️ Limited to 90 days of history
- ⚠️ Limited to 50 events per call
- ⚠️ No resource-level permissions (action applies to all trails)

### Security Considerations

- CloudTrail's `LookupEvents` API doesn't support resource-level permissions
- The permission grants access to all CloudTrail events in the account
- Security relies on client-side filtering in the CLI
- Users with AWS CLI knowledge could query other users' events if they know the ARNs

---

## Option 2: CloudWatch Logs with Resource-Level Permissions (Isolated)

### Architecture

```
CloudTrail → CloudWatch Log Group → Log Streams (per user)
                                    ├─ /aws/cloudtrail/user1
                                    ├─ /aws/cloudtrail/user2
                                    └─ /aws/cloudtrail/user3
```

### How It Works

Route CloudTrail logs to CloudWatch Logs and grant per-user access to specific log streams using resource-level IAM permissions.

### Implementation Steps

#### 1. Enable CloudTrail to CloudWatch Logs

```bash
# Create CloudWatch Logs role for CloudTrail
aws iam create-role \
  --role-name CloudTrailToCloudWatchLogs \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "Service": "cloudtrail.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
      }
    ]
  }'

# Attach policy to allow CloudTrail to write to CloudWatch Logs
aws iam put-role-policy \
  --role-name CloudTrailToCloudWatchLogs \
  --policy-name CloudWatchLogsWrite \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        "Resource": "arn:aws:logs:*:*:log-group:/aws/cloudtrail/cca-users:*"
      }
    ]
  }'

# Update CloudTrail to send logs to CloudWatch
aws cloudtrail update-trail \
  --name your-trail-name \
  --cloud-watch-logs-log-group-arn arn:aws:logs:region:account:log-group:/aws/cloudtrail/cca-users \
  --cloud-watch-logs-role-arn arn:aws:iam::account:role/CloudTrailToCloudWatchLogs
```

#### 2. Create Log Group and Streams

```bash
# Create main log group
aws logs create-log-group --log-group-name /aws/cloudtrail/cca-users

# Set retention policy (optional, e.g., 90 days)
aws logs put-retention-policy \
  --log-group-name /aws/cloudtrail/cca-users \
  --retention-in-days 90

# Create per-user log streams
aws logs create-log-stream \
  --log-group-name /aws/cloudtrail/cca-users \
  --log-stream-name testuser@example.com
```

#### 3. Grant User Access to Their Log Stream

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:FilterLogEvents",
        "logs:GetLogEvents",
        "logs:DescribeLogStreams"
      ],
      "Resource": "arn:aws:logs:*:*:log-group:/aws/cloudtrail/cca-users:log-stream:${aws:username}"
    }
  ]
}
```

### Pros & Cons

**Pros:**
- ✅ True resource-level isolation
- ✅ Longer retention (up to indefinite, or as configured)
- ✅ More flexible querying
- ✅ Can use CloudWatch Insights for advanced analysis
- ✅ Better audit trail
- ✅ Users truly cannot access other users' logs

**Cons:**
- ❌ More complex setup
- ❌ Additional costs (CloudWatch Logs storage and query charges)
- ❌ Requires Lambda or subscription filters to route logs per user
- ❌ CLI would need modification to query CloudWatch instead of CloudTrail
- ❌ Requires creating log streams for each new user

---

## Option 3: Hybrid Approach (Recommended)

### Overview

Combine both approaches for flexibility and better user experience:

1. **Grant `cloudtrail:LookupEvents`** for recent events (last 90 days) - Fast and simple
2. **Use CloudWatch Logs** for historical analysis and long-term audit trail

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CCC CLI (ccc history)                │
│                                                         │
│  1. Try CloudTrail LookupEvents (last 90 days)         │
│     └─> Fast, real-time, simple                        │
│                                                         │
│  2. Fallback to CloudWatch Logs (older events)         │
│     └─> Historical, isolated, resource-level perms     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### IAM Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "RecentHistory",
      "Effect": "Allow",
      "Action": ["cloudtrail:LookupEvents"],
      "Resource": "*"
    },
    {
      "Sid": "HistoricalLogs",
      "Effect": "Allow",
      "Action": [
        "logs:FilterLogEvents",
        "logs:GetLogEvents",
        "logs:DescribeLogStreams"
      ],
      "Resource": [
        "arn:aws:logs:*:*:log-group:/aws/cloudtrail/cca-users",
        "arn:aws:logs:*:*:log-group:/aws/cloudtrail/cca-users:log-stream:*"
      ],
      "Condition": {
        "StringEquals": {
          "logs:LogStreamName": "${cognito-identity.amazonaws.com:sub}"
        }
      }
    }
  ]
}
```

### CLI Behavior

```python
def cmd_history(args):
    """Display history of AWS operations performed by the user"""

    # Try CloudTrail first (recent events)
    try:
        events = fetch_from_cloudtrail(days=args.days, limit=args.limit)
        if events:
            display_events(events)
            return
    except AccessDeniedException:
        print("[INFO] CloudTrail access not available, checking CloudWatch Logs...")

    # Fallback to CloudWatch Logs (older events or if CloudTrail denied)
    try:
        events = fetch_from_cloudwatch_logs(days=args.days, limit=args.limit)
        display_events(events)
    except Exception as e:
        print(f"[ERROR] Could not retrieve history: {e}")
```

### Pros & Cons

**Pros:**
- ✅ Best user experience (fast recent events)
- ✅ Long-term audit capability
- ✅ Graceful fallback if one method fails
- ✅ Resource-level isolation for historical logs
- ✅ Flexible - can disable CloudTrail access if security concern

**Cons:**
- ⚠️ Most complex to implement
- ⚠️ Additional CloudWatch Logs costs
- ⚠️ Requires maintaining both systems

---

## Comparison Table

| Feature | Option 1: CloudTrail Only | Option 2: CloudWatch Only | Option 3: Hybrid |
|---------|---------------------------|---------------------------|------------------|
| **Complexity** | Low | High | Medium-High |
| **Cost** | Free | $$ | $ |
| **History Retention** | 90 days | Unlimited | Unlimited |
| **Resource Isolation** | ❌ Client-side | ✅ Resource-level | ✅ Resource-level |
| **Query Speed** | Fast | Medium | Fast (recent) |
| **Setup Time** | 5 minutes | 30 minutes | 45 minutes |
| **User Experience** | Good | Good | Best |
| **Security** | Good | Excellent | Excellent |

---

## Recommendation

### For CCA Framework: **Option 3 (Hybrid)**

**Reasons:**

1. **Security**: Resource-level isolation for historical logs
2. **Performance**: Fast CloudTrail access for recent events
3. **Flexibility**: Can disable CloudTrail if security requires
4. **User Experience**: Best of both worlds
5. **Audit**: Long-term audit trail in CloudWatch Logs

### Implementation Priority

**Phase 1 (Immediate):**
- Add `cloudtrail:LookupEvents` permission to CCA role
- Test `ccc history` with CloudTrail

**Phase 2 (Optional, for production):**
- Set up CloudWatch Logs integration
- Add per-user log stream creation
- Modify CLI to support both sources
- Add CloudWatch Logs permissions with resource-level access

---

## Cost Estimate

### Option 1: CloudTrail Only
- **Cost:** $0 (CloudTrail LookupEvents is free)

### Option 2: CloudWatch Logs Only
- **CloudWatch Logs Storage:** ~$0.50/GB/month
- **CloudWatch Logs Ingestion:** $0.50/GB ingested
- **Query Costs:** $0.005/GB scanned
- **Estimated:** ~$5-20/month for small team

### Option 3: Hybrid
- **Same as Option 2** (CloudWatch Logs costs)
- **CloudTrail LookupEvents:** Free

---

## Security Considerations

### CloudTrail LookupEvents

**Risks:**
- Users can query any username if they modify the CLI
- No true resource-level isolation

**Mitigations:**
- CLI filters by user ARN automatically
- Monitor CloudTrail for suspicious LookupEvents calls
- Educate users about acceptable use
- Consider Option 2 or 3 for high-security environments

### CloudWatch Logs

**Risks:**
- Requires creating log streams for each user
- More complex IAM policies
- Additional AWS resources to manage

**Mitigations:**
- Use resource-level IAM conditions
- Automate log stream creation
- Set retention policies
- Monitor access with CloudTrail

---

## Implementation Guide

### Quick Start (Option 1)

```bash
# Add CloudTrail read permission to CCA role
aws iam put-role-policy \
  --role-name CCA-Cognito-Auth-Role \
  --policy-name CCACloudTrailRead \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": ["cloudtrail:LookupEvents"],
        "Resource": "*"
      }
    ]
  }'

# Test
ccc history
```

### Full Implementation (Option 3)

See implementation steps in Infrastructure Changes document.

---

## Testing

### Test Cases

1. **Recent events (CloudTrail)**
   ```bash
   ccc history --days 7
   ```

2. **Older events (CloudWatch Logs)**
   ```bash
   ccc history --days 30
   ```

3. **No access (should show helpful error)**
   ```bash
   # Remove permissions and test
   ccc history
   ```

4. **Multiple users (isolation test)**
   ```bash
   # Login as user1
   ccc history
   # Should only see user1's events

   # Login as user2
   ccc history
   # Should only see user2's events
   ```

---

## Related Documents

- **CCA 0.2 - Hybrid CloudTrail Implementation.md** - Detailed implementation steps
- **Lambda Function:** `lambda/lambda_function.py` - May need log stream creation logic
- **CLI Tool:** `ccc-cli/ccc.py` - Updated history command

---

**Document Status:** ✅ Complete
**Implementation Status:** Pending
**Recommended Approach:** Option 3 (Hybrid)
