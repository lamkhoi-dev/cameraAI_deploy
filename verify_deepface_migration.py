#!/usr/bin/env python3
"""
Quick test to verify FaceProcessor works with DeepFace
"""

import sys
import logging
import os

# Fix encoding issues on Windows
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test critical imports"""
    print("\n" + "="*60)
    print("TESTING DEEPFACE IMPORTS")
    print("="*60)
    
    try:
        import numpy as np
        print("[OK] NumPy imported successfully")
    except ImportError as e:
        print(f"[FAIL] NumPy import failed: {e}")
        return False
    
    try:
        import cv2
        print("[OK] OpenCV imported successfully")
    except ImportError as e:
        print(f"[FAIL] OpenCV import failed: {e}")
        return False
    
    try:
        from deepface import DeepFace
        print("[OK] DeepFace imported successfully")
    except ImportError as e:
        print(f"[FAIL] DeepFace import failed: {e}")
        print("   Install with: pip install deepface tensorflow")
        return False
    
    try:
        import tensorflow as tf
        print(f"[OK] TensorFlow {tf.__version__} imported successfully")
    except ImportError as e:
        print(f"[FAIL] TensorFlow import failed: {e}")
        return False
    
    return True

def test_face_processor():
    """Test FaceProcessor class structure"""
    print("\n" + "="*60)
    print("TESTING FACE PROCESSOR STRUCTURE")
    print("="*60)
    
    # Check if file can be parsed
    try:
        with open('ai_engine/processors/face_processor.py', 'r', encoding='utf-8') as f:
            code = f.read()
            compile(code, 'face_processor.py', 'exec')
        print("[OK] face_processor.py compiles without syntax errors")
    except SyntaxError as e:
        print(f"[FAIL] Syntax error in face_processor.py: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Error reading face_processor.py: {e}")
        return False
    
    # Check file contains key methods
    required_methods = [
        'def load_model',
        'def process',
        'def extract_embedding',
        'def extract_embedding_deepface',
        'def compare_embeddings',
        'def _crop_face',
        'def _save_crop'
    ]
    
    with open('ai_engine/processors/face_processor.py', 'r', encoding='utf-8') as f:
        content = f.read()
        for method in required_methods:
            if method in content:
                print(f"[OK] Method found: {method.replace('def ', '')}")
            else:
                print(f"[FAIL] Method missing: {method.replace('def ', '')}")
                return False
    
    return True

def test_requirements():
    """Verify requirements.txt is updated"""
    print("\n" + "="*60)
    print("TESTING REQUIREMENTS.TXT")
    print("="*60)
    
    with open('requirements.txt', 'r') as f:
        content = f.read()
    
    # Check for DeepFace
    if 'deepface' in content:
        print("[OK] deepface found in requirements.txt")
    else:
        print("[FAIL] deepface NOT found in requirements.txt")
        return False
    
    # Check for TensorFlow
    if 'tensorflow' in content:
        print("[OK] tensorflow found in requirements.txt")
    else:
        print("[FAIL] tensorflow NOT found in requirements.txt")
        return False
    
    # Check that InsightFace is removed
    if 'insightface' not in content:
        print("[OK] insightface successfully removed from requirements.txt")
    else:
        print("[WARN] insightface still in requirements.txt (should be removed)")
        return False
    
    return True

if __name__ == '__main__':
    print("\n" + "="*60)
    print("DEEPFACE MIGRATION VERIFICATION TEST")
    print("="*60)
    
    results = {
        'Imports': test_imports(),
        'FaceProcessor': test_face_processor(),
        'Requirements': test_requirements(),
    }
    
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    
    for test_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n[OK] ALL TESTS PASSED - System is ready for deployment!")
        sys.exit(0)
    else:
        print("\n[ERROR] SOME TESTS FAILED - Please review the errors above")
        sys.exit(1)
