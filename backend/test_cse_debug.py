"""
CSE Diagnostic Tool
Isolates whether the issue is the API Key or the CSE ID.
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = (os.getenv("GOOGLE_CSE_API_KEY") or "").strip()
CSE_ID = (os.getenv("GOOGLE_CSE_ID") or "").strip()

print("="*60)
print("CSE DIAGNOSTIC TOOL")
print("="*60)
print(f"API Key: {API_KEY[:5]}...{API_KEY[-4:] if len(API_KEY)>5 else ''}")
print(f"CSE ID:  {CSE_ID}")
print("-" * 60)

def test_api_key_only():
    """Test API key with a dummy request to check validity."""
    print("\nTEST 1: API Key Validity")
    # Using a known public Wikipedia CSE ID just to test the key
    # (Note: sometimes this still requires project linkage, but worth a shot)
    wiki_cse = "000888210889775888983:tb8wohhc_m4" 
    
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": API_KEY,
        "cx": wiki_cse,
        "q": "test"
    }
    
    res = requests.get(url, params=params)
    if res.status_code == 200:
        print("✅ API Key is VALID (authorized to make requests)")
        return True
    elif res.status_code == 403:
        print("❌ API Key is INVALID or not enabled for Custom Search API")
        print(f"   Reason: {res.json().get('error', {}).get('message')}")
        return False
    else:
        print(f"⚠️ Unexpected status with public CSE: {res.status_code}")
        print(res.text)
        return True # Assume key is ok, might be other issue

def test_your_cse():
    """Test your specific CSE ID."""
    print("\nTEST 2: Your CSE Configuration")
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": API_KEY,
        "cx": CSE_ID,
        "q": "test"
    }
    
    res = requests.get(url, params=params)
    if res.status_code == 200:
        print("✅ Your CSE ID is configured correctly!")
    elif res.status_code == 404:
        print("❌ CSE ID Error (404 Not Found)")
        print("   DIAGNOSIS: The CSE ID is incorrect OR unrelated to the API Key's project.")
        print("   1. Check if CSE ID is copied correctly from Control Panel")
        print("   2. Ensure 'Search the entire web' is ON")
    elif res.status_code == 403:
         print("❌ Permission Error")
         print(f"   Reason: {res.json().get('error', {}).get('message')}")
    else:
        print(f"❌ Error {res.status_code}")
        print(res.text)

if __name__ == "__main__":
    if test_api_key_only():
        test_your_cse()
