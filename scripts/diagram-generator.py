#!/usr/bin/env python3
"""
diagram-generator.py — Generate architecture diagrams in Excalidraw and Mermaid formats

Usage:
    python diagram-generator.py --tdd ./TDD-042-v1.0.0.md --output-dir ./diagrams/
    python diagram-generator.py --tdd ./TDD-042-v1.0.0.md --types system,data,api,state,timeline --output-dir ./diagrams/

Generates:
    - system-architecture.excalidraw
    - data-model.excalidraw
    - api-flow.mmd
    - state-machine.mmd
    - timeline.excalidraw
"""

import os
import sys
import json
import argparse
import re
from datetime import datetime


def generate_excalidraw_frame(elements: list, name: str, version_watermark: str = "") -> dict:
    base_elements = []
    if version_watermark:
        base_elements.append({
            "id": f"watermark-{name}", "type": "text",
            "x": 20, "y": 20, "width": 300, "height": 30, "angle": 0,
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
            "x": (x1 + x2) / 2 - 40, "y": (y1 + y2) / 2 - 20,
            "width": 80, "height": 20, "angle": 0,
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


def generate_system_architecture(tdd_content: str, version: str = "") -> dict:
    elements = []
    components = []
    lines = tdd_content.split("\n")
    in_architecture = False
    for line in lines:
        if "## 3." in line and "Architecture" in line:
            in_architecture = True
        elif line.startswith("## ") and in_architecture:
            break
        if in_architecture and line.strip().startswith("-"):
            comp = line.strip("- ").strip()
            if comp and len(comp) < 50:
                components.append(comp)
    if not components:
        components = ["Client", "API Gateway", "Application Service", "Database", "External Service"]
    colors = {
        "Client": ("#e8f5e9", "#2e7d32"), "API": ("#fff3e0", "#ef6c00"),
        "Service": ("#e3f2fd", "#1565c0"), "Database": ("#fce4ec", "#c62828"),
        "External": ("#fffde7", "#f9a825")
    }
    x, y, width, height, gap = 100, 150, 180, 80, 60
    for i, comp in enumerate(components[:6]):
        fill, stroke = colors.get("Service", ("#e3f2fd", "#1565c0"))
        for key, (f, s) in colors.items():
            if key.lower() in comp.lower():
                fill, stroke = f, s
                break
        rect = create_rectangle(f"comp-{i}", x, y, width, height, comp, fill, stroke)
        text = create_text(f"comp-{i}", x, y, width, height, comp)
        elements.extend([rect, text])
        if i < len(components) - 1 and i < 5:
            arrow_elements = create_arrow(f"arrow-{i}", x + width, y + height / 2, x + width + gap, y + height / 2, "HTTP")
            elements.extend(arrow_elements)
        x += width + gap + 40
    watermark = f"TDD {version}" if version else "Generated by prd-to-tech-design"
    return generate_excalidraw_frame(elements, "system-architecture", watermark)


def generate_data_model(tdd_content: str, version: str = "") -> dict:
    elements = []
    entities = []
    lines = tdd_content.split("\n")
    in_data_model = False
    for line in lines:
        if "## 4." in line and ("Data" in line or "Model" in line or "Entity" in line):
            in_data_model = True
        elif line.startswith("## ") and in_data_model and "## 4." not in line:
            break
        if in_data_model and line.strip().startswith("-"):
            entity = line.strip("- ").strip()
            if entity and len(entity) < 40:
                entities.append(entity)
    if not entities:
        entities = ["User", "Order", "Product", "Payment"]
    x, y, width, height, cols, gap_x, gap_y = 100, 150, 200, 120, 3, 80, 60
    for i, entity in enumerate(entities[:6]):
        col, row = i % cols, i // cols
        ex, ey = x + col * (width + gap_x), y + row * (height + gap_y)
        rect = create_rectangle(f"entity-{i}", ex, ey, width, height, entity, "#fce4ec", "#c62828")
        text = create_text(f"entity-{i}", ex, ey, width, height, entity)
        elements.extend([rect, text])
    watermark = f"TDD {version} | Data Model" if version else "Data Model"
    return generate_excalidraw_frame(elements, "data-model", watermark)


def generate_api_flow_mermaid(tdd_content: str) -> str:
    endpoints = []
    lines = tdd_content.split("\n")
    in_api = False
    for line in lines:
        if "## 5." in line and "API" in line:
            in_api = True
        elif line.startswith("## ") and in_api:
            break
        if in_api and any(method in line.upper() for method in ["GET", "POST", "PUT", "DELETE", "PATCH"]):
            endpoints.append(line.strip())
    if not endpoints:
        endpoints = ["GET /api/resource", "POST /api/resource", "PUT /api/resource/:id"]
    mermaid = """sequenceDiagram
    autonumber
    participant C as Client
    participant A as API Gateway
    participant S as Service
    participant D as Database
    participant Ext as External Service

"""
    for i, ep in enumerate(endpoints[:4]):
        method = ep.split()[0] if " " in ep else "GET"
        path = ep.split()[1] if " " in ep else ep
        mermaid += f"    C->>A: {method} {path}\n"
        mermaid += f"    A->>S: Forward request\n"
        mermaid += f"    S->>D: Query/Update\n"
        mermaid += f"    D-->>S: Result\n"
        mermaid += f"    S-->>A: Processed response\n"
        mermaid += f"    A-->>C: {method} Response\n\n"
    return mermaid


def generate_state_machine_mermaid(tdd_content: str) -> str:
    return """stateDiagram-v2
    [*] --> Draft: Create
    Draft --> InReview: Submit
    InReview --> Approved: Pass review
    InReview --> Draft: Request changes
    Approved --> InProgress: Start implementation
    InProgress --> Testing: Code complete
    Testing --> Deployed: Pass QA
    Testing --> InProgress: Bugs found
    Deployed --> [*]: Done
    Deployed --> InProgress: Hotfix required

    note right of Draft
        TDD Version tracked
        separately from PRD
    end note
"""


def generate_timeline_excalidraw(tdd_content: str, version: str = "") -> dict:
    elements = []
    phases = []
    lines = tdd_content.split("\n")
    in_impl = False
    for line in lines:
        if "## 6." in line and ("Implementation" in line or "Plan" in line):
            in_impl = True
        elif line.startswith("## ") and in_impl:
            break
        if in_impl and line.strip().startswith("|") and "Phase" not in line and "---" not in line:
            parts = [p.strip() for p in line.strip("|").split("|")]
            if len(parts) >= 2 and parts[0] and not parts[0].startswith("-"):
                phases.append(parts[0])
    if not phases:
        phases = ["Phase 1: Setup", "Phase 2: Core", "Phase 3: Integration", "Phase 4: Testing"]
    x, y, width, height, gap = 100, 200, 200, 60, 40
    elements.append({
        "id": "timeline-bar", "type": "line",
        "x": x, "y": y + height / 2,
        "width": len(phases) * (width + gap) - gap, "height": 0, "angle": 0,
        "strokeColor": "#1976d2", "backgroundColor": "transparent",
        "fillStyle": "solid", "strokeWidth": 4, "strokeStyle": "solid",
        "roughness": 0, "opacity": 100, "groupIds": [], "frameId": None,
        "roundness": None, "seed": 9999, "version": 1, "versionNonce": 9999,
        "isDeleted": False, "boundElements": None,
        "updated": datetime.now().isoformat(), "link": None, "locked": False,
        "startBinding": None, "endBinding": None, "lastCommittedPoint": None,
        "startArrowhead": None, "endArrowhead": "arrow",
        "points": [[0, 0], [len(phases) * (width + gap) - gap, 0]]
    })
    for i, phase in enumerate(phases[:5]):
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
    watermark = f"TDD {version} | Timeline" if version else "Implementation Timeline"
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
    parser = argparse.ArgumentParser(description="Generate architecture diagrams")
    parser.add_argument("--tdd", required=True, help="Path to TDD markdown file")
    parser.add_argument("--output-dir", "-o", default="./diagrams", help="Output directory")
    parser.add_argument("--types", nargs="+", choices=["system", "data", "api", "state", "timeline", "all"], default=["all"])
    args = parser.parse_args()

    if not os.path.exists(args.tdd):
        print(f"ERROR: TDD file not found: {args.tdd}")
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)
    metadata = parse_tdd_metadata(args.tdd)
    with open(args.tdd, "r") as f:
        tdd_content = f.read()

    version_watermark = f"TDD v{metadata['version']} | PRD v{metadata['prd_version']}"
    types_to_generate = ["system", "data", "api", "state", "timeline"] if "all" in args.types else args.types
    generated = []

    if "system" in types_to_generate:
        diagram = generate_system_architecture(tdd_content, version_watermark)
        path = os.path.join(args.output_dir, "system-architecture.excalidraw")
        with open(path, "w") as f:
            json.dump(diagram, f, indent=2)
        generated.append(path)
        print(f"  ✅ System Architecture: {path}")

    if "data" in types_to_generate:
        diagram = generate_data_model(tdd_content, version_watermark)
        path = os.path.join(args.output_dir, "data-model.excalidraw")
        with open(path, "w") as f:
            json.dump(diagram, f, indent=2)
        generated.append(path)
        print(f"  ✅ Data Model: {path}")

    if "api" in types_to_generate:
        mermaid = generate_api_flow_mermaid(tdd_content)
        path = os.path.join(args.output_dir, "api-flow.mmd")
        with open(path, "w") as f:
            f.write(mermaid)
        generated.append(path)
        print(f"  ✅ API Flow: {path}")

    if "state" in types_to_generate:
        mermaid = generate_state_machine_mermaid(tdd_content)
        path = os.path.join(args.output_dir, "state-machine.mmd")
        with open(path, "w") as f:
            f.write(mermaid)
        generated.append(path)
        print(f"  ✅ State Machine: {path}")

    if "timeline" in types_to_generate:
        diagram = generate_timeline_excalidraw(tdd_content, version_watermark)
        path = os.path.join(args.output_dir, "timeline.excalidraw")
        with open(path, "w") as f:
            json.dump(diagram, f, indent=2)
        generated.append(path)
        print(f"  ✅ Timeline: {path}")

    print(f"\n✅ Generated {len(generated)} diagrams in {args.output_dir}")
    print(f"\nTo import into FigJam:")
    print(f"  1. Open FigJam")
    print(f"  2. File → Import → Select .excalidraw files")
    print(f"  3. For Mermaid diagrams, use Mermaid Live Editor or Notion embed")


if __name__ == "__main__":
    main()
