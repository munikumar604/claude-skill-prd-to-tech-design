---
name: prd-to-tech-design
description: Use when the user needs to create, update, or review a Technical Design Document (TDD) based on a Product Requirements Document (PRD) from Notion. Triggers on phrases like "tech design", "technical design", "TDD", "design doc", "architecture doc", "create TDD from PRD", "analyze PRD", "Notion to design", "version mapping PRD TDD", or when the user mentions generating diagrams, FigJam, or architecture documentation from product requirements. Also triggers when the user mentions analyzing a GitHub repository for architecture decisions or creating implementation plans from specifications.
disable-model-invocation: false
allowed-tools: Read Edit Bash Web Search Grep View
---

# PRD to Technical Design Document (TDD) — Versioned Pipeline

## Overview

This skill orchestrates a complete pipeline that reads a Product Requirements Document (PRD) from Notion (with version tracking), analyzes the target GitHub repository for architecture context, generates a versioned Technical Design Document (TDD), and produces FigJam-compatible architecture diagrams. Every TDD is permanently mapped 1:1 to its parent PRD version.

## When to Use

- User asks to create a technical design from a PRD
- User mentions Notion PRD + GitHub repo analysis
- User needs architecture diagrams (system, data model, API flow, sequence)
- User explicitly mentions version mapping between PRD and TDD
- User wants FigJam diagrams generated from requirements
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
NOTION_TOKEN          # Notion integration token
NOTION_DATABASE_ID    # PRD database ID
GITHUB_TOKEN          # GitHub personal access token (classic or fine-grained)
FIGMA_TOKEN           # Figma personal access token (optional, for auto-upload)
```

**Required User Inputs** (prompt if missing):
1. Notion PRD URL or PRD ID
2. Target GitHub repository URL + branch/commit
3. Output directory for artifacts (default: `./tech-designs/`)
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
        "acceptance_criteria": ["..."],
        "linked_stories": ["US-001"]
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

### Phase 3: Generate Versioned Technical Design Document

**Objective**: Produce a complete TDD mapped 1:1 to the PRD version.

**TDD Naming Convention**:
```
TDD-[PRD_ID]-v[X.Y.Z] (PRD v[A.B.C])
Example: TDD-042-v1.0.0 (PRD v2.1.0)
```

**TDD Template** (use `templates/tdd-template.md`):

```markdown
# Technical Design Document: {Feature Name}

## Document Metadata
| Field | Value |
|-------|-------|
| **TDD ID** | TDD-{PRD_ID}-v{X.Y.Z} |
| **TDD Version** | {X.Y.Z} |
| **Parent PRD** | [{PRD_ID}]({notion_url}) v{A.B.C} |
| **Status** | Draft → In Review → Approved → Implemented |
| **Created** | {date} |
| **Last Updated** | {date} |
| **Author** | Claude / {user} |
| **Reviewers** | TBD |

## Version History
| TDD Version | PRD Version | Date | Author | Change Summary |
|-------------|-------------|------|--------|----------------|
| 1.0.0 | 2.1.0 | {date} | Claude | Initial design |

---

## 1. Executive Summary
{2-3 paragraphs summarizing what we're building and why}

## 2. PRD Requirements Mapping

| PRD Req ID | Requirement | Technical Approach | Status | Est. Effort |
|------------|-------------|-------------------|--------|-------------|
| REQ-001 | {description} | {approach} | Designed | 3d |

### 2.1 Out of Scope (from PRD)
{List explicitly excluded items}

## 3. System Architecture

### 3.1 High-Level Architecture
{Describe the system at 10,000ft}

### 3.2 Component Diagram
{Reference to generated diagram — see Phase 4}

### 3.3 Data Flow
{Describe how data moves through the system}

## 4. Data Model

### 4.1 Entity Relationship Diagram
{Reference to generated ERD}

### 4.2 New / Modified Entities
```
{Schema definitions in code blocks}
```

### 4.3 Migration Plan
{Step-by-step migration strategy}

## 5. API Design

### 5.1 REST Endpoints / GraphQL Schema
```
{Endpoint definitions with request/response examples}
```

### 5.2 Authentication & Authorization
{How access is controlled}

### 5.3 Rate Limiting & Validation
{Constraints and guards}

## 6. Implementation Plan

### 6.1 Phase Breakdown
| Phase | Deliverable | Owner | Duration | Dependencies |
|-------|-------------|-------|----------|--------------|
| 1 | DB migration + models | TBD | 2d | None |
| 2 | API implementation | TBD | 3d | Phase 1 |
| 3 | Frontend integration | TBD | 2d | Phase 2 |
| 4 | Testing & QA | TBD | 2d | Phase 3 |

### 6.2 Key Decisions & Trade-offs
| Decision | Options Considered | Chosen | Rationale |
|----------|-------------------|--------|-----------|
| Sync vs Async | Sync API, Async job | Async job | PRD requires large file support |

## 7. Testing Strategy

### 7.1 Unit Tests
{What to unit test}

### 7.2 Integration Tests
{API contract tests}

### 7.3 E2E Tests
{User journey tests}

### 7.4 Performance Tests
{Load testing approach}

## 8. Operational Considerations

### 8.1 Monitoring & Alerting
{Metrics, dashboards, alerts}

### 8.2 Rollback Plan
{How to revert if something goes wrong}

### 8.3 Security Considerations
{Threat model, mitigations}

## 9. Open Questions & Risks

| ID | Question / Risk | Impact | Mitigation | Owner |
|----|----------------|--------|------------|-------|
| R1 | Can we handle 10k concurrent exports? | High | Load test before launch | TBD |

## 10. Appendix

### 10.1 Glossary
### 10.2 References
### 10.3 GitHub Analysis Summary
{Embed key findings from Phase 2}
```

**Version Delta Generation** (if updating existing TDD):
When a PRD version change is detected, generate a `DELTA` section at the top:

```markdown
## Delta from TDD v{old} → v{new}
**Triggered by**: PRD v{old_prd} → v{new_prd} ({change_type})

### Added
- {new requirements and their technical approaches}

### Modified
- {changed requirements and updated approaches}

### Removed
- {dropped requirements}

### Architecture Changes
- {any structural changes to the design}
```

**Output Artifact**: `TDD-{PRD_ID}-v{X.Y.Z}.md`

---

### Phase 4: Generate Architecture Diagrams

**Objective**: Produce FigJam-compatible visual artifacts.

**Diagram Types to Generate**:

1. **System Architecture Diagram** — Components, services, external dependencies
2. **Data Model / ERD** — Entities, relationships, cardinalities
3. **API Flow / Sequence Diagram** — Request lifecycle, service interactions
4. **State Machine** — Feature states and transitions
5. **Implementation Timeline** — Gantt-style phase breakdown

**Generation Strategy**:

Since FigJam does not have a public API for programmatic creation, use this approach:

**Primary**: Generate diagrams in **Excalidraw** format (`.excalidraw` files) — these import directly into FigJam via copy-paste or file import. Excalidraw is natively supported by FigJam.

**Secondary**: Generate **Mermaid** diagrams for inline documentation. Mermaid renders in GitHub, Notion, and most markdown viewers.

**Tertiary**: Generate **SVG** exports for static embedding.

**Diagram Content Rules**:
- Use consistent color coding:
  - 🟦 Existing systems (blue)
  - 🟩 New components (green)
  - 🟨 External services (yellow)
  - 🟥 Data stores (red)
  - ⬜ User/client (white)
- Include version watermark: `TDD v{X.Y.Z} | PRD v{A.B.C}`
- Label all connections with protocol/method (HTTP, gRPC, WebSocket, etc.)

**Output Artifacts**:
- `diagrams/system-architecture.excalidraw`
- `diagrams/data-model.excalidraw`
- `diagrams/api-flow.mmd`
- `diagrams/state-machine.mmd`
- `diagrams/timeline.excalidraw`

**FigJam Upload** (if FIGMA_TOKEN provided):
1. Create new FigJam file via Figma API: `POST /v1/files`
2. Name it: `TDD-{PRD_ID}-v{X.Y.Z} (PRD v{A.B.C})`
3. Unfortunately, Figma REST API does not support adding shapes to FigJam files programmatically
4. **Workaround**: Provide user with:
   - Direct FigJam file URL (empty canvas)
   - Instructions to import `.excalidraw` files via drag-and-drop
   - Pre-generated diagram images (PNG/SVG) as fallback

---

### Phase 5: Version Registry Update

**Objective**: Maintain the permanent 1:1 mapping between PRD versions and TDD versions.

**Registry File**: `version-registry.json` (stored in output directory)

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
        "file_path": "./tech-designs/TDD-042-v1.0.0.md",
        "figjam_url": "https://figma.com/file/...",
        "diagrams_path": "./tech-designs/diagrams/"
      },
      "github_analysis": {
        "repo": "org/backend-service",
        "commit": "abc123",
        "analysis_file": "./tech-designs/github-analysis.json"
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
- Update the PRD page with a link to the generated TDD file
- Add a `Technical Design` relation property if the database supports it

---

### Phase 6: Final Output & Summary

**Present to User**:

```markdown
## ✅ Technical Design Complete

**Mapping**: PRD v{A.B.C} → TDD v{X.Y.Z}

### Generated Artifacts
| Artifact | Location |
|----------|----------|
| TDD Document | `{output_dir}/TDD-{PRD_ID}-v{X.Y.Z}.md` |
| PRD Extract | `{output_dir}/prd-extract.json` |
| GitHub Analysis | `{output_dir}/github-analysis.json` |
| System Architecture Diagram | `{output_dir}/diagrams/system-architecture.excalidraw` |
| Data Model Diagram | `{output_dir}/diagrams/data-model.excalidraw` |
| API Flow Diagram | `{output_dir}/diagrams/api-flow.mmd` |
| State Machine | `{output_dir}/diagrams/state-machine.mmd` |
| Implementation Timeline | `{output_dir}/diagrams/timeline.excalidraw` |
| Version Registry | `{output_dir}/version-registry.json` |

### FigJam
- **File URL**: {figjam_url or "Create manually and import .excalidraw files"}
- **Naming**: `TDD-{PRD_ID}-v{X.Y.Z} (PRD v{A.B.C})`

### Next Steps
1. [ ] Review TDD document for accuracy
2. [ ] Import `.excalidraw` files into FigJam
3. [ ] Share with engineering team for review
4. [ ] Update status to "In Review" in version registry
5. [ ] Once approved, update status to "Approved" and begin implementation

### Version History
{Show mapping lineage if this is an update}
```

---

## Helper Scripts

This skill bundles helper scripts in the `scripts/` directory:

### `scripts/notion-extract.py`
Extracts PRD data from Notion API and outputs structured JSON.

### `scripts/github-analyzer.py`
Analyzes a GitHub repository and produces architecture analysis JSON.

### `scripts/diagram-generator.py`
Generates Excalidraw and Mermaid diagram files from TDD content.

### `scripts/registry-manager.py`
Manages the version registry JSON file.

**To run a script**: Use the Bash tool to execute `python scripts/{script}.py` with appropriate arguments.

---

## Reference Files

- `reference/notion-api-cheatsheet.md` — Notion API endpoints and property types
- `reference/figma-api-cheatsheet.md` — Figma REST API endpoints
- `reference/excalidraw-format.md` — Excalidraw JSON schema for programmatic generation
- `reference/versioning-semver.md` — SemVer rules for PRD/TDD versioning

---

## Quality Checklist

Before marking a TDD as complete, verify:

- [ ] Every PRD requirement (P0, P1) has a corresponding technical approach
- [ ] GitHub analysis informed all architectural decisions
- [ ] All diagrams include version watermark
- [ ] Version registry has been updated
- [ ] Delta section exists if this is a version update
- [ ] Open questions are explicitly listed, not hidden
- [ ] Rollback plan is concrete, not generic
- [ ] Estimates include buffer for unknowns
- [ ] Security considerations are addressed
- [ ] Breaking changes are flagged prominently

---

## Error Handling

| Scenario | Action |
|----------|--------|
| Notion API returns 404 | Ask user to verify PRD URL and NOTION_TOKEN permissions |
| GitHub repo not accessible | Check GITHUB_TOKEN scope; ask user for access or use public repo |
| PRD has no version | Prompt user for version; default to 1.0.0 if they decline |
| Version already mapped | Show existing TDD; ask: update, branch, or skip |
| Figma token missing | Skip auto-upload; provide manual import instructions |
| Large repo (>1GB) | Use shallow clone (`--depth 1`); warn user analysis may be incomplete |
| PRD content is unstructured | Use heuristics to extract requirements; warn user and ask for manual review |

---

## Progressive Disclosure

The full skill body loads on activation. Reference files load only when:
- Notion API issues → load `reference/notion-api-cheatsheet.md`
- Figma upload issues → load `reference/figma-api-cheatsheet.md`
- Diagram generation issues → load `reference/excalidraw-format.md`
- Version conflicts → load `reference/versioning-semver.md`

---

## Example Invocation

**User**: "Create a tech design for PRD-042 from Notion. The repo is github.com/org/backend. I want diagrams in FigJam."

**Claude** (activates this skill):
1. "I'll create a Technical Design Document for PRD-042. Let me check for required environment variables..."
2. "Found NOTION_TOKEN and GITHUB_TOKEN. Fetching PRD from Notion..."
3. "PRD v2.1.0 detected. No existing mapping found. Proceeding with fresh TDD v1.0.0."
4. "Analyzing github.com/org/backend @ main..."
5. "Generating TDD, diagrams, and updating version registry..."
6. "Done! Here's your complete design package..."
