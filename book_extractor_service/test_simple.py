#!/usr/bin/env python3
"""
Simple test script to verify book extractor structure
"""

import sys
from pathlib import Path

def test_file_structure():
    """Test that all required files exist"""
    required_files = [
        "vertex/__init__.py",
        "vertex/extractor.py",
        "vertex/subject_mapper.py",
        "main.py",
        "Dockerfile",
        "README.md"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files exist")
        return True

def test_main_endpoints():
    """Test that main.py has all required endpoints"""
    try:
        with open('main.py', 'r') as f:
            content = f.read()
        
        required_endpoints = [
            '@app.route(\'/health\'',
            '@app.route(\'/extract-questions\'',
            '@app.route(\'/extract-answers\'',
            '@app.route(\'/extract-all\'',
            '@app.route(\'/subjects\''
        ]
        
        missing_endpoints = []
        for endpoint in required_endpoints:
            if endpoint not in content:
                missing_endpoints.append(endpoint)
        
        if missing_endpoints:
            print(f"❌ Missing endpoints: {missing_endpoints}")
            return False
        else:
            print("✅ All required endpoints present")
            return True
            
    except Exception as e:
        print(f"❌ Endpoint test failed: {e}")
        return False

def test_subject_mapper_structure():
    """Test subject mapper file structure"""
    try:
        with open('vertex/subject_mapper.py', 'r') as f:
            content = f.read()
        
        required_components = [
            'class SubjectExtractor',
            'class ComputerApplicationExtractor',
            'class MathExtractor',
            'class SubjectExtractorFactory',
            'def get_extractor',
            'def get_available_subjects'
        ]
        
        missing_components = []
        for component in required_components:
            if component not in content:
                missing_components.append(component)
        
        if missing_components:
            print(f"❌ Missing components in subject_mapper.py: {missing_components}")
            return False
        else:
            print("✅ Subject mapper structure looks good")
            return True
            
    except Exception as e:
        print(f"❌ Subject mapper test failed: {e}")
        return False

def test_dockerfile():
    """Test Dockerfile structure"""
    try:
        with open('Dockerfile', 'r') as f:
            content = f.read()
        
        required_components = [
            'FROM python:3.11-slim',
            'COPY requirements.txt',
            'pip install',
            'COPY . .',
            'EXPOSE 8080',
            'CMD ["python", "main.py"]'
        ]
        
        missing_components = []
        for component in required_components:
            if component not in content:
                missing_components.append(component)
        
        if missing_components:
            print(f"❌ Missing components in Dockerfile: {missing_components}")
            return False
        else:
            print("✅ Dockerfile structure looks good")
            return True
            
    except Exception as e:
        print(f"❌ Dockerfile test failed: {e}")
        return False

def test_workflow_files():
    """Test that workflow files exist"""
    workflow_files = [
        "../.github/workflows/deploy-book-extractor.yml",
        "book_extraction_workflow.yaml",
        "update_book_extractor_urls.py"
    ]
    
    missing_files = []
    for file_path in workflow_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing workflow files: {missing_files}")
        return False
    else:
        print("✅ All workflow files exist")
        return True

def main():
    """Run simple tests"""
    print("🧪 Book Extractor Simple Tests")
    print("=" * 35)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Main Endpoints", test_main_endpoints),
        ("Subject Mapper", test_subject_mapper_structure),
        ("Dockerfile", test_dockerfile),
        ("Workflow Files", test_workflow_files),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}")
        print("-" * 25)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All simple tests passed!")
        print("✅ Book extractor structure is ready for deployment!")
        print("\n📋 Next steps:")
        print("1. Deploy to Cloud Run using GitHub Actions")
        print("2. Update workflow URLs after deployment")
        print("3. Test the deployed service")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
