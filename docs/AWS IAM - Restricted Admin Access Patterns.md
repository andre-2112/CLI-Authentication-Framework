# AWS IAM - Restricted Admin Access Patterns

**Purpose:** Strategies for giving CLI users admin-like access with restrictions, including resource count limits
**Last Updated:** 2025-11-10

---

## Overview

You want to give users the ability to create AWS resources via CLI, but with safeguards to prevent:
- Unlimited resource creation
- Access to sensitive resources
- Excessive costs
- Security misconfigurations

---

## Strategy 1: Permission Boundaries + Service Quotas (EASIEST)

### ⭐ Recommended Approach

**Pros:**
- ✅ Easy to implement
- ✅ Easy to manage
- ✅ Built-in AWS features
- ✅ No custom code needed

**How it works:**
1. **Permission Boundary** - Defines maximum permissions
2. **Service Quotas** - Hard limits on resource counts
3. **IAM Policy** - Grants specific permissions (within boundary)

---

### Step 1: Create Permission Boundary

**Permission boundary defines the MAXIMUM permissions a user can have.**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowEC2Operations",
      "Effect": "Allow",
      "Action": [
        "ec2:RunInstances",
        "ec2:TerminateInstances",
        "ec2:StartInstances",
        "ec2:StopInstances",
        "ec2:DescribeInstances",
        "ec2:CreateTags"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": ["us-east-1", "us-west-2"]
        }
      }
    },
    {
      "Sid": "AllowS3Operations",
      "Effect": "Allow",
      "Action": [
        "s3:CreateBucket",
        "s3:DeleteBucket",
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": "*",
      "Condition": {
        "StringLike": {
          "s3:x-amz-acl": ["private", "bucket-owner-full-control"]
        }
      }
    },
    {
      "Sid": "AllowLambdaOperations",
      "Effect": "Allow",
      "Action": [
        "lambda:CreateFunction",
        "lambda:DeleteFunction",
        "lambda:UpdateFunctionCode",
        "lambda:InvokeFunction"
      ],
      "Resource": "*"
    },
    {
      "Sid": "DenyDangerousOperations",
      "Effect": "Deny",
      "Action": [
        "iam:CreateUser",
        "iam:DeleteUser",
        "iam:CreateAccessKey",
        "organizations:*",
        "account:*",
        "aws-portal:*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "DenyExpensiveResources",
      "Effect": "Deny",
      "Action": [
        "ec2:RunInstances"
      ],
      "Resource": "arn:aws:ec2:*:*:instance/*",
      "Condition": {
        "ForAnyValue:StringNotLike": {
          "ec2:InstanceType": [
            "t2.micro",
            "t2.small",
            "t3.micro",
            "t3.small"
          ]
        }
      }
    }
  ]
}
```

**Create the boundary:**
```bash
aws iam create-policy \
  --policy-name RestrictedAdminBoundary \
  --policy-document file://boundary-policy.json
```

---

### Step 2: Set Service Quotas (Resource Count Limits)

**Service Quotas enforce hard limits on resource counts.**

```bash
# Limit EC2 instances to 5
aws service-quotas request-service-quota-increase \
  --service-code ec2 \
  --quota-code L-1216C47A \
  --desired-value 5

# Limit S3 buckets to 50 (default is 100)
aws service-quotas request-service-quota-increase \
  --service-code s3 \
  --quota-code L-DC2B2D3D \
  --desired-value 50

# Limit Lambda functions to 25
aws service-quotas request-service-quota-increase \
  --service-code lambda \
  --quota-code L-9FEE3D26 \
  --desired-value 25

# Limit RDS instances to 10
aws service-quotas request-service-quota-increase \
  --service-code rds \
  --quota-code L-7B6409FD \
  --desired-value 10
```

**View current quotas:**
```bash
# List all EC2 quotas
aws service-quotas list-service-quotas --service-code ec2

# Get specific quota
aws service-quotas get-service-quota \
  --service-code ec2 \
  --quota-code L-1216C47A
```

---

### Step 3: Create IAM Role with Boundary

```bash
# Create role with permission boundary
aws iam create-role \
  --role-name RestrictedAdminRole \
  --assume-role-policy-document file://trust-policy.json \
  --permissions-boundary arn:aws:iam::ACCOUNT_ID:policy/RestrictedAdminBoundary

# Attach managed policies (limited by boundary)
aws iam attach-role-policy \
  --role-name RestrictedAdminRole \
  --policy-arn arn:aws:iam::aws:policy/PowerUserAccess
```

**Trust policy for Cognito (for CCA users):**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "cognito-identity.amazonaws.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "cognito-identity.amazonaws.com:aud": "us-east-1:IDENTITY_POOL_ID"
        }
      }
    }
  ]
}
```

---

## Strategy 2: Tag-Based Access Control (EASY TO MANAGE)

### How It Works

**Require users to tag all resources. Enforce limits based on tag values.**

**Pros:**
- ✅ Easy to track resource ownership
- ✅ Easy to find resources by user
- ✅ Can use AWS Config to enforce
- ✅ Cost allocation by tag

**Cons:**
- ⚠️ Requires custom monitoring for count limits
- ⚠️ Users can create resources until limit reached

---

### Implementation

#### Policy: Require Tags on Creation

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "RequireTagsOnEC2Creation",
      "Effect": "Allow",
      "Action": "ec2:RunInstances",
      "Resource": "arn:aws:ec2:*:*:instance/*",
      "Condition": {
        "StringEquals": {
          "aws:RequestTag/Owner": "${aws:username}",
          "aws:RequestTag/ManagedBy": "CCA"
        }
      }
    },
    {
      "Sid": "RequireTagsOnS3Creation",
      "Effect": "Allow",
      "Action": "s3:CreateBucket",
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:RequestTag/Owner": "${aws:username}",
          "aws:RequestTag/CostCenter": "Development"
        }
      }
    },
    {
      "Sid": "AllowOnlyOwnedResourcesModification",
      "Effect": "Allow",
      "Action": [
        "ec2:TerminateInstances",
        "ec2:StopInstances",
        "s3:DeleteBucket"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:ResourceTag/Owner": "${aws:username}"
        }
      }
    }
  ]
}
```

#### Monitor Resource Counts with AWS Config

**AWS Config Rule (custom Lambda):**
```python
import boto3

def lambda_handler(event, context):
    """Check if user has exceeded resource quota"""

    ec2 = boto3.client('ec2')
    config = boto3.client('config')

    # Get all EC2 instances for user
    username = event['configRuleParameters']['username']

    response = ec2.describe_instances(
        Filters=[
            {'Name': 'tag:Owner', 'Values': [username]},
            {'Name': 'instance-state-name', 'Values': ['running', 'stopped']}
        ]
    )

    instance_count = sum(len(r['Instances']) for r in response['Reservations'])
    max_instances = int(event['configRuleParameters']['maxInstances'])

    if instance_count > max_instances:
        return {
            'compliance_type': 'NON_COMPLIANT',
            'annotation': f'User has {instance_count} instances (max: {max_instances})'
        }

    return {
        'compliance_type': 'COMPLIANT',
        'annotation': f'User has {instance_count} instances (max: {max_instances})'
    }
```

---

## Strategy 3: AWS Budgets with Actions (COST-BASED)

### How It Works

**Set a budget for each user. Stop resource creation when budget exceeded.**

**Pros:**
- ✅ Cost-based (more important than count)
- ✅ Built-in AWS feature
- ✅ Can automatically apply IAM deny policy
- ✅ Email alerts

**Cons:**
- ⚠️ Cost-based, not count-based
- ⚠️ Slight delay (hourly budget updates)

---

### Implementation

```bash
# Create budget for user
aws budgets create-budget \
  --account-id ACCOUNT_ID \
  --budget file://budget.json \
  --notifications-with-subscribers file://notifications.json
```

**budget.json:**
```json
{
  "BudgetName": "user-john-monthly-budget",
  "BudgetLimit": {
    "Amount": "100",
    "Unit": "USD"
  },
  "TimeUnit": "MONTHLY",
  "BudgetType": "COST",
  "CostFilters": {
    "TagKeyValue": ["Owner$john@example.com"]
  }
}
```

**Budget Action (Deny Policy):**
```json
{
  "ActionId": "deny-when-budget-exceeded",
  "BudgetName": "user-john-monthly-budget",
  "NotificationType": "ACTUAL",
  "ActionType": "APPLY_IAM_POLICY",
  "ActionThreshold": {
    "ActionThresholdValue": 100,
    "ActionThresholdType": "PERCENTAGE"
  },
  "Definition": {
    "IamActionDefinition": {
      "PolicyArn": "arn:aws:iam::ACCOUNT_ID:policy/DenyAllActions"
    }
  },
  "ExecutionRoleArn": "arn:aws:iam::ACCOUNT_ID:role/BudgetActionRole",
  "ApprovalModel": "AUTOMATIC",
  "Subscribers": [
    {
      "SubscriptionType": "EMAIL",
      "Address": "admin@example.com"
    }
  ]
}
```

**DenyAllActions policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Deny",
      "Action": [
        "ec2:RunInstances",
        "s3:CreateBucket",
        "lambda:CreateFunction",
        "rds:CreateDBInstance"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## Strategy 4: Resource Groups + CloudWatch Alarms

### How It Works

**Use Resource Groups to track user resources. CloudWatch alarms for count thresholds.**

**Pros:**
- ✅ Real-time monitoring
- ✅ Automated alerting
- ✅ Can trigger Lambda for enforcement

**Cons:**
- ⚠️ Requires custom Lambda for enforcement
- ⚠️ More complex setup

---

### Implementation

#### Create Resource Group

```bash
# Create resource group for user's resources
aws resource-groups create-group \
  --name "user-john-resources" \
  --resource-query file://query.json
```

**query.json:**
```json
{
  "Type": "TAG_FILTERS_1_0",
  "Query": {
    "ResourceTypeFilters": ["AWS::AllSupported"],
    "TagFilters": [
      {
        "Key": "Owner",
        "Values": ["john@example.com"]
      }
    ]
  }
}
```

#### CloudWatch Alarm for Resource Count

```python
import boto3

def count_user_resources(username):
    """Count all resources for a user"""

    # Use Resource Groups Tagging API
    tagging = boto3.client('resourcegroupstaggingapi')

    response = tagging.get_resources(
        TagFilters=[
            {
                'Key': 'Owner',
                'Values': [username]
            }
        ]
    )

    return len(response['ResourceTagMappingList'])

# Publish to CloudWatch
cloudwatch = boto3.client('cloudwatch')
cloudwatch.put_metric_data(
    Namespace='UserResources',
    MetricData=[
        {
            'MetricName': 'ResourceCount',
            'Value': count_user_resources('john@example.com'),
            'Unit': 'Count',
            'Dimensions': [
                {'Name': 'Username', 'Value': 'john@example.com'}
            ]
        }
    ]
)
```

**CloudWatch Alarm:**
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name user-john-resource-limit \
  --alarm-description "Alert when user exceeds 50 resources" \
  --metric-name ResourceCount \
  --namespace UserResources \
  --statistic Maximum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 50 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=Username,Value=john@example.com \
  --alarm-actions arn:aws:sns:us-east-1:ACCOUNT_ID:admin-alerts
```

---

## Comparison Matrix

| Strategy | Ease of Setup | Ease of Management | Resource Count Limits | Cost | Flexibility |
|----------|---------------|--------------------|-----------------------|------|-------------|
| **Permission Boundaries + Service Quotas** | ⭐⭐⭐⭐⭐ Easy | ⭐⭐⭐⭐⭐ Easy | ✅ Built-in | Free | ⭐⭐⭐ Medium |
| **Tag-Based Access** | ⭐⭐⭐⭐ Easy | ⭐⭐⭐⭐ Easy | ⚠️ Requires monitoring | Free | ⭐⭐⭐⭐⭐ High |
| **AWS Budgets** | ⭐⭐⭐⭐ Easy | ⭐⭐⭐⭐⭐ Easy | ⚠️ Cost-based only | Free (2 budgets) | ⭐⭐⭐ Medium |
| **Resource Groups + Alarms** | ⭐⭐ Complex | ⭐⭐⭐ Medium | ✅ Custom enforcement | Low cost | ⭐⭐⭐⭐⭐ High |

---

## Recommended Approach for CCA

### Hybrid: Permission Boundary + Service Quotas + Tags

**Why this combination:**
1. **Permission Boundary** - Prevents dangerous operations
2. **Service Quotas** - Hard limits on resource counts
3. **Tags** - Easy tracking and cost allocation

---

### Step-by-Step Implementation

#### 1. Update CCA IAM Role with Permission Boundary

**Modify the CCA-Cognito-Auth-Role:**

```bash
# Create permission boundary policy
aws iam create-policy \
  --policy-name CCA-User-Boundary \
  --policy-document file://cca-boundary.json

# Apply boundary to existing role (requires recreate)
# Note: Cannot add boundary to existing role, must recreate
aws iam create-role \
  --role-name CCA-Cognito-Auth-Role-v2 \
  --assume-role-policy-document file://trust-policy.json \
  --permissions-boundary arn:aws:iam::211050572089:policy/CCA-User-Boundary
```

**cca-boundary.json:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowBasicServices",
      "Effect": "Allow",
      "Action": [
        "ec2:Describe*",
        "ec2:RunInstances",
        "ec2:TerminateInstances",
        "ec2:Start*",
        "ec2:Stop*",
        "s3:*",
        "lambda:*Function*",
        "dynamodb:*",
        "cloudwatch:*",
        "logs:*"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "us-east-1"
        }
      }
    },
    {
      "Sid": "RequireTagsOnCreation",
      "Effect": "Allow",
      "Action": [
        "ec2:RunInstances",
        "s3:CreateBucket",
        "lambda:CreateFunction"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:RequestTag/ManagedBy": "CCA"
        }
      }
    },
    {
      "Sid": "DenyDangerousActions",
      "Effect": "Deny",
      "Action": [
        "iam:*",
        "organizations:*",
        "account:*",
        "aws-portal:*",
        "budgets:*",
        "ec2:*ReservedInstances*",
        "ec2:*SpotInstances*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "LimitInstanceTypes",
      "Effect": "Deny",
      "Action": "ec2:RunInstances",
      "Resource": "arn:aws:ec2:*:*:instance/*",
      "Condition": {
        "StringNotLike": {
          "ec2:InstanceType": ["t2.*", "t3.*"]
        }
      }
    }
  ]
}
```

#### 2. Set Service Quotas

```bash
# Set limits for the AWS account
aws service-quotas request-service-quota-increase \
  --service-code ec2 \
  --quota-code L-1216C47A \
  --desired-value 10 \
  --region us-east-1

aws service-quotas request-service-quota-increase \
  --service-code s3 \
  --quota-code L-DC2B2D3D \
  --desired-value 50 \
  --region us-east-1
```

#### 3. Update Cognito Identity Pool Role Mapping

```bash
# Update Identity Pool to use new role
aws cognito-identity set-identity-pool-roles \
  --identity-pool-id us-east-1:0a656e9c-d356-4964-b6ba-610afb34cbb7 \
  --roles authenticated=arn:aws:iam::211050572089:role/CCA-Cognito-Auth-Role-v2
```

---

## Monitoring and Enforcement

### Dashboard: User Resource Tracking

**CloudWatch Dashboard:**
```bash
aws cloudwatch put-dashboard \
  --dashboard-name CCA-User-Resources \
  --dashboard-body file://dashboard.json
```

**dashboard.json:**
```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/EC2", "InstanceCount", {"stat": "Sum"}],
          ["AWS/S3", "BucketCount", {"stat": "Sum"}],
          ["AWS/Lambda", "FunctionCount", {"stat": "Sum"}]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "us-east-1",
        "title": "Total Resources by Service"
      }
    }
  ]
}
```

### Alerting: Quota Approaching

**SNS Topic for alerts:**
```bash
aws sns create-topic --name cca-quota-alerts

aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:211050572089:cca-quota-alerts \
  --protocol email \
  --notification-endpoint admin@example.com
```

**CloudWatch Alarm:**
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name ec2-quota-warning \
  --alarm-description "Warn when 80% of EC2 quota used" \
  --metric-name ResourceCount \
  --namespace AWS/Usage \
  --statistic Maximum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 8 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:us-east-1:211050572089:cca-quota-alerts
```

---

## User Documentation

### For CCA Users

**What you can do:**
- ✅ Create EC2 instances (t2/t3 types only)
- ✅ Create S3 buckets
- ✅ Create Lambda functions
- ✅ Create DynamoDB tables
- ✅ View CloudWatch logs

**What you cannot do:**
- ❌ Create IAM users or roles
- ❌ Modify account settings
- ❌ Create expensive instance types
- ❌ Create resources outside us-east-1

**Resource limits:**
- EC2 instances: 10 max
- S3 buckets: 50 max
- Lambda functions: 25 max

**Required tags:**
- All resources must have `ManagedBy: CCA` tag
- Add `Owner: your-email@example.com` for tracking

**Example:**
```bash
# Create EC2 instance with required tags
aws ec2 run-instances \
  --image-id ami-12345678 \
  --instance-type t3.micro \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=ManagedBy,Value=CCA},{Key=Owner,Value=user@example.com}]'

# Create S3 bucket with tags
aws s3api create-bucket \
  --bucket my-test-bucket \
  --region us-east-1 \
  --tagging 'TagSet=[{Key=ManagedBy,Value=CCA},{Key=Owner,Value=user@example.com}]'
```

---

## Advanced: Per-User Quotas (Complex)

### If you need different limits per user

**Use IAM Policy Variables:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "LimitResourcesByTag",
      "Effect": "Deny",
      "Action": ["ec2:RunInstances"],
      "Resource": "*",
      "Condition": {
        "NumericGreaterThan": {
          "aws:ResourceTag/Owner": "${aws:username}"
        }
      }
    }
  ]
}
```

**Problem:** IAM doesn't natively support counting resources.

**Solution:** Use external system:

1. **AWS Config + Lambda** - Count resources, deny via SCPs
2. **Third-party tools** - Cloud Custodian, CloudHealth
3. **Custom API Gateway** - Intercept AWS API calls, enforce limits

---

## Troubleshooting

### User gets "Access Denied" creating resources

**Check:**
1. Permission boundary allows the action
2. IAM role policy allows the action
3. Service quota not exceeded
4. Required tags present in request

**Debug:**
```bash
# Check effective permissions
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::211050572089:role/CCA-Cognito-Auth-Role \
  --action-names ec2:RunInstances \
  --resource-arns arn:aws:ec2:us-east-1:211050572089:instance/*
```

---

### Quota increase request denied

**Reasons:**
- Account too new
- Previous quota violations
- AWS service limits

**Solution:**
- Contact AWS Support
- Provide business justification
- May take 24-48 hours

---

## Summary

**Easiest Approach for CCA:**

1. **Permission Boundary** (one-time setup)
   - Defines maximum permissions
   - Blocks dangerous operations
   - Easy to create and apply

2. **Service Quotas** (one-time setup)
   - Hard limits on resource counts
   - Built-in AWS feature
   - Easy to adjust

3. **Required Tags** (enforce with policy)
   - Track resource ownership
   - Easy cost allocation
   - Simple to audit

**Management Overhead:**
- Initial setup: 1-2 hours
- Ongoing: < 30 minutes per month
- Per-user setup: < 5 minutes

**This gives you:**
- ✅ Admin-like access (within boundaries)
- ✅ Resource count limits (via quotas)
- ✅ Easy to administer
- ✅ No custom code needed
- ✅ Built-in AWS features only

---

**Document Status:** ✅ Complete
**Last Updated:** 2025-11-10
**Maintained By:** CCA Team
