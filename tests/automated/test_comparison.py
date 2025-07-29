#!/usr/bin/env python3
"""
Test Comparison Script for STTM-to-Notebook Generator
Compares outputs between v1.0.0 and v1.1.0
"""

import json
import subprocess
import time
import requests
from datetime import datetime
import os

class VersionTester:
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
        
    def start_server(self):
        """Start the FastAPI server"""
        print("🚀 Starting server...")
        # Kill any existing process on port 8000
        subprocess.run(["lsof", "-ti:8000"], capture_output=True)
        subprocess.run(["lsof", "-ti:8000", "|", "xargs", "kill", "-9"], shell=True, capture_output=True)
        
        # Start server in background
        process = subprocess.Popen([
            "uvicorn", "sttm_to_notebook_generator_integrated.api3_sttm_to_notebook_generator:app",
            "--host", "0.0.0.0", "--port", "8000"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        time.sleep(5)
        return process
        
    def test_api(self):
        """Test the API endpoint"""
        print("🧪 Testing API endpoint...")
        
        try:
            with open(self.test_data["sttm_file"], 'rb') as f:
                files = {'sttm_files': f}
                data = {
                    'sttm_metadata_json': self.test_data["sttm_metadata_json"],
                    'notebook_metadata_json': self.test_data["notebook_metadata_json"]
                }
                
                response = requests.post(
                    f"{self.base_url}/None/api/v1/edf/genai/codegenservices/from-sttm-generate-notebook",
                    files=files,
                    data=data,
                    timeout=120
                )
                
                return {
                    'status_code': response.status_code,
                    'response': response.json() if response.status_code == 200 else response.text,
                    'headers': dict(response.headers)
                }
                
        except Exception as e:
            return {
                'status_code': 'ERROR',
                'response': str(e),
                'headers': {}
            }
    
    def save_results(self, version, results):
        """Save test results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results_{version}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"💾 Results saved to {filename}")
        return filename
    
    def compare_results(self, v1_results, v2_results):
        """Compare results between versions"""
        print("\n📊 COMPARISON RESULTS:")
        print("=" * 50)
        
        # Compare status codes
        print(f"Status Code - v1.0.0: {v1_results['status_code']}")
        print(f"Status Code - v1.1.0: {v2_results['status_code']}")
        
        # Compare response structure
        if isinstance(v1_results['response'], dict) and isinstance(v2_results['response'], dict):
            print(f"\nResponse Keys - v1.0.0: {list(v1_results['response'].keys())}")
            print(f"Response Keys - v1.1.0: {list(v2_results['response'].keys())}")
            
            # Compare success status
            v1_success = v1_results['response'].get('success', False)
            v2_success = v2_results['response'].get('success', False)
            print(f"\nSuccess - v1.0.0: {v1_success}")
            print(f"Success - v1.1.0: {v2_success}")
            
            # Compare notebook content length
            if 'data' in v1_results['response'] and 'data' in v2_results['response']:
                v1_length = len(v1_results['response']['data'])
                v2_length = len(v2_results['response']['data'])
                print(f"\nNotebook Content Length - v1.0.0: {v1_length} characters")
                print(f"Notebook Content Length - v1.1.0: {v2_length} characters")
                print(f"Length Difference: {v2_length - v1_length} characters")
        
        print("=" * 50)

def main():
    tester = VersionTester()
    
    print("🧪 STTM-to-Notebook Generator Version Comparison Test")
    print("=" * 60)
    
    # Test v1.0.0
    print("\n📋 TESTING VERSION 1.0.0 (Original)")
    print("-" * 40)
    
    tester.switch_to_version("v1.0.0")
    server_v1 = tester.start_server()
    
    try:
        results_v1 = tester.test_api()
        filename_v1 = tester.save_results("v1.0.0", results_v1)
        print(f"✅ v1.0.0 test completed. Results: {results_v1['status_code']}")
    except Exception as e:
        print(f"❌ v1.0.0 test failed: {e}")
        results_v1 = {'status_code': 'ERROR', 'response': str(e)}
    finally:
        server_v1.terminate()
        time.sleep(2)
    
    # Test v1.1.0
    print("\n📋 TESTING VERSION 1.1.0 (Optimized)")
    print("-" * 40)
    
    tester.switch_to_version("v1.1.0")
    server_v2 = tester.start_server()
    
    try:
        results_v2 = tester.test_api()
        filename_v2 = tester.save_results("v1.1.0", results_v2)
        print(f"✅ v1.1.0 test completed. Results: {results_v2['status_code']}")
    except Exception as e:
        print(f"❌ v1.1.0 test failed: {e}")
        results_v2 = {'status_code': 'ERROR', 'response': str(e)}
    finally:
        server_v2.terminate()
        time.sleep(2)
    
    # Compare results
    tester.compare_results(results_v1, results_v2)
    
    # Switch back to main branch
    tester.switch_to_version("main")
    
    print("\n🎉 Comparison test completed!")
    print(f"📁 Results saved: {filename_v1}, {filename_v2}")

if __name__ == "__main__":
    main() 