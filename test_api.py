"""
Test script for RTI-Lens API endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8001"

def test_health():
    """Test health check endpoint"""
    print("Testing /health...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")

def test_denial_rates():
    """Test denial rates endpoint"""
    print("Testing /api/analytics/denial-rates...")
    response = requests.get(f"{BASE_URL}/api/analytics/denial-rates")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Found {len(data)} ministries")
    if data:
        print(f"Sample: {data[0]}\n")

def test_section_heatmap():
    """Test section heatmap endpoint"""
    print("Testing /api/analytics/section-heatmap...")
    response = requests.get(f"{BASE_URL}/api/analytics/section-heatmap")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Found {len(data)} section-ministry combinations")
    if data:
        print(f"Sample: {data[0]}\n")

def test_override_trend():
    """Test override trend endpoint"""
    print("Testing /api/analytics/override-trend...")
    response = requests.get(f"{BASE_URL}/api/analytics/override-trend")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Found {len(data)} time periods")
    if data:
        print(f"Sample: {data[0]}\n")

def test_predict():
    """Test prediction endpoint"""
    print("Testing /api/predict...")
    payload = {
        "ministry": "Ministry of Finance",
        "section_cited": "8(1)(j)",
        "appeal_level": "second_appeal",
        "order_date": "2023-01-15",
        "raw_text": "The appellant sought information regarding file notings and internal communications. The PIO denied the request citing Section 8(1)(j) claiming it would impede the process of investigation."
    }
    response = requests.post(f"{BASE_URL}/api/predict", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")

def test_qa():
    """Test Q&A endpoint"""
    print("Testing /api/qa...")
    payload = {
        "question": "What are common reasons for Section 8(1)(j) being overturned?",
        "top_k": 5
    }
    response = requests.post(f"{BASE_URL}/api/qa", json=payload)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Answer: {data.get('answer', '')[:200]}...")
    print(f"Sources: {len(data.get('sources', []))}\n")

def test_draft():
    """Test draft generation endpoint"""
    print("Testing /api/draft...")
    payload = {
        "ministry": "Ministry of Finance",
        "section_cited": "8(1)(j)",
        "context": "I requested information about loan sanctions but was denied under Section 8(1)(j). The PIO claimed it would harm the decision-making process, but I believe this is a misuse of the exemption."
    }
    response = requests.post(f"{BASE_URL}/api/draft", json=payload)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Draft length: {len(data.get('draft', ''))} characters")
    print(f"Suggestions: {len(data.get('suggestions', []))}\n")

if __name__ == "__main__":
    print("=" * 60)
    print("RTI-Lens API Test Suite")
    print("=" * 60 + "\n")

    print("Make sure the API is running: python3 backend/main.py\n")

    try:
        test_health()
        test_denial_rates()
        test_section_heatmap()
        test_override_trend()
        test_predict()
        test_qa()
        test_draft()

        print("=" * 60)
        print("✅ Basic tests completed successfully!")
        print("=" * 60)

    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API. Make sure it's running.")
    except Exception as e:
        print(f"❌ Error: {e}")
