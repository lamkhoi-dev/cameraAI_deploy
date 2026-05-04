#!/usr/bin/env python3
"""
FaceID Implementation Test Script
Tests all FaceID endpoints and components
"""

import requests
import json
from pathlib import Path
import sys

# Configuration
API_BASE_URL = "http://localhost:5000"
TEST_RESULTS = []

def test(name, func):
    """Run a test and record result"""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print('='*60)
    try:
        result = func()
        status = "✓ PASS" if result else "✗ FAIL"
        TEST_RESULTS.append((name, status))
        print(f"\n{status}: {name}")
        return result
    except Exception as e:
        TEST_RESULTS.append((name, "✗ ERROR"))
        print(f"\n✗ ERROR: {str(e)}")
        return False

def test_api_health():
    """Test if API server is running"""
    try:
        resp = requests.get(f"{API_BASE_URL}/health", timeout=5)
        print(f"API Status: {resp.json()}")
        return resp.status_code == 200
    except Exception as e:
        print(f"Cannot connect to API: {e}")
        return False

def test_faceid_available():
    """Test if FaceID is available"""
    try:
        resp = requests.get(f"{API_BASE_URL}/api/faces/stats")
        if resp.status_code == 501:
            print("⚠️  FaceID not available - dependencies not installed")
            return False
        print(f"FaceID Status: Available")
        print(f"Response: {resp.json()}")
        return resp.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_get_known_faces():
    """Test getting all known faces"""
    try:
        resp = requests.get(f"{API_BASE_URL}/api/faces/known")
        data = resp.json()
        print(f"Total known faces: {data.get('total', 0)}")
        print(f"Response: {json.dumps(data, indent=2)}")
        return resp.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_register_face_embedding():
    """Test registering a face from embedding"""
    try:
        # Create a dummy 512D embedding
        dummy_embedding = [0.1] * 512
        
        payload = {
            "person_id": "test_person_001",
            "embedding": dummy_embedding,
            "metadata": {"name": "Test Person", "age": 30}
        }
        
        resp = requests.post(
            f"{API_BASE_URL}/api/faces/known",
            json=payload
        )
        
        print(f"Response: {resp.json()}")
        success = resp.status_code in [201, 200]
        
        if success:
            print("✓ Face registered successfully")
        
        return success
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_match_face_embedding():
    """Test matching a face embedding"""
    try:
        # Create a similar dummy embedding (should match test_person_001)
        query_embedding = [0.1] * 512
        
        payload = {"embedding": query_embedding}
        
        resp = requests.post(
            f"{API_BASE_URL}/api/faces/match",
            json=payload
        )
        
        data = resp.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        return resp.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_get_face_stats():
    """Test getting face statistics"""
    try:
        resp = requests.get(f"{API_BASE_URL}/api/faces/stats")
        data = resp.json()
        print(f"Stats: {json.dumps(data, indent=2)}")
        return resp.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_persons_with_faces():
    """Test getting persons with face embeddings"""
    try:
        resp = requests.get(f"{API_BASE_URL}/api/faces/persons-with-faces?page=1&per_page=5")
        data = resp.json()
        print(f"Persons with faces: {data.get('total', 0)}")
        print(f"Response keys: {list(data.keys())}")
        return resp.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_remove_face():
    """Test removing a known face"""
    try:
        resp = requests.delete(f"{API_BASE_URL}/api/faces/known/test_person_001")
        print(f"Response: {resp.json()}")
        return resp.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("FaceID IMPLEMENTATION TEST SUITE")
    print("="*60)
    print(f"\nAPI Base URL: {API_BASE_URL}")
    
    # Run tests
    test("API Health Check", test_api_health)
    test("FaceID Availability", test_faceid_available)
    test("Get Known Faces", test_get_known_faces)
    test("Register Face from Embedding", test_register_face_embedding)
    test("Match Face Embedding", test_match_face_embedding)
    test("Get Face Statistics", test_get_face_stats)
    test("Get Persons with Faces", test_persons_with_faces)
    test("Remove Known Face", test_remove_face)
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, status in TEST_RESULTS if "PASS" in status)
    total = len(TEST_RESULTS)
    
    for name, status in TEST_RESULTS:
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({100*passed//total}%)")
    
    if passed == total:
        print("\n✓ All tests passed! FaceID is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
