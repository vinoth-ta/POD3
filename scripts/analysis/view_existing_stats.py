#!/usr/bin/env python3
"""
Existing Stats Viewer for STTM-to-Notebook Generator
Analyzes and displays statistics from previous test runs
"""

import json
import os
from pathlib import Path
from datetime import datetime
import glob

class ExistingStatsViewer:
    def __init__(self):
        self.results_dir = Path("tests/results")
        self.data_dir = Path("data/responses")
        
    def find_latest_results(self):
        """Find the most recent test results"""
        # Look for version stats files
        stats_files = list(self.results_dir.glob("version_stats_*.json"))
        if stats_files:
            latest_stats = max(stats_files, key=os.path.getctime)
            return latest_stats
        
        # Look for individual version results
        v1_0_0_files = list(self.results_dir.glob("test_results_v1.0.0_*.json"))
        v1_1_0_files = list(self.results_dir.glob("test_results_v1.1.0_*.json"))
        
        if v1_0_0_files and v1_1_0_files:
            latest_v1_0_0 = max(v1_0_0_files, key=os.path.getctime)
            latest_v1_1_0 = max(v1_1_0_files, key=os.path.getctime)
            return latest_v1_0_0, latest_v1_1_0
        
        return None
    
    def load_existing_responses(self):
        """Load existing response files from data/responses"""
        v1_0_0_file = self.data_dir / "v1.0.0_response.json"
        v1_1_0_file = self.data_dir / "v1.1.0_response.json"
        
        responses = {}
        
        if v1_0_0_file.exists():
            with open(v1_0_0_file, 'r') as f:
                responses["v1.0.0"] = json.load(f)
        
        if v1_1_0_file.exists():
            with open(v1_1_0_file, 'r') as f:
                responses["v1.1.0"] = json.load(f)
        
        return responses
    
    def analyze_response_differences(self, v1_0_0_response, v1_1_0_response):
        """Analyze differences between two responses"""
        analysis = {
            "response_size": {
                "v1.0.0": len(json.dumps(v1_0_0_response)),
                "v1.1.0": len(json.dumps(v1_1_0_response)),
                "difference": len(json.dumps(v1_1_0_response)) - len(json.dumps(v1_0_0_response))
            },
            "notebook_content": {
                "v1.0.0_length": len(v1_0_0_response.get("data", "")),
                "v1.1.0_length": len(v1_1_0_response.get("data", "")),
                "length_difference": len(v1_1_0_response.get("data", "")) - len(v1_0_0_response.get("data", ""))
            },
            "success_status": {
                "v1.0.0": v1_0_0_response.get("success", False),
                "v1.1.0": v1_1_0_response.get("success", False)
            }
        }
        
        return analysis
    
    def display_existing_analysis(self):
        """Display existing analysis from docs"""
        analysis_files = [
            "docs/analysis/version_comparison_analysis.md",
            "docs/analysis/comprehensive_technical_analysis.md",
            "docs/analysis/token_analysis_report.md"
        ]
        
        print("📚 EXISTING ANALYSIS DOCUMENTS")
        print("=" * 50)
        
        for file_path in analysis_files:
            if Path(file_path).exists():
                print(f"📄 {file_path}")
                with open(file_path, 'r') as f:
                    content = f.read()
                    # Extract key metrics
                    if "Performance Improvements" in content:
                        print("   ✅ Contains performance analysis")
                    if "Token Usage" in content:
                        print("   ✅ Contains token analysis")
                    if "SQL Generation" in content:
                        print("   ✅ Contains SQL quality analysis")
            else:
                print(f"❌ {file_path} - Not found")
        
        print()
    
    def display_latest_results(self):
        """Display the most recent test results"""
        latest_results = self.find_latest_results()
        
        if not latest_results:
            print("❌ No recent test results found")
            return
        
        print("📊 LATEST TEST RESULTS")
        print("=" * 50)
        
        if isinstance(latest_results, tuple):
            # Individual version files
            v1_0_0_file, v1_1_0_file = latest_results
            print(f"📄 V1.0.0 Results: {v1_0_0_file.name}")
            print(f"📄 V1.1.0 Results: {v1_1_0_file.name}")
            
            # Load and display basic info
            with open(v1_0_0_file, 'r') as f:
                v1_0_0_data = json.load(f)
            with open(v1_1_0_file, 'r') as f:
                v1_1_0_data = json.load(f)
            
            print(f"📅 V1.0.0 Test Date: {v1_0_0_file.stem.split('_')[-2:]}")
            print(f"📅 V1.1.0 Test Date: {v1_1_0_file.stem.split('_')[-2:]}")
            
        else:
            # Combined stats file
            print(f"📄 Combined Results: {latest_results.name}")
            
            with open(latest_results, 'r') as f:
                data = json.load(f)
            
            print(f"📅 Test Date: {data.get('timestamp', 'Unknown')}")
            
            if 'statistics' in data:
                stats = data['statistics']
                for version, version_stats in stats.items():
                    print(f"\n📋 {version.upper()}:")
                    print(f"   Total Runs: {version_stats.get('total_runs', 0)}")
                    print(f"   Success Count: {version_stats.get('success_count', 0)}")
                    print(f"   Error Count: {version_stats.get('error_count', 0)}")
                    
                    if 'timing_stats' in version_stats:
                        timing = version_stats['timing_stats']
                        print(f"   Mean Time: {timing.get('mean', 0):.2f}s")
                        print(f"   Std Dev: {timing.get('std_dev', 0):.2f}s")
        
        print()
    
    def display_response_comparison(self):
        """Display comparison of existing responses"""
        responses = self.load_existing_responses()
        
        if not responses:
            print("❌ No existing response files found")
            return
        
        print("📄 EXISTING RESPONSE COMPARISON")
        print("=" * 50)
        
        if "v1.0.0" in responses and "v1.1.0" in responses:
            analysis = self.analyze_response_differences(
                responses["v1.0.0"], 
                responses["v1.1.0"]
            )
            
            print("📊 Response Size Analysis:")
            print(f"   V1.0.0: {analysis['response_size']['v1.0.0']:,} bytes")
            print(f"   V1.1.0: {analysis['response_size']['v1.1.0']:,} bytes")
            print(f"   Difference: {analysis['response_size']['difference']:,} bytes")
            
            print("\n📝 Notebook Content Analysis:")
            print(f"   V1.0.0 Length: {analysis['notebook_content']['v1.0.0_length']:,} characters")
            print(f"   V1.1.0 Length: {analysis['notebook_content']['v1.1.0_length']:,} characters")
            print(f"   Length Difference: {analysis['notebook_content']['length_difference']:,} characters")
            
            print("\n✅ Success Status:")
            print(f"   V1.0.0: {analysis['success_status']['v1.0.0']}")
            print(f"   V1.1.0: {analysis['success_status']['v1.1.0']}")
            
        elif "v1.0.0" in responses:
            print("📄 V1.0.0 Response Available")
            print(f"   Size: {len(json.dumps(responses['v1.0.0'])):,} bytes")
            print(f"   Success: {responses['v1.0.0'].get('success', False)}")
            
        elif "v1.1.0" in responses:
            print("📄 V1.1.0 Response Available")
            print(f"   Size: {len(json.dumps(responses['v1.1.0'])):,} bytes")
            print(f"   Success: {responses['v1.1.0'].get('success', False)}")
        
        print()
    
    def show_summary(self):
        """Show a summary of all available statistics"""
        print("🚀 STTM-to-Notebook Generator: Existing Statistics Summary")
        print("=" * 70)
        
        # Check what's available
        has_results = self.find_latest_results() is not None
        has_responses = len(self.load_existing_responses()) > 0
        has_analysis = any(Path(f).exists() for f in [
            "docs/analysis/version_comparison_analysis.md",
            "docs/analysis/comprehensive_technical_analysis.md",
            "docs/analysis/token_analysis_report.md"
        ])
        
        print("📋 Available Data:")
        print(f"   📊 Test Results: {'✅ Available' if has_results else '❌ Not found'}")
        print(f"   📄 Response Files: {'✅ Available' if has_responses else '❌ Not found'}")
        print(f"   📚 Analysis Docs: {'✅ Available' if has_analysis else '❌ Not found'}")
        
        print("\n" + "=" * 70)
        
        if has_results:
            self.display_latest_results()
        
        if has_responses:
            self.display_response_comparison()
        
        if has_analysis:
            self.display_existing_analysis()
        
        print("🎯 Next Steps:")
        print("   1. Run 'python extract_version_stats.py' for fresh statistics")
        print("   2. Run 'python run_parallel.py' to test both versions")
        print("   3. Check the generated reports in tests/results/")

def main():
    viewer = ExistingStatsViewer()
    viewer.show_summary()

if __name__ == "__main__":
    main() 