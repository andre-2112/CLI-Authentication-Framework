#!/usr/bin/env python3
"""
Test script to test user registration flow
"""

import json
import requests
import time
from datetime import datetime

# Get Lambda function URL
LAMBDA_URL = "https://bbsv5ycsxdpxh4y6lh6cmyjgmy0yxkqq.lambda-url.us-east-1.on.aws/"

def test_registration():
    """Test user registration flow"""
    print("=== Testing User Registration ===\n")

    # Generate test user with timestamp
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    test_email = f"test-{timestamp}@example.com"
    test_first_name = "Test"
    test_last_name = f"User{timestamp}"

    print(f"[TEST] Registering new user: {test_email}")

    # Prepare registration data
    registration_data = {
        "action": "register",
        "email": test_email,
        "firstName": test_first_name,
        "lastName": test_last_name
    }

    try:
        # Send registration request
        response = requests.post(
            LAMBDA_URL,
            json=registration_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )

        print(f"[INFO] HTTP Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"[OK] Registration response: {json.dumps(result, indent=2)}")

            if result.get('success'):
                print(f"\n[SUCCESS] User registration submitted successfully!")
                print(f"  - Email: {test_email}")
                print(f"  - Status: {result.get('status', 'pending')}")
                print(f"  - Message: {result.get('message', 'N/A')}")
                return True
            else:
                print(f"\n[FAILED] Registration failed: {result.get('message', 'Unknown error')}")
                return False
        else:
            print(f"[ERROR] Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"\n[ERROR] Registration test failed: {e}")
        return False

if __name__ == '__main__':
    import sys
    success = test_registration()
    sys.exit(0 if success else 1)
