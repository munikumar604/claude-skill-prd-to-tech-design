---
name: prd-to-tech-design
description: Use when the user needs to create, update, or review a Technical Design Document (TDD) based on a Product Requirements Document (PRD) from Notion. Triggers on phrases like "tech design", "technical design", "TDD", "design doc", "architecture doc", "create TDD from PRD", "analyze PRD", "Notion to design", "version mapping PRD TDD", or when the user mentions generating diagrams, Figjam, or architecture documentation from product requirements. Also triggers when the user mentions analyzing a GitHub repository for architecture decisions or creating implementation plans from specifications.
disable-model-invocation: false
allowed-tools: Read Edit Bash Web Search Grep View
---

# PRD to Technical Design Document (TDD) — Versioned Pipeline

## Overview

This skill orchestrates a complete pipeline that:
1. **Reads a Product Requirements Document (PRD)** from Notion (with version tracking)
2. **Analyzes the target GitHub repository** for architecture context
3. **Generates a versioned Technical Design Document (TDD)** as a **Notion page** with rich content
4. **Creates architecture diagrams** in **FigJam** (via Excalidraw import + Figma API file creation)
5. **Maintains a permanent 1:1 version mapping** between PRD versions and TDD versions

## When to Use

- User asks to create a technical design from a PRD
- User mentions Notion PRD + GitHub repo analysis
- User needs architecture diagrams in FigJam
- User explicitly mentions version mapping between PRD and TDD
- User wants TDD stored in Notion (not just local markdown)
- User says "design doc", "tech spec", "architecture document", "implementation plan"

## When NOT to Use

- Pure code implementation without design phase
- Simple bug fixes or one-line changes
- Non-technical product discussions (pricing, marketing, go-to-market)
- Code review without PRD context

---

## Execution Pipeline

Follow these phases in strict order. Do not skip phases. Ask the user for missing required inputs before proceeding.

### Phase 0: Configuration & Setup

**Required Environment Variables** (check before proceeding):
```
NOTION_TOKEN          # Notion integration token (read + write)
NOTION_PRD_DATABASE_ID   # PRD source database ID
NOTION_TDD_DATABASE_ID   # TDD destination database ID (must exist in Notion)
GITHUB_TOKEN          # GitHub personal access token (classic or fine-grained)
FIGMA_TOKEN           # Figma personal access token (for creating FigJam files)
```

**Required User Inputs** (prompt if missing):
1. Notion PRD URL or PRD ID
2. Target GitHub repository URL + branch/commit
3. Whether to auto-create TDD in Notion (requires NOTION_TDD_DATABASE_ID)
4. Whether to auto-create FigJam file (requires FIGMA_TOKEN)

If any required input is missing, ask the user: "I need [X] to proceed. Please provide it or set the environment variable."

---

### Phase 1: Read & Parse Notion PRD

**Objective**: Extract the PRD with full version metadata.

**Steps**:
1. Use the Notion API to fetch the PRD page by ID/URL
2. Extract the `Version` property (or infer from page history if missing)
3. Parse the full content into structured sections:
   - Title, Status, Owner, Dates
   - Requirements list (with IDs, priorities, acceptance criteria)
   - User stories / use cases
   - Dependencies and blockers
   - Out of scope
   - Success metrics
4. Build version history from Notion page history or a `Version History` property
5. Detect if this is a NEW version vs. previously processed version

**Output Artifact**: `prd-extract.json`

```json
{
  "prd": {
    "id": "prd-uuid",
    "title": "Feature Name",
    "version": "2.1.0",
    "version_history": [
      {"version": "1.0.0", "date": "2026-06-01", "change_type": "initial"},
      {"version": "2.0.0", "date": "2026-06-15", "change_type": "major"},
      {"version": "2.1.0", "date": "2026-06-20", "change_type": "minor"}
    ],
    "status": "Ready for Tech Design",
    "requirements": [
      {
        "id": "REQ-001",
        "priority": "P0",
        "category": "Functional",
        "description": "...",
        "acceptance_criteria": ["..."]
      }
    ],
    "dependencies": ["PRD-038: Auth Service"],
    "notion_url": "https://notion.so/...",
    "raw_markdown": "..."
  }
}
```

**Version Detection Rules**:
- If `Version` property exists → use it
- If missing → check page history for last edit with version-like tags
- If still missing → prompt user: "I couldn't detect a PRD version. What version is this? (e.g., 1.0.0)"
- Compare against local registry (`version-registry.json`). If version already mapped, warn user and ask if they want to UPDATE the existing TDD or create a new mapping.

---

### Phase 2: Analyze GitHub Repository

**Objective**: Understand the existing codebase to inform architecture decisions.

**Steps**:
1. Clone or fetch the target repository (shallow clone if large)
2. Analyze directory structure and identify:
   - Tech stack (package.json, go.mod, requirements.txt, Cargo.toml, etc.)
   - Architecture pattern (MVC, microservices, clean architecture, etc.)
   - Existing modules/services related to the PRD domain
   - Database schema / ORM models
   - API routes / GraphQL schemas
   - Configuration and infrastructure files
3. Search for existing implementations of similar features
4. Identify integration points: where should the new feature hook in?
5. Assess constraints: coding standards, frameworks, deployment patterns

**Output Artifact**: `github-analysis.json`

```json
{
  "repository": {
    "url": "https://github.com/org/repo",
    "branch": "main",
    "commit": "abc123",
    "tech_stack": {
      "language": "TypeScript",
      "framework": "Next.js",
      "database": "PostgreSQL",
      "orm": "Prisma",
      "queue": "BullMQ",
      "deployment": "Vercel"
    },
    "architecture": {
      "pattern": "Layered / Clean Architecture",
      "key_directories": ["src/domain/", "src/infrastructure/", "src/application/"],
      "entry_points": ["src/app/api/", "src/app/page.tsx"]
    },
    "existing_patterns": [
      {
        "pattern": "Async job processing",
        "location": "src/jobs/",
        "relevance": "PRD requires export job — reuse BullMQ pattern"
      }
    ],
    "integration_points": [
      {
        "component": "Export Service",
        "hook_location": "src/services/export.ts",
        "pattern": "Add method to existing service class"
      }
    ],
    "constraints": [
      "Must use existing Prisma schema conventions",
      "API routes must follow RESTful pattern in src/app/api/",
      "All async jobs must use BullMQ with retry logic"
    ],
    "risk_assessment": {
      "breaking_changes": ["New DB migration required"],
      "performance_implications": ["Export could be CPU-intensive — consider worker scaling"],
      "security_concerns": ["Exported data must be encrypted at rest"]
    }
  }
}
```

**Analysis Commands** (run via Bash tool):
```bash
# Detect tech stack
find . -maxdepth 2 -name "package.json" -o -name "go.mod" -o -name "requirements.txt" -o -name "Cargo.toml" -o -name "pyproject.toml" | head -5

# Find existing similar features
grep -r "export" --include="*.ts" --include="*.js" -l | head -10
grep -r "download" --include="*.ts" --include="*.js" -l | head -10

# Schema analysis
find . -name "*.prisma" -o -name "schema.rb" -o -name "*.sql" | head -5

# API routes
find . -path "*/api/*" -name "*.ts" -o -path "*/routes/*" -name "*.ts" | head -20
```

---

### Phase 3: Generate Technical Design Document in Notion

**Objective**: Produce a complete TDD as a **Notion page** mapped 1:1 to the PRD version.

**TDD Naming Convention**:
```
TDD-[PRD_ID]-v[X.Y.Z] (PRD v[A.B.C])
Example: TDD-042-v1.0.0 (PRD v2.1.0)
```

**Notion TDD Database Requirements**:
The user must have a Notion database with these properties:
- `Name` (Title) — TDD title
- `Version` (Rich Text or Select) — TDD version
- `PRD Version` (Rich Text) — Parent PRD version
- `Status` (Select) — Draft / In Review / Approved / Implemented
- `PRD` (Relation) — Link to parent PRD page
- `GitHub Repo` (URL) — Repository URL
- `FigJam` (URL) — FigJam diagram link
- `Author` (People) — Document author
- `Created` (Date) — Creation date
- `Last Updated` (Date) — Last update date

**Steps**:
1. Use `scripts/notion-tdd-creator.py` to create a new page in the TDD database
2. Populate the page with rich content blocks:
   - Headings (H1, H2, H3)
   - Paragraphs
   - Tables (requirements mapping, decisions, risks)
   - Code blocks (API specs, schema definitions)
   - Bulleted/numbered lists
   - Callouts (for warnings, important notes)
   - Dividers
3. Add the `Version` property to the page
4. Link back to the parent PRD using a Relation property or inline link
5. Set initial `Status` to "Draft"

**TDD Content Structure in Notion**:

```
📄 TDD-042-v1.0.0 (PRD v2.1.0)
│
├── 📋 Document Metadata (Table block)
│   ├── TDD ID: TDD-042-v1.0.0
│   ├── TDD Version: 1.0.0
│   ├── Parent PRD: [PRD-042 v2.1.0] (linked)
│   ├── Status: Draft
│   ├── Created: 2026-06-23
│   └── Author: Claude
│
├── 📜 Version History (Table block)
│   ├── TDD v1.0.0 | PRD v2.1.0 | 2026-06-23 | Initial design
│
├── 📝 1. Executive Summary
├── 📝 2. PRD Requirements Mapping (Table)
│   ├── REQ-001 | Description | Technical Approach | Status | Effort
├── 🏗️ 3. System Architecture
│   ├── 3.1 High-Level Description
│   ├── 3.2 Component Diagram → [FigJam link]
│   └── 3.3 Data Flow
├── 🗄️ 4. Data Model
│   ├── 4.1 ERD → [FigJam link]
│   ├── 4.2 New/Modified Entities (Code block)
│   └── 4.3 Migration Plan
├── 🔌 5. API Design
│   ├── 5.1 REST/GraphQL Schema (Code block)
│   ├── 5.2 Auth & Authorization
│   └── 5.3 Rate Limiting
├── 📅 6. Implementation Plan (Table)
│   ├── Phase | Deliverable | Owner | Duration | Dependencies
├── 🧪 7. Testing Strategy
├── ⚙️ 8. Operational Considerations
│   ├── 8.1 Monitoring & Alerting
│   ├── 8.2 Rollback Plan
│   └── 8.3 Security Considerations
├── ❓ 9. Open Questions & Risks (Table)
│   ├── ID | Question/Risk | Impact | Mitigation | Owner
└── 📎 10. Appendix
    ├── 10.1 Glossary
    ├── 10.2 References
    └── 10.3 GitHub Analysis Summary
```

**Version Delta Section** (if updating existing TDD):
When a PRD version change is detected, prepend a Delta section at the top:

```
⚠️ Delta from TDD v{old} → v{new}
Triggered by: PRD v{old_prd} → v{new_prd} ({change_type})

Added:
• {new requirements and their technical approaches}

Modified:
• {changed requirements and updated approaches}

Removed:
• {dropped requirements}

Architecture Changes:
• {any structural changes to the design}
```

**Output Artifacts**:
- Notion TDD page URL
- Local backup: `TDD-{PRD_ID}-v{X.Y.Z}.md` (for git/version control)

---

### Phase 4: Create Design Diagrams in FigJam

**Objective**: Produce architecture diagrams as **FigJam files**.

**FigJam File Creation Strategy**:

Since FigJam's REST API cannot add shapes programmatically, use this hybrid approach:

**Step 1: Create FigJam file via Figma API**
```bash
curl -X POST https://api.figma.com/v1/files   -H "X-Figma-Token: $FIGMA_TOKEN"   -H "Content-Type: application/json"   -d '{"name": "TDD-042-v1.0.0 System Architecture", "editor_type": "figjam"}'
```
This returns a `file_key` and `file_url`.

**Step 2: Generate Excalidraw diagram files**
Use `scripts/diagram-generator.py` to create `.excalidraw` files with:
- Version watermark: `TDD v{X.Y.Z} | PRD v{A.B.C}`
- Consistent color coding:
  - 🟦 Existing systems (blue)
  - 🟩 New components (green)
  - 🟨 External services (yellow)
  - 🟥 Data stores (red)
  - ⬜ User/client (white)
- Labeled connections with protocol/method

**Step 3: Provide user with import instructions**
Since we cannot programmatically add shapes to FigJam, instruct the user:

```
📋 FigJam Setup Instructions:

1. Open the created FigJam file: {figjam_url}
2. File → Import → Select the generated .excalidraw files:
   • system-architecture.excalidraw
   • data-model.excalidraw
   • timeline.excalidraw
3. The diagrams will import with all shapes, text, colors, and arrows preserved.
4. Arrange the imported diagrams on the FigJam canvas as needed.
5. For Mermaid diagrams (api-flow.mmd, state-machine.mmd):
   • Use Mermaid Live Editor (mermaid.live) to render
   • Screenshot and paste into FigJam, OR
   • Use the Mermaid FigJam plugin (if available)
```

**Diagram Types to Generate**:

| Diagram | Format | FigJam Import | Content |
|---------|--------|---------------|---------|
| **System Architecture** | `.excalidraw` | ✅ Drag & drop | Components, services, data flow |
| **Data Model / ERD** | `.excalidraw` | ✅ Drag & drop | Entities, relationships, cardinalities |
| **API Flow** | `.mmd` (Mermaid) | ⚠️ Screenshot/plugin | Request lifecycle, service interactions |
| **State Machine** | `.mmd` (Mermaid) | ⚠️ Screenshot/plugin | Feature states and transitions |
| **Implementation Timeline** | `.excalidraw` | ✅ Drag & drop | Gantt-style phase breakdown |

**FigJam Naming Convention**:
```
📁 TDD-042: User Export Feature
  ├── 📝 TDD v1.0.0 (PRD v2.1.0) — System Architecture
  ├── 📝 TDD v1.0.0 (PRD v2.1.0) — Data Model
  ├── 📝 TDD v1.0.0 (PRD v2.1.0) — Implementation Timeline
  └── 📝 TDD v1.1.0 (PRD v2.2.0) — Delta Diagrams
```

**Output Artifacts**:
- FigJam file URL(s)
- `diagrams/system-architecture.excalidraw`
- `diagrams/data-model.excalidraw`
- `diagrams/api-flow.mmd`
- `diagrams/state-machine.mmd`
- `diagrams/timeline.excalidraw`

---

### Phase 5: Version Registry Update

**Objective**: Maintain the permanent 1:1 mapping between PRD versions and TDD versions.

**Registry File**: `version-registry.json` (stored locally, can be committed to repo)

```json
{
  "project_name": "{derived from repo or user input}",
  "last_updated": "2026-06-23T08:50:00Z",
  "mappings": [
    {
      "mapping_id": "map-{uuid}",
      "prd": {
        "id": "PRD-042",
        "version": "2.1.0",
        "notion_url": "https://notion.so/...",
        "title": "User Data Export Feature"
      },
      "tdd": {
        "version": "1.0.0",
        "status": "draft",
        "notion_url": "https://notion.so/...",
        "figjam_url": "https://figma.com/file/...",
        "local_backup": "./backups/TDD-042-v1.0.0.md"
      },
      "github_analysis": {
        "repo": "org/backend-service",
        "commit": "abc123"
      },
      "created_at": "2026-06-23T08:50:00Z",
      "updated_at": "2026-06-23T08:50:00Z",
      "parent_mapping": null,
      "changelog": "Initial mapping: PRD v2.1.0 → TDD v1.0.0"
    }
  ]
}
```

**Update Rules**:
- On NEW mapping: append to `mappings` array
- On UPDATE: find existing mapping by PRD ID, update `tdd.version`, set `parent_mapping` to previous mapping ID, append changelog
- Always update `last_updated` timestamp

**Notion Backlink** (optional, if NOTION_TOKEN has write access):
- Update the PRD page with a link to the generated TDD Notion page
- Add a `Technical Design` relation property if the database supports it

---

### Phase 6: Final Output & Summary

**Present to User**:

```markdown
## ✅ Technical Design Complete

**Mapping**: PRD v{A.B.C} → TDD v{X.Y.Z}

### Generated Artifacts
| Artifact | Location | Link |
|----------|----------|------|
| TDD Document | Notion | [Open in Notion]({notion_tdd_url}) |
| PRD Extract | Local | `./prd-extract.json` |
| GitHub Analysis | Local | `./github-analysis.json` |
| System Architecture Diagram | FigJam + Excalidraw | [FigJam]({figjam_url}) / [Download .excalidraw]({path}) |
| Data Model Diagram | FigJam + Excalidraw | [FigJam]({figjam_url}) / [Download .excalidraw]({path}) |
| API Flow Diagram | Mermaid | `./diagrams/api-flow.mmd` |
| State Machine | Mermaid | `./diagrams/state-machine.mmd` |
| Implementation Timeline | FigJam + Excalidraw | [FigJam]({figjam_url}) / [Download .excalidraw]({path}) |
| Version Registry | Local | `./version-registry.json` |
| TDD Backup | Local | `./backups/TDD-{PRD_ID}-v{X.Y.Z}.md` |

### FigJam Setup
- **FigJam File**: {figjam_url}
- **Naming**: `TDD-{PRD_ID}-v{X.Y.Z} (PRD v{A.B.C})`
- **Import Steps**:
  1. Open FigJam file
  2. File → Import → Select `.excalidraw` files from `./diagrams/`
  3. Arrange diagrams on canvas

### Next Steps
1. [ ] Review TDD in Notion for accuracy
2. [ ] Import `.excalidraw` files into FigJam
3. [ ] Share Notion TDD with engineering team for review
4. [ ] Update TDD `Status` to "In Review" in Notion
5. [ ] Once approved, update `Status` to "Approved" and begin implementation

### Version History
{Show mapping lineage if this is an update}
```

---

## Helper Scripts

This skill bundles helper scripts in the `scripts/` directory:

### `scripts/notion-extract.py`
Extracts PRD data from Notion API and outputs structured JSON.

### `scripts/notion-tdd-creator.py`
Creates a new TDD page in a Notion database with rich content blocks (headings, tables, code, callouts).

### `scripts/github-analyzer.py`
Analyzes a GitHub repository and produces architecture analysis JSON.

### `scripts/diagram-generator.py`
Generates Excalidraw and Mermaid diagram files from TDD content.

### `scripts/figjam-creator.py`
Creates FigJam files via Figma API and returns shareable URLs.

### `scripts/registry-manager.py`
Manages the version registry JSON file.

**To run a script**: Use the Bash tool to execute `python scripts/{script}.py` with appropriate arguments.

---

## Reference Files

- `reference/notion-api-cheatsheet.md` — Notion API endpoints and property types
- `reference/figma-api-cheatsheet.md` — Figma REST API endpoints for FigJam creation
- `reference/excalidraw-format.md` — Excalidraw JSON schema for programmatic generation
- `reference/versioning-semver.md` — SemVer rules for PRD/TDD versioning

---

## Quality Checklist

Before marking a TDD as complete, verify:

- [ ] Every PRD requirement (P0, P1) has a corresponding technical approach in Notion
- [ ] GitHub analysis informed all architectural decisions
- [ ] All diagrams include version watermark
- [ ] Version registry has been updated with Notion and FigJam URLs
- [ ] Delta section exists in Notion if this is a version update
- [ ] Open questions are explicitly listed in Notion, not hidden
- [ ] Rollback plan is concrete, not generic
- [ ] Estimates include buffer for unknowns
- [ ] Security considerations are addressed in Notion
- [ ] Breaking changes are flagged prominently in Notion
- [ ] Notion TDD page has correct `Version` property
- [ ] Notion TDD page is linked back to parent PRD
- [ ] FigJam file was created and URL stored in registry

---

## Error Handling

| Scenario | Action |
|----------|--------|
| Notion API returns 404 | Ask user to verify PRD URL and NOTION_TOKEN permissions |
| Notion TDD database missing | Ask user to create a database with required properties (Name, Version, Status, PRD, etc.) |
| GitHub repo not accessible | Check GITHUB_TOKEN scope; ask user for access or use public repo |
| PRD has no version | Prompt user for version; default to 1.0.0 if they decline |
| Version already mapped | Show existing TDD Notion URL; ask: update, branch, or skip |
| Figma token missing | Skip auto-creation; provide manual FigJam creation instructions |
| Large repo (>1GB) | Use shallow clone (`--depth 1`); warn user analysis may be incomplete |
| PRD content is unstructured | Use heuristics to extract requirements; warn user and ask for manual review |
| Notion block limit exceeded | Notion has a 100 block limit per request; paginate if needed |

---

## Progressive Disclosure

The full skill body loads on activation. Reference files load only when:
- Notion API issues → load `reference/notion-api-cheatsheet.md`
- Figma/FigJam issues → load `reference/figma-api-cheatsheet.md`
- Diagram generation issues → load `reference/excalidraw-format.md`
- Version conflicts → load `reference/versioning-semver.md`

---

## Example Invocation

**User**: "Create a tech design for PRD-042 from Notion. The repo is github.com/org/backend. Save the TDD in Notion and diagrams in FigJam."

**Claude** (activates this skill):
1. "I'll create a Technical Design Document for PRD-042. Let me check for required environment variables..."
2. "Found NOTION_TOKEN, NOTION_TDD_DATABASE_ID, GITHUB_TOKEN, and FIGMA_TOKEN. Fetching PRD from Notion..."
3. "PRD v2.1.0 detected. No existing mapping found. Proceeding with fresh TDD v1.0.0."
4. "Analyzing github.com/org/backend @ main..."
5. "Creating TDD page in Notion database..."
6. "Creating FigJam file and generating diagrams..."
7. "Updating version registry..."
8. "Done! Here's your complete design package..."
