#!/usr/bin/env python3
"""
Helper script to save API response to files for inspection
Usage: python save_api_response.py <path_to_response.json>
"""

import json
import sys
from pathlib import Path
from datetime import datetime

def save_response(response_file):
    """Parse API response and save JSON and notebook separately"""

    # Read the response
    with open(response_file, 'r') as f:
        response = json.load(f)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("api_outputs")
    output_dir.mkdir(exist_ok=True)

    # Save JSON mapping if present (from API1)
    if "content" in response and response["content"]:
        json_output_file = output_dir / f"json_mapping_{timestamp}.json"
        with open(json_output_file, 'w') as f:
            json.dump(response["content"], f, indent=2)
        print(f"✅ JSON mapping saved to: {json_output_file}")

    # Save notebook if present (from API2 or full pipeline)
    if "data" in response and response["data"]:
        notebook_file = output_dir / f"generated_notebook_{timestamp}.py"
        with open(notebook_file, 'w') as f:
            f.write(response["data"])
        print(f"✅ Notebook saved to: {notebook_file}")

    # Save full response
    full_response_file = output_dir / f"full_response_{timestamp}.json"
    with open(full_response_file, 'w') as f:
        json.dump(response, f, indent=2)
    print(f"✅ Full response saved to: {full_response_file}")

    print(f"\n📁 All outputs saved in: {output_dir.absolute()}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python save_api_response.py <path_to_response.json>")
        print("\nExample:")
        print("  1. In Swagger UI, copy the response JSON")
        print("  2. Save it to a file (e.g., response.json)")
        print("  3. Run: python save_api_response.py response.json")
        sys.exit(1)

    response_file = sys.argv[1]
    if not Path(response_file).exists():
        print(f"❌ Error: File '{response_file}' not found")
        sys.exit(1)

    save_response(response_file)