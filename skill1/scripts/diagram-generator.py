#!/usr/bin/env python3
"""
diagram-generator.py — Generate context-aware architecture diagrams from GitHub repo + PRD

Usage:
    python diagram-generator.py --tdd ./TDD-042-v1.0.0.md --github-analysis ./github-analysis.json --prd ./prd-extract.json --output-dir ./diagrams/
    python diagram-generator.py --tdd ./TDD.md --github-analysis ./analysis.json --prd ./prd.json --types system,data,api,state,timeline --output-dir ./diagrams/

Generates:
    - system-architecture.excalidraw (based on actual repo structure + PRD scope)
    - data-model.excalidraw (based on actual schema files + PRD entities)
    - api-flow.mmd (based on actual API routes + PRD endpoints)
    - state-machine.mmd (based on PRD feature states)
    - timeline.excalidraw (based on PRD phases + repo complexity)
"""

import os
import sys
import json
import argparse
import re
from datetime import datetime
from pathlib import Path


def load_json(path: str) -> dict:
    """Load JSON file."""
    with open(path, "r") as f:
        return json.load(f)


def generate_excalidraw_frame(elements: list, name: str, version_watermark: str = "") -> dict:
    base_elements = []
    if version_watermark:
        base_elements.append({
            "id": f"watermark-{name}", "type": "text",
            "x": 20, "y": 20, "width": 400, "height": 30, "angle": 0,
            "strokeColor": "#999999", "backgroundColor": "transparent",
            "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid",
            "roughness": 0, "opacity": 50, "groupIds": [], "frameId": None,
            "roundness": None, "seed": 1, "version": 1, "versionNonce": 1,
            "isDeleted": False, "boundElements": None,
            "updated": datetime.now().isoformat(), "link": None, "locked": False,
            "text": version_watermark, "fontSize": 14, "fontFamily": 1,
            "textAlign": "left", "verticalAlign": "top", "baseline": 18,
            "containerId": None, "originalText": version_watermark, "lineHeight": 1.25
        })
    base_elements.extend(elements)
    return {
        "type": "excalidraw", "version": 2, "source": "prd-to-tech-design-skill",
        "elements": base_elements,
        "appState": {"gridSize": 20, "viewBackgroundColor": "#ffffff"},
        "files": {}
    }


def create_rectangle(id_prefix: str, x: float, y: float, width: float, height: float,
                     label: str, fill_color: str = "#e3f2fd", stroke_color: str = "#1976d2") -> dict:
    return {
        "id": f"{id_prefix}-rect", "type": "rectangle",
        "x": x, "y": y, "width": width, "height": height, "angle": 0,
        "strokeColor": stroke_color, "backgroundColor": fill_color,
        "fillStyle": "solid", "strokeWidth": 2, "strokeStyle": "solid",
        "roughness": 1, "opacity": 100, "groupIds": [f"{id_prefix}-group"],
        "frameId": None, "roundness": {"type": 3, "value": 8},
        "seed": hash(id_prefix) % 10000, "version": 1,
        "versionNonce": hash(id_prefix) % 10000, "isDeleted": False,
        "boundElements": [{"type": "text", "id": f"{id_prefix}-text"}],
        "updated": datetime.now().isoformat(), "link": None, "locked": False
    }


def create_text(id_prefix: str, x: float, y: float, width: float, height: float,
                text: str, font_size: int = 16) -> dict:
    return {
        "id": f"{id_prefix}-text", "type": "text",
        "x": x, "y": y + height / 2 - font_size / 2,
        "width": width, "height": font_size * 1.25, "angle": 0,
        "strokeColor": "#1a1a1a", "backgroundColor": "transparent",
        "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid",
        "roughness": 0, "opacity": 100, "groupIds": [f"{id_prefix}-group"],
        "frameId": None, "roundness": None,
        "seed": hash(id_prefix + "text") % 10000, "version": 1,
        "versionNonce": hash(id_prefix + "text") % 10000, "isDeleted": False,
        "boundElements": None, "updated": datetime.now().isoformat(),
        "link": None, "locked": False, "text": text, "fontSize": font_size,
        "fontFamily": 1, "textAlign": "center", "verticalAlign": "middle",
        "baseline": font_size * 0.8, "containerId": f"{id_prefix}-rect",
        "originalText": text, "lineHeight": 1.25
    }


def create_arrow(id_prefix: str, x1: float, y1: float, x2: float, y2: float, label: str = "") -> list:
    elements = [{
        "id": f"{id_prefix}-arrow", "type": "arrow",
        "x": x1, "y": y1, "width": x2 - x1, "height": y2 - y1, "angle": 0,
        "strokeColor": "#666666", "backgroundColor": "transparent",
        "fillStyle": "solid", "strokeWidth": 2, "strokeStyle": "solid",
        "roughness": 0, "opacity": 100, "groupIds": [], "frameId": None,
        "roundness": {"type": 2},
        "seed": hash(id_prefix + "arrow") % 10000, "version": 1,
        "versionNonce": hash(id_prefix + "arrow") % 10000, "isDeleted": False,
        "boundElements": None, "updated": datetime.now().isoformat(),
        "link": None, "locked": False, "startBinding": None, "endBinding": None,
        "lastCommittedPoint": None, "startArrowhead": None, "endArrowhead": "arrow",
        "points": [[0, 0], [x2 - x1, y2 - y1]]
    }]
    if label:
        elements.append({
            "id": f"{id_prefix}-label", "type": "text",
            "x": (x1 + x2) / 2 - 50, "y": (y1 + y2) / 2 - 25,
            "width": 100, "height": 20, "angle": 0,
            "strokeColor": "#666666", "backgroundColor": "transparent",
            "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid",
            "roughness": 0, "opacity": 100, "groupIds": [], "frameId": None,
            "roundness": None, "seed": hash(id_prefix + "label") % 10000,
            "version": 1, "versionNonce": hash(id_prefix + "label") % 10000,
            "isDeleted": False, "boundElements": None,
            "updated": datetime.now().isoformat(), "link": None, "locked": False,
            "text": label, "fontSize": 12, "fontFamily": 1,
            "textAlign": "center", "verticalAlign": "middle", "baseline": 15,
            "containerId": None, "originalText": label, "lineHeight": 1.25
        })
    return elements


def extract_components_from_github(github_analysis: dict, prd_data: dict) -> list:
    """Extract actual system components from GitHub analysis + PRD scope."""
    components = []

    # From GitHub: tech stack components
    stack = github_analysis.get("tech_stack", {})
    if stack.get("framework"):
        components.append({"name": stack["framework"], "type": "existing", "layer": "app"})
    if stack.get("database"):
        components.append({"name": stack["database"].split()[0], "type": "existing", "layer": "data"})
    if stack.get("queue"):
        components.append({"name": stack["queue"], "type": "existing", "layer": "infra"})

    # From GitHub: key directories as services
    dirs = github_analysis.get("directory_structure", {}).get("key_directories", [])
    for d in dirs[:4]:
        name = d.replace("src/", "").replace("app/", "").replace("/", " ").title()
        if name and name not in [c["name"] for c in components]:
            components.append({"name": name, "type": "existing", "layer": "service"})

    # From GitHub: integration points (new components needed)
    integration = github_analysis.get("integration_points", [])
    for ip in integration[:3]:
        keyword = ip.get("keyword", "").title()
        if keyword and keyword not in [c["name"] for c in components]:
            components.append({"name": f"{keyword} Service", "type": "new", "layer": "service"})

    # From PRD: requirements that imply new components
    reqs = prd_data.get("prd", {}).get("requirements", [])
    for req in reqs:
        desc = req.get("description", "").lower()
        if "export" in desc and "Export" not in [c["name"] for c in components]:
            components.append({"name": "Export Service", "type": "new", "layer": "service"})
        if "notification" in desc and "Notification" not in [c["name"] for c in components]:
            components.append({"name": "Notification Service", "type": "new", "layer": "service"})
        if "auth" in desc and "Auth" not in [c["name"] for c in components]:
            components.append({"name": "Auth Service", "type": "existing", "layer": "service"})

    # Ensure we have at minimum: Client, API, Service, DB
    defaults = [
        {"name": "Client", "type": "existing", "layer": "client"},
        {"name": "API Gateway", "type": "existing", "layer": "api"},
    ]
    for d in defaults:
        if d["name"] not in [c["name"] for c in components]:
            components.insert(0, d)

    if not any(c["layer"] == "data" for c in components):
        components.append({"name": "Database", "type": "existing", "layer": "data"})

    return components


def extract_entities_from_github(github_analysis: dict, prd_data: dict) -> list:
    """Extract data entities from GitHub schema + PRD requirements."""
    entities = []

    # From PRD: requirements mentioning entities
    reqs = prd_data.get("prd", {}).get("requirements", [])
    for req in reqs:
        desc = req.get("description", "").lower()
        title = req.get("title", "").lower()
        combined = desc + " " + title

        entity_keywords = ["user", "order", "product", "payment", "export", "report", 
                          "notification", "session", "account", "profile", "file"]
        for kw in entity_keywords:
            if kw in combined:
                entity_name = kw.title()
                if entity_name not in [e["name"] for e in entities]:
                    entities.append({"name": entity_name, "type": "new" if "export" in combined or "create" in combined else "existing"})

    # From GitHub: integration points that suggest entities
    integration = github_analysis.get("integration_points", [])
    for ip in integration:
        keyword = ip.get("keyword", "").lower()
        if keyword in ["user", "auth"] and "User" not in [e["name"] for e in entities]:
            entities.append({"name": "User", "type": "existing"})
        if keyword == "export" and "Export" not in [e["name"] for e in entities]:
            entities.append({"name": "Export", "type": "new"})

    if not entities:
        entities = [
            {"name": "User", "type": "existing"},
            {"name": "Request", "type": "new"},
            {"name": "Response", "type": "new"}
        ]

    return entities


def extract_api_endpoints(github_analysis: dict, prd_data: dict) -> list:
    """Extract API endpoints from GitHub routes + PRD requirements."""
    endpoints = []

    # From GitHub: API routes found
    integration = github_analysis.get("integration_points", [])
    for ip in integration:
        if ip.get("type") == "api_directory":
            routes = ip.get("routes", [])
            for r in routes[:5]:
                if "." in r:
                    route_name = r.split(".")[0]
                    if route_name not in [e["path"] for e in endpoints]:
                        endpoints.append({"method": "GET", "path": f"/api/{route_name}", "source": "github"})

    # From PRD: requirements implying endpoints
    reqs = prd_data.get("prd", {}).get("requirements", [])
    for req in reqs:
        desc = req.get("description", "").lower()
        req_id = req.get("id", "")

        if "export" in desc:
            endpoints.append({"method": "POST", "path": "/api/export", "source": "prd", "req_id": req_id})
            endpoints.append({"method": "GET", "path": "/api/export/:id", "source": "prd", "req_id": req_id})
        if "download" in desc:
            endpoints.append({"method": "GET", "path": "/api/download/:id", "source": "prd", "req_id": req_id})
        if "create" in desc or "add" in desc:
            endpoints.append({"method": "POST", "path": "/api/resource", "source": "prd", "req_id": req_id})
        if "list" in desc or "get all" in desc:
            endpoints.append({"method": "GET", "path": "/api/resources", "source": "prd", "req_id": req_id})

    if not endpoints:
        endpoints = [
            {"method": "GET", "path": "/api/health", "source": "default"},
            {"method": "POST", "path": "/api/resource", "source": "default"},
            {"method": "GET", "path": "/api/resource/:id", "source": "default"}
        ]

    return endpoints


def extract_states_from_prd(prd_data: dict) -> list:
    """Extract state machine states from PRD requirements."""
    states = ["Draft", "Pending", "InProgress", "Completed", "Failed"]

    reqs = prd_data.get("prd", {}).get("requirements", [])
    for req in reqs:
        desc = req.get("description", "").lower()
        if "status" in desc or "state" in desc:
            words = desc.split()
            for i, word in enumerate(words):
                if word.lower() in ["to", "->", "→"] and i > 0 and i < len(words) - 1:
                    prev = words[i-1].strip(",.()[]{}").title()
                    next_w = words[i+1].strip(",.()[]{}").title()
                    if prev and prev not in states:
                        states.append(prev)
                    if next_w and next_w not in states:
                        states.append(next_w)

    return list(dict.fromkeys(states))


def extract_phases_from_prd(prd_data: dict, github_analysis: dict) -> list:
    """Extract implementation phases from PRD + GitHub complexity."""
    phases = []
    reqs = prd_data.get("prd", {}).get("requirements", [])

    phases.append("Phase 1: Setup & Scaffolding")

    has_db_changes = any("database" in r.get("description", "").lower() or 
                         "schema" in r.get("description", "").lower() for r in reqs)
    if has_db_changes:
        phases.append("Phase 2: Data Model & Migration")

    phases.append("Phase 3: Core Service Implementation")

    has_api = any("api" in r.get("description", "").lower() or 
                  "endpoint" in r.get("description", "").lower() for r in reqs)
    if has_api:
        phases.append("Phase 4: API Layer")

    has_frontend = any("ui" in r.get("description", "").lower() or 
                       "frontend" in r.get("description", "").lower() or
                       "page" in r.get("description", "").lower() for r in reqs)
    if has_frontend:
        phases.append("Phase 5: Frontend Integration")

    phases.append("Phase 6: Testing & QA")
    phases.append("Phase 7: Deployment")

    return phases


def generate_system_architecture(components: list, version: str = "") -> dict:
    """Generate system architecture diagram from actual components."""
    elements = []

    colors = {
        "client": ("#e8f5e9", "#2e7d32"),
        "api": ("#fff3e0", "#ef6c00"),
        "service": ("#e3f2fd", "#1565c0"),
        "data": ("#fce4ec", "#c62828"),
        "infra": ("#f3e5f5", "#7b1fa2"),
        "new": ("#e8f5e9", "#2e7d32"),
        "existing": ("#e3f2fd", "#1565c0")
    }

    layer_y = {"client": 50, "api": 180, "service": 310, "data": 440, "infra": 440}
    layer_x = {"client": 100, "api": 100, "service": 100, "data": 100, "infra": 500}
    x_offsets = {"client": 0, "api": 0, "service": 0, "data": 0, "infra": 0}
    width, height, gap = 180, 80, 60

    for i, comp in enumerate(components):
        layer = comp.get("layer", "service")
        comp_type = comp.get("type", "existing")
        name = comp["name"]

        if comp_type == "new":
            fill, stroke = colors["new"]
        else:
            fill, stroke = colors.get(layer, colors["existing"])

        x = layer_x.get(layer, 100) + x_offsets.get(layer, 0)
        y = layer_y.get(layer, 310)

        rect = create_rectangle(f"comp-{i}", x, y, width, height, name, fill, stroke)
        text = create_text(f"comp-{i}", x, y, width, height, name)
        elements.extend([rect, text])

        x_offsets[layer] = x_offsets.get(layer, 0) + width + gap

    # Add arrows between layers
    elements.extend(create_arrow("flow-client-api", 190, 130, 190, 180, "HTTP"))
    elements.extend(create_arrow("flow-api-svc", 190, 260, 190, 310, "Internal"))
    elements.extend(create_arrow("flow-svc-db", 190, 390, 190, 440, "SQL/NoSQL"))

    watermark = f"TDD {version} | Generated from Repo Analysis" if version else "Generated from Repo Analysis"
    return generate_excalidraw_frame(elements, "system-architecture", watermark)


def generate_data_model(entities: list, version: str = "") -> dict:
    """Generate data model / ERD diagram from actual entities."""
    elements = []
    colors = {"existing": ("#e3f2fd", "#1565c0"), "new": ("#e8f5e9", "#2e7d32")}

    x, y, width, height, cols = 100, 150, 200, 120, 3
    gap_x, gap_y = 80, 60

    for i, entity in enumerate(entities[:8]):
        col = i % cols
        row = i // cols
        ex = x + col * (width + gap_x)
        ey = y + row * (height + gap_y)
        fill, stroke = colors.get(entity.get("type", "existing"), colors["existing"])

        rect = create_rectangle(f"entity-{i}", ex, ey, width, height, entity["name"], fill, stroke)
        text = create_text(f"entity-{i}", ex, ey, width, height, entity["name"])
        elements.extend([rect, text])

        if i > 0 and col > 0:
            prev_ex = x + (col - 1) * (width + gap_x)
            arrow_elements = create_arrow(f"rel-{i}", prev_ex + width, ey + height / 2, ex, ey + height / 2, "1:N")
            elements.extend(arrow_elements)

    watermark = f"TDD {version} | Data Model from PRD + Schema" if version else "Data Model from PRD + Schema"
    return generate_excalidraw_frame(elements, "data-model", watermark)


def generate_api_flow_mermaid(endpoints: list, version: str = "") -> str:
    """Generate Mermaid sequence diagram from actual endpoints."""
    mermaid = f"""sequenceDiagram
    autonumber
    participant C as Client
    participant A as API Gateway
    participant S as Service
    participant D as Database
    participant Ext as External Service

    Note over C,Ext: TDD {version} — API Flow from PRD + Repo Analysis

"""

    for i, ep in enumerate(endpoints[:6]):
        method = ep.get("method", "GET")
        path = ep.get("path", "/api/resource")
        req_id = ep.get("req_id", "")
        note = f" ({req_id})" if req_id else ""

        mermaid += f"    C->>A: {method} {path}{note}\n"
        mermaid += f"    A->>S: Forward request\n"
        mermaid += f"    S->>D: Query/Update\n"
        mermaid += f"    D-->>S: Result\n"
        mermaid += f"    S-->>A: Processed response\n"
        mermaid += f"    A-->>C: {method} Response\n\n"

    return mermaid


def generate_state_machine_mermaid(states: list, version: str = "") -> str:
    """Generate Mermaid state diagram from PRD states."""
    mermaid = f"""stateDiagram-v2
    [*] --> {states[0]}: Initialize

"""
    for i in range(len(states) - 1):
        mermaid += f"    {states[i]} --> {states[i+1]}: Process\n"

    for state in states[1:-1]:
        mermaid += f"    {state} --> Failed: Error\n"

    mermaid += f"    Failed --> {states[0]}: Retry\n"
    mermaid += f"    {states[-1]} --> [*]: Complete\n"

    mermaid += f"""
    note right of {states[0]}
        TDD {version}
        States derived from PRD requirements
    end note
"""
    return mermaid


def generate_timeline_excalidraw(phases: list, version: str = "") -> dict:
    """Generate implementation timeline from actual phases."""
    elements = []
    x, y, width, height, gap = 100, 200, 200, 60, 40
    total_width = len(phases) * (width + gap) - gap

    elements.append({
        "id": "timeline-bar", "type": "line",
        "x": x, "y": y + height / 2,
        "width": total_width, "height": 0, "angle": 0,
        "strokeColor": "#1976d2", "backgroundColor": "transparent",
        "fillStyle": "solid", "strokeWidth": 4, "strokeStyle": "solid",
        "roughness": 0, "opacity": 100, "groupIds": [], "frameId": None,
        "roundness": None, "seed": 9999, "version": 1, "versionNonce": 9999,
        "isDeleted": False, "boundElements": None,
        "updated": datetime.now().isoformat(), "link": None, "locked": False,
        "startBinding": None, "endBinding": None, "lastCommittedPoint": None,
        "startArrowhead": None, "endArrowhead": "arrow",
        "points": [[0, 0], [total_width, 0]]
    })

    for i, phase in enumerate(phases[:6]):
        px = x + i * (width + gap)
        rect = create_rectangle(f"phase-{i}", px, y - 30, width, height, phase, "#e8f5e9", "#2e7d32")
        text = create_text(f"phase-{i}", px, y - 30, width, height, phase, 14)
        dot = {
            "id": f"dot-{i}", "type": "ellipse",
            "x": px + width / 2 - 8, "y": y + height / 2 - 8,
            "width": 16, "height": 16, "angle": 0,
            "strokeColor": "#1976d2", "backgroundColor": "#1976d2",
            "fillStyle": "solid", "strokeWidth": 2, "strokeStyle": "solid",
            "roughness": 0, "opacity": 100, "groupIds": [], "frameId": None,
            "roundness": {"type": 2},
            "seed": hash(phase) % 10000, "version": 1,
            "versionNonce": hash(phase) % 10000, "isDeleted": False,
            "boundElements": None, "updated": datetime.now().isoformat(),
            "link": None, "locked": False
        }
        elements.extend([rect, text, dot])

    watermark = f"TDD {version} | Timeline from PRD + Repo" if version else "Implementation Timeline from PRD + Repo"
    return generate_excalidraw_frame(elements, "timeline", watermark)


def parse_tdd_metadata(tdd_path: str) -> dict:
    with open(tdd_path, "r") as f:
        content = f.read()
    metadata = {"version": "", "prd_version": "", "title": ""}
    version_match = re.search(r"\*\*TDD Version\*\*\s*\|\s*([\d.]+)", content)
    if version_match:
        metadata["version"] = version_match.group(1)
    prd_version_match = re.search(r"Parent PRD.*?v([\d.]+)", content)
    if prd_version_match:
        metadata["prd_version"] = prd_version_match.group(1)
    title_match = re.search(r"# Technical Design Document: (.+)", content)
    if title_match:
        metadata["title"] = title_match.group(1)
    return metadata


def main():
    parser = argparse.ArgumentParser(description="Generate context-aware architecture diagrams")
    parser.add_argument("--tdd", required=True, help="Path to TDD markdown file")
    parser.add_argument("--github-analysis", required=True, help="Path to github-analysis.json")
    parser.add_argument("--prd", required=True, help="Path to prd-extract.json")
    parser.add_argument("--output-dir", "-o", default="./diagrams", help="Output directory")
    parser.add_argument("--types", nargs="+", choices=["system", "data", "api", "state", "timeline", "all"], default=["all"])
    args = parser.parse_args()

    for required in [args.tdd, args.github_analysis, args.prd]:
        if not os.path.exists(required):
            print(f"ERROR: File not found: {required}")
            sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)

    github_analysis = load_json(args.github_analysis)
    prd_data = load_json(args.prd)
    metadata = parse_tdd_metadata(args.tdd)

    version_watermark = f"TDD v{metadata['version']} | PRD v{metadata['prd_version']}"
    types_to_generate = ["system", "data", "api", "state", "timeline"] if "all" in args.types else args.types

    print(f"Generating diagrams for: {metadata['title']}")
    print(f"  PRD version: {metadata['prd_version']}")
    print(f"  TDD version: {metadata['version']}")
    print(f"  Repo: {github_analysis.get('repository', {}).get('url', 'N/A')}")
    print()

    generated = []

    if "system" in types_to_generate:
        components = extract_components_from_github(github_analysis, prd_data)
        print(f"  System components found: {len(components)}")
        for c in components:
            print(f"    - {c['name']} ({c['type']}, {c['layer']})")
        diagram = generate_system_architecture(components, version_watermark)
        path = os.path.join(args.output_dir, "system-architecture.excalidraw")
        with open(path, "w") as f:
            json.dump(diagram, f, indent=2)
        generated.append(path)
        print(f"  ✅ System Architecture: {path}\n")

    if "data" in types_to_generate:
        entities = extract_entities_from_github(github_analysis, prd_data)
        print(f"  Data entities found: {len(entities)}")
        for e in entities:
            print(f"    - {e['name']} ({e['type']})")
        diagram = generate_data_model(entities, version_watermark)
        path = os.path.join(args.output_dir, "data-model.excalidraw")
        with open(path, "w") as f:
            json.dump(diagram, f, indent=2)
        generated.append(path)
        print(f"  ✅ Data Model: {path}\n")

    if "api" in types_to_generate:
        endpoints = extract_api_endpoints(github_analysis, prd_data)
        print(f"  API endpoints found: {len(endpoints)}")
        for e in endpoints:
            print(f"    - {e['method']} {e['path']} (from {e['source']})")
        mermaid = generate_api_flow_mermaid(endpoints, version_watermark)
        path = os.path.join(args.output_dir, "api-flow.mmd")
        with open(path, "w") as f:
            f.write(mermaid)
        generated.append(path)
        print(f"  ✅ API Flow: {path}\n")

    if "state" in types_to_generate:
        states = extract_states_from_prd(prd_data)
        print(f"  States found: {len(states)}")
        for s in states:
            print(f"    - {s}")
        mermaid = generate_state_machine_mermaid(states, version_watermark)
        path = os.path.join(args.output_dir, "state-machine.mmd")
        with open(path, "w") as f:
            f.write(mermaid)
        generated.append(path)
        print(f"  ✅ State Machine: {path}\n")

    if "timeline" in types_to_generate:
        phases = extract_phases_from_prd(prd_data, github_analysis)
        print(f"  Implementation phases: {len(phases)}")
        for p in phases:
            print(f"    - {p}")
        diagram = generate_timeline_excalidraw(phases, version_watermark)
        path = os.path.join(args.output_dir, "timeline.excalidraw")
        with open(path, "w") as f:
            json.dump(diagram, f, indent=2)
        generated.append(path)
        print(f"  ✅ Timeline: {path}\n")

    print(f"✅ Generated {len(generated)} diagrams in {args.output_dir}")
    print(f"\nTo import into FigJam:")
    print(f"  1. Open the FigJam file created by figjam-creator.py")
    print(f"  2. File → Import → Select .excalidraw files")
    print(f"  3. For Mermaid diagrams, use Mermaid Live Editor or Notion embed")


if __name__ == "__main__":
    main()
