#!/usr/bin/env python3
"""
LinkedIn API Diagnostic Script
Tests your credentials and identifies where the issue is
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

def test_linkedin_credentials():
    """Test LinkedIn credentials step by step"""
    
    print("\n" + "="*60)
    print("LinkedIn API Diagnostic")
    print("="*60)
    
    # Check environment variables
    client_id = os.getenv("LINKEDIN_CLIENT_ID")
    client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
    access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    
    print("\n1️⃣ Checking Environment Variables...")
    print(f"   LINKEDIN_CLIENT_ID: {'✅ Set' if client_id else '❌ Missing'}")
    print(f"   LINKEDIN_CLIENT_SECRET: {'✅ Set' if client_secret else '❌ Missing'}")
    print(f"   LINKEDIN_ACCESS_TOKEN: {'✅ Set' if access_token else '❌ Missing'}")
    
    if not access_token:
        print("\n❌ No access token found. Cannot proceed.")
        return
    
    # Test token with userinfo endpoint (OpenID Connect)
    print("\n2️⃣ Testing token with /v2/userinfo...")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(
        "https://api.linkedin.com/v2/userinfo",
        headers=headers
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        userinfo = response.json()
        print(f"   ✅ Token is valid!")
        print(f"   Name: {userinfo.get('name', 'N/A')}")
        print(f"   Email: {userinfo.get('email', 'N/A')}")
        
        # The 'sub' field is the person ID
        sub = userinfo.get('sub')
        print(f"   Sub (Person ID): {sub}")
        
        if sub:
            person_urn = f"urn:li:person:{sub}"
            print(f"   ✅ Person URN: {person_urn}")
        else:
            print("   ❌ No 'sub' field in response - this is the problem!")
            print(f"   Full response: {userinfo}")
    elif response.status_code == 401:
        print("   ❌ 401 Unauthorized - Token is invalid or expired")
        print("   You need to generate a new access token")
    else:
        print(f"   ❌ Error: {response.status_code}")
        print(f"   Response: {response.text}")
    
    # Also try the legacy /v2/me endpoint
    print("\n3️⃣ Testing token with /v2/me (legacy)...")
    response = requests.get(
        "https://api.linkedin.com/v2/me",
        headers=headers
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        profile = response.json()
        print(f"   ✅ /v2/me works!")
        person_id = profile.get('id')
        print(f"   ID: {person_id}")
        print(f"   Person URN: urn:li:person:{person_id}")
    elif response.status_code == 403:
        print("   ❌ 403 Forbidden - Missing r_liteprofile scope")
        print("   This is OK if /v2/userinfo worked")
    else:
        print(f"   Response: {response.text[:200]}")
    
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    
    if response.status_code == 200 or (userinfo and userinfo.get('sub')):
        print("\n✅ Your LinkedIn credentials are working!")
        print("\nThe person URN should be:")
        if userinfo and userinfo.get('sub'):
            print(f"   urn:li:person:{userinfo.get('sub')}")
        print("\nMake sure your LinkedIn poster code is using /v2/userinfo")
        print("to get the 'sub' field for the person ID.")
    else:
        print("\n❌ There's an issue with your credentials")
        print("\nPossible fixes:")
        print("1. Generate a new access token (they expire after 60 days)")
        print("2. Make sure you requested the correct scopes:")
        print("   - openid")
        print("   - profile") 
        print("   - w_member_social")


if __name__ == "__main__":
    test_linkedin_credentials()



