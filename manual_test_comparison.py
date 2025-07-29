#!/usr/bin/env python3
"""
Manual Test Comparison Script for STTM-to-Notebook Generator
Guides through manual testing of v1.0.0 vs v1.1.0
"""

import json
import subprocess
import time
import requests
from datetime import datetime
import os

class ManualVersionTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_data = {
            "sttm_metadata_json": '[{"file_name":"Corporate_Social_Responsibility_XTNElectricityBasedEmission_multi_source_same_column.xlsx","sheet_name":"Enablon_myEHS_ElectriciEmission","table_name":"XTNElectricityBasedEmission_multi_source_same_column","target_table_name":"XTNElectricityBasedEmission"}]',
            "notebook_metadata_json": '{"user_id":"vinoth.premkumar","table_load_type":"silver","domain":"corporate_social_responsibility","product":"emissions_tracking","notebook_name":"XTNElectricityBasedEmission_multi_source_same_column_etl_notebook"}',
            "sttm_file": "sample STTM/Corporate_Social_Responsibility_XTNElectricityBasedEmission_multi_source_same_column.xlsx"
        }
        
    def switch_to_version(self, version):
        """Switch to specific git version"""
        print(f"\n🔄 Switching to version {version}...")
        subprocess.run(["git", "checkout", version], check=True)
        print(f"✅ Switched to {version}")
        
    def save_results(self, version, results):
        """Save test results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"manual_test_results_{version}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"💾 Results saved to {filename}")
        return filename
    
    def test_api_manual(self):
        """Manual API test with curl command"""
        print("🧪 Testing API endpoint with curl...")
        
        curl_command = f'''curl -X POST "{self.base_url}/None/api/v1/edf/genai/codegenservices/from-sttm-generate-notebook" \\
  -F "sttm_metadata_json={self.test_data['sttm_metadata_json']}" \\
  -F "notebook_metadata_json={self.test_data['notebook_metadata_json']}" \\
  -F "sttm_files=@{self.test_data['sttm_file']}"'''
        
        print(f"Running: {curl_command}")
        
        try:
            result = subprocess.run(curl_command, shell=True, capture_output=True, text=True, timeout=180)
            
            return {
                'status_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'command': curl_command
            }
            
        except subprocess.TimeoutExpired:
            return {
                'status_code': 'TIMEOUT',
                'stdout': '',
                'stderr': 'Request timed out after 3 minutes',
                'command': curl_command
            }
        except Exception as e:
            return {
                'status_code': 'ERROR',
                'stdout': '',
                'stderr': str(e),
                'command': curl_command
            }

def main():
    tester = ManualVersionTester()
    
    print("🧪 MANUAL STTM-to-Notebook Generator Version Comparison Test")
    print("=" * 70)
    print("This script will guide you through testing each version manually.")
    print("You'll need to start the server manually for each version.")
    
    # Test v1.0.0
    print("\n📋 STEP 1: TESTING VERSION 1.0.0 (Original)")
    print("-" * 50)
    
    tester.switch_to_version("v1.0.0")
    
    print("\n🚀 MANUAL STEP: Please start the server for v1.0.0")
    print("Run this command in a new terminal:")
    print("uvicorn sttm_to_notebook_generator_integrated.api3_sttm_to_notebook_generator:app --host 0.0.0.0 --port 8000 --reload")
    
    input("\n⏳ Press Enter when the server is running and ready...")
    
    results_v1 = tester.test_api_manual()
    filename_v1 = tester.save_results("v1.0.0", results_v1)
    
    print(f"\n✅ v1.0.0 test completed.")
    print(f"Status: {results_v1['status_code']}")
    if results_v1['stdout']:
        print(f"Response length: {len(results_v1['stdout'])} characters")
    
    input("\n⏳ Press Enter to continue to v1.1.0 test...")
    
    # Test v1.1.0
    print("\n📋 STEP 2: TESTING VERSION 1.1.0 (Optimized)")
    print("-" * 50)
    
    tester.switch_to_version("v1.1.0")
    
    print("\n🚀 MANUAL STEP: Please start the server for v1.1.0")
    print("Run this command in a new terminal:")
    print("uvicorn sttm_to_notebook_generator_integrated.api3_sttm_to_notebook_generator:app --host 0.0.0.0 --port 8000 --reload")
    
    input("\n⏳ Press Enter when the server is running and ready...")
    
    results_v2 = tester.test_api_manual()
    filename_v2 = tester.save_results("v1.1.0", results_v2)
    
    print(f"\n✅ v1.1.0 test completed.")
    print(f"Status: {results_v2['status_code']}")
    if results_v2['stdout']:
        print(f"Response length: {len(results_v2['stdout'])} characters")
    
    # Compare results
    print("\n📊 COMPARISON RESULTS:")
    print("=" * 50)
    print(f"v1.0.0 Status: {results_v1['status_code']}")
    print(f"v1.1.0 Status: {results_v2['status_code']}")
    
    if results_v1['stdout'] and results_v2['stdout']:
        v1_length = len(results_v1['stdout'])
        v2_length = len(results_v2['stdout'])
        print(f"\nv1.0.0 Response Length: {v1_length} characters")
        print(f"v1.1.0 Response Length: {v2_length} characters")
        print(f"Length Difference: {v2_length - v1_length} characters")
        
        # Check if responses are identical
        if results_v1['stdout'] == results_v2['stdout']:
            print("🔍 Responses are IDENTICAL")
        else:
            print("🔍 Responses are DIFFERENT")
    
    print("=" * 50)
    
    # Switch back to main branch
    tester.switch_to_version("main")
    
    print(f"\n🎉 Manual comparison test completed!")
    print(f"📁 Results saved: {filename_v1}, {filename_v2}")
    print("\n📝 Next steps:")
    print("1. Review the saved JSON files for detailed responses")
    print("2. Compare the notebook content between versions")
    print("3. Check for any differences in JSON STTM generation")

if __name__ == "__main__":
    main() 