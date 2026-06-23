#!/usr/bin/env python3
"""
registry-manager.py — Manage PRD ↔ TDD version mappings

Usage:
    python registry-manager.py init --project "My Project"
    python registry-manager.py add --prd-id PRD-042 --prd-version 2.1.0 --tdd-version 1.0.0 --tdd-file ./TDD-042-v1.0.0.md
    python registry-manager.py list
    python registry-manager.py tree --prd-id PRD-042
    python registry-manager.py status --mapping-id map-xxx --status approved

Environment:
    REGISTRY_FILE (default: ./version-registry.json)
"""

import os
import sys
import json
import uuid
import argparse
from datetime import datetime

DEFAULT_REGISTRY = os.environ.get("REGISTRY_FILE", "./version-registry.json")


def load_registry(path: str = DEFAULT_REGISTRY) -> dict:
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {"project_name": "", "last_updated": datetime.now().isoformat(), "mappings": []}


def save_registry(registry: dict, path: str = DEFAULT_REGISTRY):
    registry["last_updated"] = datetime.now().isoformat()
    with open(path, "w") as f:
        json.dump(registry, f, indent=2)


def find_mapping(registry: dict, prd_id: str = None, mapping_id: str = None) -> dict:
    for mapping in registry["mappings"]:
        if prd_id and mapping["prd"]["id"] == prd_id:
            return mapping
        if mapping_id and mapping["mapping_id"] == mapping_id:
            return mapping
    return None


def get_latest_mapping(registry: dict, prd_id: str) -> dict:
    mappings = [m for m in registry["mappings"] if m["prd"]["id"] == prd_id]
    if not mappings:
        return None
    mappings.sort(key=lambda x: x["created_at"], reverse=True)
    return mappings[0]


def init_registry(project_name: str, path: str = DEFAULT_REGISTRY):
    registry = {"project_name": project_name, "last_updated": datetime.now().isoformat(), "mappings": []}
    save_registry(registry, path)
    print(f"✅ Initialized registry: {path}")
    print(f"   Project: {project_name}")


def add_mapping(prd_id: str, prd_version: str, prd_url: str, prd_title: str,
                tdd_version: str, tdd_file: str, figjam_url: str = None,
                github_repo: str = None, github_commit: str = None,
                parent_mapping_id: str = None, changelog: str = None,
                path: str = DEFAULT_REGISTRY):
    registry = load_registry(path)
    existing = find_mapping(registry, prd_id=prd_id)
    if existing and existing["prd"]["version"] == prd_version:
        print(f"WARNING: PRD {prd_id} v{prd_version} already mapped to TDD v{existing['tdd']['version']}")
        print(f"  Existing: {existing['tdd']['file_path']}")
        print(f"  Use --force to override, or create a new TDD version instead.")
        return False

    mapping_id = f"map-{uuid.uuid4().hex[:8]}"
    mapping = {
        "mapping_id": mapping_id,
        "prd": {"id": prd_id, "version": prd_version, "notion_url": prd_url, "title": prd_title},
        "tdd": {
            "version": tdd_version, "status": "draft",
            "file_path": os.path.abspath(tdd_file) if tdd_file else None,
            "figjam_url": figjam_url,
            "diagrams_path": os.path.join(os.path.dirname(tdd_file), "diagrams") if tdd_file else None
        },
        "github_analysis": {"repo": github_repo, "commit": github_commit} if github_repo else None,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "parent_mapping": parent_mapping_id,
        "changelog": changelog or f"Initial mapping: PRD v{prd_version} → TDD v{tdd_version}"
    }
    registry["mappings"].append(mapping)
    save_registry(registry, path)
    print(f"✅ Added mapping: {mapping_id}")
    print(f"   PRD {prd_id} v{prd_version} → TDD v{tdd_version}")
    print(f"   Status: draft")
    if parent_mapping_id:
        print(f"   Parent: {parent_mapping_id}")
    return True


def list_mappings(prd_id: str = None, path: str = DEFAULT_REGISTRY):
    registry = load_registry(path)
    mappings = registry["mappings"]
    if prd_id:
        mappings = [m for m in mappings if m["prd"]["id"] == prd_id]
    if not mappings:
        print("No mappings found.")
        return
    print(f"\n{'Mapping ID':<15} {'PRD':<12} {'PRD Ver':<10} {'TDD Ver':<10} {'Status':<12} {'Date'}")
    print("-" * 80)
    for m in mappings:
        print(f"{m['mapping_id']:<15} {m['prd']['id']:<12} {m['prd']['version']:<10} "
              f"{m['tdd']['version']:<10} {m['tdd']['status']:<12} {m['created_at'][:10]}")
    print(f"\nTotal: {len(mappings)} mapping(s)")


def update_status(mapping_id: str, status: str, path: str = DEFAULT_REGISTRY):
    registry = load_registry(path)
    mapping = find_mapping(registry, mapping_id=mapping_id)
    if not mapping:
        print(f"ERROR: Mapping {mapping_id} not found")
        return False
    old_status = mapping["tdd"]["status"]
    mapping["tdd"]["status"] = status
    mapping["updated_at"] = datetime.now().isoformat()
    save_registry(registry, path)
    print(f"✅ Updated {mapping_id}: {old_status} → {status}")
    return True


def show_mapping_tree(prd_id: str, path: str = DEFAULT_REGISTRY):
    registry = load_registry(path)
    mappings = [m for m in registry["mappings"] if m["prd"]["id"] == prd_id]
    if not mappings:
        print(f"No mappings found for {prd_id}")
        return
    print(f"\n📋 Version Lineage for {prd_id}")
    print("=" * 50)
    for m in sorted(mappings, key=lambda x: x["created_at"]):
        parent = m.get("parent_mapping")
        parent_str = f" ← {parent}" if parent else " (root)"
        print(f"\n  PRD v{m['prd']['version']} → TDD v{m['tdd']['version']}{parent_str}")
        print(f"    Mapping: {m['mapping_id']}")
        print(f"    Status: {m['tdd']['status']}")
        print(f"    Created: {m['created_at'][:10]}")
        print(f"    Changelog: {m['changelog']}")


def main():
    parser = argparse.ArgumentParser(description="Manage PRD-TDD version registry")
    parser.add_argument("--registry", "-r", default=DEFAULT_REGISTRY, help="Registry file path")
    subparsers = parser.add_subparsers(dest="command", help="Command")

    init_parser = subparsers.add_parser("init", help="Initialize new registry")
    init_parser.add_argument("--project", required=True, help="Project name")

    add_parser = subparsers.add_parser("add", help="Add new mapping")
    add_parser.add_argument("--prd-id", required=True)
    add_parser.add_argument("--prd-version", required=True)
    add_parser.add_argument("--prd-url", default="")
    add_parser.add_argument("--prd-title", default="")
    add_parser.add_argument("--tdd-version", required=True)
    add_parser.add_argument("--tdd-file", required=True)
    add_parser.add_argument("--figjam-url", default=None)
    add_parser.add_argument("--github-repo", default=None)
    add_parser.add_argument("--github-commit", default=None)
    add_parser.add_argument("--parent-mapping", default=None)
    add_parser.add_argument("--changelog", default=None)

    list_parser = subparsers.add_parser("list", help="List mappings")
    list_parser.add_argument("--prd-id", help="Filter by PRD ID")

    status_parser = subparsers.add_parser("status", help="Update mapping status")
    status_parser.add_argument("--mapping-id", required=True)
    status_parser.add_argument("--status", required=True, choices=["draft", "in_review", "approved", "implemented", "deprecated"])

    tree_parser = subparsers.add_parser("tree", help="Show version lineage")
    tree_parser.add_argument("--prd-id", required=True)

    args = parser.parse_args()

    if args.command == "init":
        init_registry(args.project, args.registry)
    elif args.command == "add":
        add_mapping(args.prd_id, args.prd_version, args.prd_url, args.prd_title,
                    args.tdd_version, args.tdd_file, args.figjam_url,
                    args.github_repo, args.github_commit, args.parent_mapping, args.changelog, args.registry)
    elif args.command == "list":
        list_mappings(args.prd_id, args.registry)
    elif args.command == "status":
        update_status(args.mapping_id, args.status, args.registry)
    elif args.command == "tree":
        show_mapping_tree(args.prd_id, args.registry)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
