#!/usr/bin/env python3
"""
Quick test script to verify the setup is correct
"""

import sys
from pathlib import Path

# Add the project root to the Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

def test_imports():
    """Test if all critical imports work"""
    print("=" * 60)
    print("Testing imports...")
    print("=" * 60)
    
    try:
        print("\n✓ Testing read_env_var...")
        from sttm_to_notebook_generator_integrated.read_env_var import (
            AZURE_OPENAI_ENDPOINT,
            AZURE_OPENAI_DEPLOYMENT,
            AZURE_OPENAI_API_VERSION,
            AZURE_OPENAI_API_KEY,
            rootContext
        )
        print(f"  ├─ Endpoint: {AZURE_OPENAI_ENDPOINT}")
        print(f"  ├─ Deployment: {AZURE_OPENAI_DEPLOYMENT}")
        print(f"  ├─ API Version: {AZURE_OPENAI_API_VERSION}")
        print(f"  ├─ API Key: {'*' * 20}...{AZURE_OPENAI_API_KEY[-10:] if AZURE_OPENAI_API_KEY else 'NOT SET'}")
        print(f"  └─ Root Context: {rootContext}")
        
        print("\n✓ Testing FastAPI app import...")
        from sttm_to_notebook_generator_integrated.api3_sttm_to_notebook_generator import app
        print(f"  └─ App title: {app.title}")
        
        print("\n✓ Testing langchain_workflow...")
        from notebook_generator_app.llm.langchain_workflow import llm_wrapper
        print(f"  └─ LLM Wrapper loaded successfully")
        
        print("\n✓ Testing api1_json_converter_optimized...")
        from sttm_to_notebook_generator_integrated.api1_json_converter_optimized import app1
        print(f"  └─ API1 Router loaded successfully")
        
        print("\n" + "=" * 60)
        print("✅ All imports successful!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ Import failed: {str(e)}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False

def test_env_file():
    """Test if .env file exists and has required variables"""
    print("\n" + "=" * 60)
    print("Testing .env file...")
    print("=" * 60)
    
    env_file = BASE_DIR / ".env"
    if not env_file.exists():
        print("❌ .env file not found!")
        return False
    
    print("✓ .env file exists")
    
    with open(env_file, 'r') as f:
        content = f.read()
        required_vars = ['endpoint', 'deployment', 'subscription_key', 'api_version']
        missing = []
        for var in required_vars:
            if var not in content:
                missing.append(var)
        
        if missing:
            print(f"⚠ Missing variables in .env: {', '.join(missing)}")
            return False
        else:
            print("✓ All required variables found in .env")
            return True

def test_directories():
    """Test if required directories exist"""
    print("\n" + "=" * 60)
    print("Testing required directories...")
    print("=" * 60)
    
    required_dirs = [
        "sttm_to_notebook_generator_integrated",
        "notebook_generator_app",
        "templates",
        "templates/silver",
        "templates/gold"
    ]
    
    all_exist = True
    for dir_name in required_dirs:
        dir_path = BASE_DIR / dir_name
        if dir_path.exists():
            print(f"✓ {dir_name}/")
        else:
            print(f"❌ {dir_name}/ NOT FOUND")
            all_exist = False
    
    return all_exist

def main():
    print("\n" + "=" * 60)
    print("STTM-to-Notebook Generator - Setup Verification")
    print("=" * 60)
    
    results = {
        "env_file": test_env_file(),
        "directories": test_directories(),
        "imports": test_imports()
    }
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_passed = all(results.values())
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    if all_passed:
        print("\n" + "=" * 60)
        print("✅ Setup verification PASSED!")
        print("=" * 60)
        print("\nYou can now run the application with:")
        print("  python run_app.py")
        print("\nOr directly with uvicorn:")
        print("  uvicorn sttm_to_notebook_generator_integrated.api3_sttm_to_notebook_generator:app --reload")
        print("\nAccess Swagger UI at:")
        print("  http://localhost:8000/docs")
        print("=" * 60)
        return 0
    else:
        print("\n" + "=" * 60)
        print("❌ Setup verification FAILED!")
        print("=" * 60)
        print("\nPlease fix the issues above before running the application.")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())

