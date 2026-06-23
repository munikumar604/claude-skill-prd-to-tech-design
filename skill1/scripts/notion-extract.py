#!/usr/bin/env python3
"""
notion-extract.py — Extract PRD data from Notion API

Usage:
    python notion-extract.py --url "https://notion.so/..." --output ./prd-extract.json
    python notion-extract.py --id "abc123-def456" --output ./prd-extract.json

Environment:
    NOTION_TOKEN (required)
"""

import os
import sys
import json
import argparse
from datetime import datetime
from urllib.parse import urlparse, unquote

try:
    import requests
except ImportError:
    print("ERROR: requests library required. Install: pip install requests")
    sys.exit(1)

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def extract_page_id_from_url(url: str) -> str:
    """Extract Notion page ID from various URL formats."""
    parsed = urlparse(url)
    path = unquote(parsed.path)
    parts = [p for p in path.split("/") if p]
    if not parts:
        raise ValueError(f"Could not extract page ID from URL: {url}")
    page_id = parts[-1].split("?")[0]
    if len(page_id) == 32:
        page_id = f"{page_id[:8]}-{page_id[8:12]}-{page_id[12:16]}-{page_id[16:20]}-{page_id[20:]}"
    return page_id


def fetch_page(page_id: str, token: str) -> dict:
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }
    response = requests.get(f"{NOTION_API_BASE}/pages/{page_id}", headers=headers)
    response.raise_for_status()
    return response.json()


def fetch_page_content(page_id: str, token: str) -> list:
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }
    blocks = []
    next_cursor = None
    while True:
        url = f"{NOTION_API_BASE}/blocks/{page_id}/children"
        params = {"page_size": 100}
        if next_cursor:
            params["start_cursor"] = next_cursor
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        blocks.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        next_cursor = data.get("next_cursor")
    return blocks


def extract_version(properties: dict) -> str:
    version_props = ["Version", "PRD Version", "Doc Version", "version", "prd_version"]
    for prop_name in version_props:
        if prop_name in properties:
            prop = properties[prop_name]
            prop_type = prop.get("type", "")
            if prop_type == "rich_text":
                text_parts = prop.get("rich_text", [])
                if text_parts:
                    return text_parts[0].get("plain_text", "")
            elif prop_type == "title":
                text_parts = prop.get("title", [])
                if text_parts:
                    return text_parts[0].get("plain_text", "")
            elif prop_type == "select":
                return prop.get("select", {}).get("name", "")
            elif prop_type == "number":
                return str(prop.get("number", ""))
    return None


def extract_requirements(blocks: list) -> list:
    requirements = []
    current_req = None
    for block in blocks:
        block_type = block.get("type", "")
        if block_type in ["heading_1", "heading_2", "heading_3"]:
            heading = block.get(block_type, {}).get("rich_text", [])
            text = "".join([t.get("plain_text", "") for t in heading]).strip()
            if text.upper().startswith("REQ-") or "REQUIREMENT" in text.upper():
                if current_req:
                    requirements.append(current_req)
                req_id = text.split()[0] if text.upper().startswith("REQ-") else f"REQ-{len(requirements)+1:03d}"
                current_req = {
                    "id": req_id,
                    "title": text,
                    "description": "",
                    "priority": "P1",
                    "acceptance_criteria": [],
                    "category": "Functional"
                }
        elif block_type == "bulleted_list_item" and current_req:
            text = "".join([t.get("plain_text", "") for t in block.get("bulleted_list_item", {}).get("rich_text", [])])
            if "acceptance" in text.lower() or "criteria" in text.lower():
                current_req["acceptance_criteria"].append(text)
            else:
                current_req["description"] += text + "\n"
        elif block_type == "paragraph" and current_req:
            text = "".join([t.get("plain_text", "") for t in block.get("paragraph", {}).get("rich_text", [])])
            if text.strip():
                current_req["description"] += text + "\n"
    if current_req:
        requirements.append(current_req)
    return requirements


def blocks_to_markdown(blocks: list) -> str:
    md_lines = []
    for block in blocks:
        block_type = block.get("type", "")
        if block_type in ["heading_1", "heading_2", "heading_3"]:
            level = int(block_type.split("_")[1])
            heading = block.get(block_type, {}).get("rich_text", [])
            text = "".join([t.get("plain_text", "") for t in heading])
            md_lines.append(f"{'#' * level} {text}")
        elif block_type == "paragraph":
            text = "".join([t.get("plain_text", "") for t in block.get("paragraph", {}).get("rich_text", [])])
            md_lines.append(text)
        elif block_type == "bulleted_list_item":
            text = "".join([t.get("plain_text", "") for t in block.get("bulleted_list_item", {}).get("rich_text", [])])
            md_lines.append(f"- {text}")
        elif block_type == "numbered_list_item":
            text = "".join([t.get("plain_text", "") for t in block.get("numbered_list_item", {}).get("rich_text", [])])
            md_lines.append(f"1. {text}")
        elif block_type == "code":
            code = block.get("code", {})
            language = code.get("language", "")
            text = "".join([t.get("plain_text", "") for t in code.get("rich_text", [])])
            md_lines.append(f"\`\`\`{language}\n{text}\n\`\`\`")
        elif block_type == "quote":
            text = "".join([t.get("plain_text", "") for t in block.get("quote", {}).get("rich_text", [])])
            md_lines.append(f"> {text}")
        elif block_type == "divider":
            md_lines.append("---")
        md_lines.append("")
    return "\n".join(md_lines)


def main():
    parser = argparse.ArgumentParser(description="Extract PRD from Notion")
    parser.add_argument("--url", help="Notion PRD URL")
    parser.add_argument("--id", help="Notion page ID")
    parser.add_argument("--output", "-o", default="prd-extract.json", help="Output JSON file")
    args = parser.parse_args()

    token = os.environ.get("NOTION_TOKEN")
    if not token:
        print("ERROR: NOTION_TOKEN environment variable not set")
        sys.exit(1)

    if args.url:
        page_id = extract_page_id_from_url(args.url)
    elif args.id:
        page_id = args.id
    else:
        print("ERROR: Provide --url or --id")
        sys.exit(1)

    print(f"Fetching Notion page: {page_id}")

    try:
        page = fetch_page(page_id, token)
        blocks = fetch_page_content(page_id, token)
    except requests.exceptions.HTTPError as e:
        print(f"ERROR: Notion API error: {e}")
        if e.response.status_code == 404:
            print("  → Page not found. Check the URL/ID and token permissions.")
        elif e.response.status_code == 401:
            print("  → Unauthorized. Check NOTION_TOKEN.")
        sys.exit(1)

    properties = page.get("properties", {})
    title = "".join([t.get("plain_text", "") for t in properties.get("Name", properties.get("Title", {})).get("title", [])])

    version = extract_version(properties)
    if not version:
        version = "1.0.0"
        print(f"WARNING: No version property found. Defaulting to {version}")

    requirements = extract_requirements(blocks)

    output = {
        "prd": {
            "id": page_id,
            "title": title or "Untitled PRD",
            "version": version,
            "version_history": [{"version": version, "date": datetime.now().isoformat(), "change_type": "extracted"}],
            "status": properties.get("Status", {}).get("select", {}).get("name", "Unknown"),
            "url": args.url or f"https://notion.so/{page_id.replace('-', '')}",
            "properties": {k: str(v) for k, v in properties.items()},
            "requirements": requirements,
            "raw_markdown": blocks_to_markdown(blocks),
            "extracted_at": datetime.now().isoformat()
        }
    }

    with open(args.output, "w") as f:
        json.dump(output, f, indent=2)

    print(f"✅ Extracted PRD: {title} v{version}")
    print(f"   Requirements found: {len(requirements)}")
    print(f"   Output: {args.output}")


if __name__ == "__main__":
    main()
