# PRD to Technical Design Document (TDD) — Claude Code Skill

A complete, production-ready Claude Code skill that orchestrates a versioned pipeline from Product Requirements Document (PRD) → Technical Design Document (TDD) with architecture diagrams.

## What It Does

1. **Reads PRDs from Notion** — Extracts structured requirements with version metadata
2. **Analyzes GitHub repositories** — Identifies architecture patterns, integration points, constraints
3. **Generates versioned TDDs** — Complete technical design documents with PRD requirement mapping
4. **Creates architecture diagrams** — Excalidraw (FigJam-compatible) and Mermaid diagrams
5. **Maintains version registry** — Permanent 1:1 mapping between PRD versions and TDD versions

## Installation

### Option 1: Project-level (recommended for teams)
```bash
# Copy skill folder into your project
cp -r prd-to-tech-design ./.claude/skills/

# Set environment variables
export NOTION_TOKEN="your-notion-integration-token"
export GITHUB_TOKEN="your-github-pat"
export FIGMA_TOKEN="your-figma-token"  # Optional
```

### Option 2: Global (personal use)
```bash
mkdir -p ~/.claude/skills/
cp -r prd-to-tech-design ~/.claude/skills/
```

## Quick Start

Once installed, simply tell Claude:

> "Create a tech design for PRD-042 from Notion. The repo is github.com/org/backend. I want diagrams in FigJam."

Claude will:
1. Detect and load this skill automatically
2. Fetch the PRD from Notion
3. Analyze the GitHub repository
4. Generate a complete TDD with diagrams
5. Update the version registry

## Skill Structure

```
prd-to-tech-design/
├── SKILL.md                          # Main skill instructions (model-invoked)
├── scripts/
│   ├── notion-extract.py             # Notion API PRD extractor
│   ├── github-analyzer.py            # GitHub repo architecture analyzer
│   ├── diagram-generator.py          # Excalidraw/Mermaid diagram generator
│   └── registry-manager.py           # Version mapping registry
├── templates/
│   └── tdd-template.md               # TDD document template
└── reference/
    ├── notion-api-cheatsheet.md      # Notion API quick reference
    ├── figma-api-cheatsheet.md       # Figma API quick reference
    ├── excalidraw-format.md          # Excalidraw JSON schema
    └── versioning-semver.md          # Versioning rules and conventions
```

## Manual Script Usage

### Extract PRD from Notion
```bash
export NOTION_TOKEN="ntn_..."
python scripts/notion-extract.py --url "https://notion.so/..." --output prd-extract.json
```

### Analyze GitHub Repository
```bash
export GITHUB_TOKEN="ghp_..."
python scripts/github-analyzer.py --repo "org/backend" --branch main --output github-analysis.json
```

### Generate Diagrams
```bash
python scripts/diagram-generator.py --tdd ./TDD-042-v1.0.0.md --output-dir ./diagrams/
```

### Manage Version Registry
```bash
# Initialize registry
python scripts/registry-manager.py init --project "My Product"

# Add mapping
python scripts/registry-manager.py add   --prd-id PRD-042 --prd-version 2.1.0   --tdd-version 1.0.0 --tdd-file ./TDD-042-v1.0.0.md

# View lineage
python scripts/registry-manager.py tree --prd-id PRD-042

# Update status
python scripts/registry-manager.py status --mapping-id map-abc123 --status approved
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `NOTION_TOKEN` | Yes | Notion integration token |
| `NOTION_DATABASE_ID` | No | PRD database ID (if using database queries) |
| `GITHUB_TOKEN` | Recommended | GitHub PAT for private repos and higher rate limits |
| `FIGMA_TOKEN` | No | Figma PAT for auto-creating FigJam files |
| `REGISTRY_FILE` | No | Path to version registry (default: `./version-registry.json`) |

## Version Mapping

The skill maintains a `version-registry.json` file that tracks:

```json
{
  "project_name": "My Product",
  "last_updated": "2026-06-23T08:50:00Z",
  "mappings": [
    {
      "mapping_id": "map-abc123",
      "prd": {"id": "PRD-042", "version": "2.1.0", "notion_url": "..."},
      "tdd": {"version": "1.0.0", "status": "draft", "file_path": "..."},
      "parent_mapping": null,
      "changelog": "Initial mapping: PRD v2.1.0 → TDD v1.0.0"
    }
  ]
}
```

## Diagram Types Generated

| Diagram | Format | FigJam Import |
|---------|--------|---------------|
| System Architecture | `.excalidraw` | ✅ Drag & drop |
| Data Model / ERD | `.excalidraw` | ✅ Drag & drop |
| API Flow | `.mmd` (Mermaid) | ⚠️ Via Mermaid plugin or screenshot |
| State Machine | `.mmd` (Mermaid) | ⚠️ Via Mermaid plugin or screenshot |
| Implementation Timeline | `.excalidraw` | ✅ Drag & drop |

## Requirements

- Python 3.8+
- `requests` library (`pip install requests`)
- `git` CLI (for GitHub analysis)
- Claude Code (for skill loading)

## License

MIT
