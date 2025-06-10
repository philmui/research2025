import os
import requests
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv())

QDRANT_HOSTED_URL = os.environ.get("QDRANT_HOSTED_URL", "")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY", "")
QDRANT_PORT = os.environ.get("QDRANT_PORT", 6333)

print("=== Qdrant Connection Debugging ===")
print(f"Qdrant URL: {QDRANT_HOSTED_URL}")
print(f"Qdrant API Key length: {len(QDRANT_API_KEY)}")
print(f"Qdrant Port: {QDRANT_PORT}")
print()

# Test 1: Basic URL validation
print("=== Test 1: URL Validation ===")
if not QDRANT_HOSTED_URL:
    print("❌ QDRANT_HOSTED_URL is empty!")
elif not QDRANT_HOSTED_URL.startswith(('http://', 'https://')):
    print("⚠️  URL doesn't start with http:// or https://")
else:
    print("✅ URL format looks correct")
print()

# Test 2: Basic HTTP connectivity
print("=== Test 2: Basic HTTP Connectivity ===")
try:
    # Try a basic GET request to the root
    response = requests.get(QDRANT_HOSTED_URL, 
                          headers={'api-key': QDRANT_API_KEY} if QDRANT_API_KEY else {},
                          timeout=10)
    print(f"✅ HTTP response received: {response.status_code}")
    print(f"Response content: {response.text[:200]}...")
except requests.exceptions.ConnectionError as e:
    print(f"❌ Connection error: {e}")
except requests.exceptions.Timeout:
    print("❌ Request timed out")
except Exception as e:
    print(f"❌ Other error: {e}")
print()

# Test 3: Try Qdrant health endpoint
print("=== Test 3: Qdrant Health Check ===")
try:
    health_url = QDRANT_HOSTED_URL.rstrip('/') + '/health'
    response = requests.get(health_url,
                          headers={'api-key': QDRANT_API_KEY} if QDRANT_API_KEY else {},
                          timeout=10)
    print(f"Health check status: {response.status_code}")
    print(f"Health response: {response.text}")
except Exception as e:
    print(f"❌ Health check failed: {e}")
print()

# Test 4: Try collections endpoint
print("=== Test 4: Collections Endpoint ===")
try:
    collections_url = QDRANT_HOSTED_URL.rstrip('/') + '/collections'
    response = requests.get(collections_url,
                          headers={'api-key': QDRANT_API_KEY} if QDRANT_API_KEY else {},
                          timeout=10)
    print(f"Collections endpoint status: {response.status_code}")
    print(f"Collections response: {response.text[:500]}...")
except Exception as e:
    print(f"❌ Collections endpoint failed: {e}")
print()

# Test 5: Try with different URL variations
print("=== Test 5: URL Variations ===")
base_urls_to_try = [
    QDRANT_HOSTED_URL,
    QDRANT_HOSTED_URL.rstrip('/'),
    f"{QDRANT_HOSTED_URL}:{QDRANT_PORT}" if not str(QDRANT_PORT) in QDRANT_HOSTED_URL else QDRANT_HOSTED_URL
]

for url in set(base_urls_to_try):  # Remove duplicates
    try:
        print(f"Trying URL: {url}")
        response = requests.get(url + '/health',
                              headers={'api-key': QDRANT_API_KEY} if QDRANT_API_KEY else {},
                              timeout=5)
        print(f"  ✅ Success: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Failed: {str(e)[:100]}...")
print()

print("=== Recommendations ===")
print("1. Verify your Qdrant URL is correct and accessible")
print("2. Check if Qdrant service is running")
print("3. Ensure your API key is valid")
print("4. Try accessing the Qdrant web UI in your browser")
print("5. Consider using a local Qdrant instance for testing") 