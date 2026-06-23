#!/usr/bin/env python3
"""
notion-tdd-creator.py — Create a TDD page in Notion database with rich content blocks

Usage:
    python notion-tdd-creator.py --database-id "abc123" --title "TDD-042-v1.0.0" --version "1.0.0" --prd-version "2.1.0" --prd-url "https://notion.so/..." --content-file ./TDD-content.md

Environment:
    NOTION_TOKEN (required)
    NOTION_TDD_DATABASE_ID (fallback if --database-id not provided)
"""

import os
import sys
import json
import argparse
import re
from datetime import datetime

try:
    import requests
except ImportError:
    print("ERROR: requests library required. Install: pip install requests")
    sys.exit(1)

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def create_page(database_id: str, properties: dict, token: str) -> dict:
    """Create a new page in a Notion database."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }
    payload = {
        "parent": {"database_id": database_id},
        "properties": properties
    }
    response = requests.post(f"{NOTION_API_BASE}/pages", headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


def add_blocks(page_id: str, blocks: list, token: str):
    """Append content blocks to a Notion page."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }
    # Notion API has a 100 block limit per request
    for i in range(0, len(blocks), 100):
        chunk = blocks[i:i+100]
        response = requests.patch(
            f"{NOTION_API_BASE}/blocks/{page_id}/children",
            headers=headers,
            json={"children": chunk}
        )
        response.raise_for_status()


def markdown_to_notion_blocks(markdown_text: str) -> list:
    """Convert markdown text to Notion block objects."""
    blocks = []
    lines = markdown_text.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            i += 1
            continue

        # Headings
        if stripped.startswith("# "):
            text = stripped[2:]
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": [{"type": "text", "text": {"content": text}}]}
            })
        elif stripped.startswith("## "):
            text = stripped[3:]
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": text}}]}
            })
        elif stripped.startswith("### "):
            text = stripped[4:]
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": [{"type": "text", "text": {"content": text}}]}
            })

        # Code blocks
        elif stripped.startswith("```"):
            language = stripped[3:].strip() or "plain text"
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            blocks.append({
                "object": "block",
                "type": "code",
                "code": {
                    "rich_text": [{"type": "text", "text": {"content": "\n".join(code_lines)}}],
                    "language": language
                }
            })

        # Tables (simple heuristic)
        elif "|" in stripped and i + 1 < len(lines) and "---" in lines[i+1]:
            # Parse table
            headers = [c.strip() for c in stripped.split("|") if c.strip()]
            i += 2  # Skip header and separator
            table_rows = []
            while i < len(lines) and "|" in lines[i]:
                cells = [c.strip() for c in lines[i].split("|") if c.strip()]
                if cells:
                    table_rows.append(cells)
                i += 1

            if headers and table_rows:
                table_block = {
                    "object": "block",
                    "type": "table",
                    "table": {
                        "table_width": len(headers),
                        "has_column_header": True,
                        "has_row_header": False,
                        "children": []
                    }
                }
                # Header row
                header_row = {
                    "object": "block",
                    "type": "table_row",
                    "table_row": {
                        "cells": [[{"type": "text", "text": {"content": h}}] for h in headers]
                    }
                }
                table_block["table"]["children"].append(header_row)
                # Data rows
                for row in table_rows:
                    table_block["table"]["children"].append({
                        "object": "block",
                        "type": "table_row",
                        "table_row": {
                            "cells": [[{"type": "text", "text": {"content": c}}] for c in row[:len(headers)]]
                        }
                    })
                blocks.append(table_block)
            continue  # Skip i += 1 at end since we already advanced

        # Bulleted list
        elif stripped.startswith("- ") or stripped.startswith("* "):
            text = stripped[2:]
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": text}}]}
            })

        # Numbered list
        elif re.match(r"^\d+\.\s", stripped):
            text = re.sub(r"^\d+\.\s", "", stripped)
            blocks.append({
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {"rich_text": [{"type": "text", "text": {"content": text}}]}
            })

        # Divider
        elif stripped == "---":
            blocks.append({
                "object": "block",
                "type": "divider",
                "divider": {}
            })

        # Quote / Callout
        elif stripped.startswith("> "):
            text = stripped[2:]
            blocks.append({
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"type": "text", "text": {"content": text}}],
                    "icon": {"emoji": "💡"}
                }
            })

        # Regular paragraph
        else:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": stripped}}]}
            })

        i += 1

    return blocks


def build_tdd_properties(title: str, version: str, prd_version: str, prd_url: str = "",
                         github_repo: str = "", figjam_url: str = "", status: str = "Draft") -> dict:
    """Build Notion page properties for TDD database entry."""
    properties = {
        "Name": {
            "title": [{"type": "text", "text": {"content": title}}]
        },
        "Version": {
            "rich_text": [{"type": "text", "text": {"content": version}}]
        },
        "PRD Version": {
            "rich_text": [{"type": "text", "text": {"content": prd_version}}]
        },
        "Status": {
            "select": {"name": status}
        }
    }

    if prd_url:
        properties["PRD URL"] = {"url": prd_url}
    if github_repo:
        properties["GitHub Repo"] = {"url": github_repo}
    if figjam_url:
        properties["FigJam"] = {"url": figjam_url}

    return properties


def main():
    parser = argparse.ArgumentParser(description="Create TDD page in Notion")
    parser.add_argument("--database-id", help="Notion TDD database ID")
    parser.add_argument("--title", required=True, help="TDD page title")
    parser.add_argument("--version", required=True, help="TDD version")
    parser.add_argument("--prd-version", required=True, help="Parent PRD version")
    parser.add_argument("--prd-url", default="", help="Parent PRD Notion URL")
    parser.add_argument("--github-repo", default="", help="GitHub repo URL")
    parser.add_argument("--figjam-url", default="", help="FigJam file URL")
    parser.add_argument("--content-file", required=True, help="Markdown file with TDD content")
    parser.add_argument("--status", default="Draft", help="Initial status")
    args = parser.parse_args()

    token = os.environ.get("NOTION_TOKEN")
    if not token:
        print("ERROR: NOTION_TOKEN environment variable not set")
        sys.exit(1)

    database_id = args.database_id or os.environ.get("NOTION_TDD_DATABASE_ID")
    if not database_id:
        print("ERROR: Provide --database-id or set NOTION_TDD_DATABASE_ID")
        sys.exit(1)

    # Read content file
    if not os.path.exists(args.content_file):
        print(f"ERROR: Content file not found: {args.content_file}")
        sys.exit(1)

    with open(args.content_file, "r") as f:
        content = f.read()

    print(f"Creating TDD page: {args.title}")
    print(f"  Database: {database_id}")
    print(f"  Version: {args.version} (PRD v{args.prd_version})")

    # Create page
    properties = build_tdd_properties(
        args.title, args.version, args.prd_version,
        args.prd_url, args.github_repo, args.figjam_url, args.status
    )

    try:
        page = create_page(database_id, properties, token)
        page_id = page["id"]
        page_url = page.get("url", f"https://notion.so/{page_id.replace('-', '')}")
        print(f"  ✅ Page created: {page_url}")
    except requests.exceptions.HTTPError as e:
        print(f"ERROR: Failed to create page: {e}")
        if e.response.status_code == 400:
            print("  → Check that your database has the required properties: Name, Version, PRD Version, Status")
        sys.exit(1)

    # Add content blocks
    blocks = markdown_to_notion_blocks(content)
    print(f"  Adding {len(blocks)} content blocks...")

    try:
        add_blocks(page_id, blocks, token)
        print(f"  ✅ Content added successfully")
    except requests.exceptions.HTTPError as e:
        print(f"WARNING: Some blocks may have failed: {e}")

    print(f"\n✅ TDD created in Notion: {page_url}")
    print(f"   Page ID: {page_id}")

    # Output JSON for downstream use
    output = {
        "tdd": {
            "title": args.title,
            "version": args.version,
            "prd_version": args.prd_version,
            "notion_url": page_url,
            "page_id": page_id,
            "status": args.status,
            "created_at": datetime.now().isoformat()
        }
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
