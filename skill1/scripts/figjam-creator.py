#!/usr/bin/env python3
"""
figjam-creator.py — Create FigJam files via Figma API

Usage:
    python figjam-creator.py --name "TDD-042-v1.0.0 System Architecture" --output ./figjam-info.json
    python figjam-creator.py --name "TDD-042-v1.0.0" --parent-folder "folder-id" --output ./figjam-info.json

Environment:
    FIGMA_TOKEN (required)
"""

import os
import sys
import json
import argparse
from datetime import datetime

try:
    import requests
except ImportError:
    print("ERROR: requests library required. Install: pip install requests")
    sys.exit(1)

FIGMA_API_BASE = "https://api.figma.com/v1"


def create_figjam_file(name: str, token: str, parent_folder: str = None) -> dict:
    """Create a new FigJam file via Figma API."""
    headers = {
        "X-Figma-Token": token,
        "Content-Type": "application/json"
    }
    payload = {
        "name": name,
        "editor_type": "figjam"
    }
    if parent_folder:
        payload["parent_folder"] = parent_folder

    response = requests.post(f"{FIGMA_API_BASE}/files", headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


def get_file_info(file_key: str, token: str) -> dict:
    """Get file metadata."""
    headers = {"X-Figma-Token": token}
    response = requests.get(f"{FIGMA_API_BASE}/files/{file_key}", headers=headers)
    response.raise_for_status()
    return response.json()


def main():
    parser = argparse.ArgumentParser(description="Create FigJam files")
    parser.add_argument("--name", "-n", required=True, help="FigJam file name")
    parser.add_argument("--parent-folder", help="Parent folder ID (optional)")
    parser.add_argument("--output", "-o", default="figjam-info.json", help="Output JSON file")
    args = parser.parse_args()

    token = os.environ.get("FIGMA_TOKEN")
    if not token:
        print("ERROR: FIGMA_TOKEN environment variable not set")
        sys.exit(1)

    print(f"Creating FigJam file: {args.name}")

    try:
        result = create_figjam_file(args.name, token, args.parent_folder)
        file_key = result.get("file_key")
        file_url = f"https://www.figma.com/file/{file_key}"

        print(f"  ✅ FigJam created: {file_url}")

        output = {
            "figjam": {
                "name": args.name,
                "file_key": file_key,
                "file_url": file_url,
                "editor_type": "figjam",
                "created_at": datetime.now().isoformat()
            }
        }

        with open(args.output, "w") as f:
            json.dump(output, f, indent=2)

        print(f"  ✅ Info saved to: {args.output}")
        print(json.dumps(output, indent=2))

    except requests.exceptions.HTTPError as e:
        print(f"ERROR: Failed to create FigJam file: {e}")
        if e.response.status_code == 403:
            print("  → Check that your FIGMA_TOKEN has file write permissions")
        sys.exit(1)


if __name__ == "__main__":
    main()
