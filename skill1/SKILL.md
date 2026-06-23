---
name: prd-to-tech-design
description: Use when the user needs to create a Technical Design Document (TDD) in Notion with an implementation timeline, and architecture design diagrams in FigJam, both with version tracking. Triggers on phrases like "tech design", "technical design", "TDD", "design doc", "architecture doc", "create TDD from PRD", "Notion TDD", "FigJam design", "implementation timeline", "version mapping PRD TDD", or when the user mentions generating diagrams, FigJam, or architecture documentation from product requirements.
disable-model-invocation: false
allowed-tools: Read Edit Bash Web Search Grep View
---

# PRD → FigJam Design + Notion TDD with Timeline (Versioned)

## Overview

This skill produces **two versioned deliverables** from a Product Requirements Document (PRD):

1. **🎨 Design FigJam** — Architecture diagrams created as actual FigJam files with version tracking
2. **📝 Notion TDD with Implementation Timeline** — Technical Design Document as a rich Notion page with a visual timeline, both versioned

Every output is permanently mapped: **PRD v{X.Y.Z} → TDD v{A.B.C} → FigJam v{A.B.C}**

---

## Two Key Outputs

### Output 1: Design FigJam

**What**: A FigJam file containing architecture diagrams specific to the GitHub repository and PRD scope.

**Diagrams included**:
- System Architecture (components from actual repo + new from PRD)
- Data Model / ERD (entities from PRD + existing schema)
- API Flow (endpoints from repo routes + PRD requirements)
- State Machine (states from PRD feature lifecycle)
- Implementation Timeline (phases from PRD + repo complexity)

**Versioning**: Each FigJam file is named `TDD-{PRD_ID}-v{X.Y.Z} (PRD v{A.B.C})` and includes a version watermark on every diagram.

**Creation process**:
1. Figma API creates the FigJam file
2. Excalidraw diagrams are generated from repo + PRD context
3. User imports `.excalidraw` files into FigJam (drag & drop)
4. Mermaid diagrams are rendered and pasted as images

### Output 2: Notion TDD with Implementation Timeline

**What**: A rich Notion page in the TDD database containing the full technical design with an embedded implementation timeline.

**Sections**:
- Document Metadata (version, PRD link, status)
- Version History (table of all versions)
- Executive Summary
- PRD Requirements Mapping (table)
- System Architecture → [FigJam link]
- Data Model → [FigJam link]
- API Design (code blocks for schemas)
- **Implementation Timeline** (visual table + phase breakdown)
- Testing Strategy
- Operational Considerations
- Open Questions & Risks

**Versioning**: The Notion page has a `Version` property. Updates create new TDD versions with a Delta section.

---

## Execution Pipeline

### Phase 0: Configuration

**Required Environment Variables**:
```
NOTION_TOKEN              # Notion integration token (read + write)
NOTION_PRD_DATABASE_ID    # PRD source database ID
NOTION_TDD_DATABASE_ID    # TDD destination database ID
GITHUB_TOKEN              # GitHub personal access token
FIGMA_TOKEN               # Figma personal access token
```

**Required User Inputs** (prompt if missing):
1. Notion PRD URL or PRD ID
2. Target GitHub repository URL + branch/commit
3. Notion TDD database ID (or confirm env var)

---

### Phase 1: Read PRD from Notion

Extract PRD with version metadata.

**Script**: `scripts/notion-extract.py`
```bash
python scripts/notion-extract.py --url "https://notion.so/..." --output ./prd-extract.json
```

**Output**: `prd-extract.json`
- Title, version, requirements, dependencies
- Version history
- Raw markdown content

---

### Phase 2: Analyze GitHub Repository

Analyze the actual codebase for architecture context.

**Script**: `scripts/github-analyzer.py`
```bash
python scripts/github-analyzer.py --repo "org/backend" --branch main --output ./github-analysis.json
```

**Output**: `github-analysis.json`
- Tech stack (framework, database, ORM, queue)
- Directory structure
- Integration points (where new feature hooks in)
- Constraints (linting, testing, CI/CD)
- Risk assessment

---

### Phase 3: Generate Versioned TDD in Notion

Create the Technical Design Document as a Notion page.

**Script**: `scripts/notion-tdd-creator.py`
```bash
python scripts/notion-tdd-creator.py   --database-id "$NOTION_TDD_DATABASE_ID"   --title "TDD-042-v1.0.0"   --version "1.0.0"   --prd-version "2.1.0"   --prd-url "https://notion.so/prd-042"   --content-file ./TDD-content.md   --status "Draft"
```

**Notion TDD Database Schema** (user must create this):
| Property | Type | Purpose |
|----------|------|---------|
| Name | Title | TDD title (e.g., "TDD-042-v1.0.0") |
| Version | Rich Text | TDD version (e.g., "1.0.0") |
| PRD Version | Rich Text | Parent PRD version |
| Status | Select | Draft / In Review / Approved / Implemented |
| PRD | URL | Link to parent PRD |
| FigJam | URL | Link to FigJam file |
| GitHub Repo | URL | Repository URL |
| Author | People | Document author |
| Created | Date | Creation date |
| Last Updated | Date | Last update |

**TDD Content Structure in Notion**:

```
📄 TDD-042-v1.0.0 (PRD v2.1.0)
│
├── 📋 Document Metadata (Table)
│   ├── TDD ID: TDD-042-v1.0.0
│   ├── TDD Version: 1.0.0
│   ├── Parent PRD: [PRD-042 v2.1.0]
│   ├── Status: Draft
│   ├── Created: 2026-06-23
│   └── Author: Claude
│
├── 📜 Version History (Table)
│   ├── TDD v1.0.0 | PRD v2.1.0 | 2026-06-23 | Initial design
│
├── 📝 1. Executive Summary
├── 📝 2. PRD Requirements Mapping (Table)
│   ├── REQ-001 | Description | Technical Approach | Status | Effort
├── 🏗️ 3. System Architecture → [FigJam Link]
├── 🗄️ 4. Data Model → [FigJam Link]
├── 🔌 5. API Design (Code blocks)
├── 📅 6. Implementation Timeline ⭐
│   ├── 6.1 Phase Breakdown (Table)
│   │   ├── Phase | Deliverable | Owner | Duration | Dependencies
│   ├── 6.2 Timeline Diagram → [FigJam Link]
│   ├── 6.3 Milestones & Gates
│   └── 6.4 Resource Allocation
├── 🧪 7. Testing Strategy
├── ⚙️ 8. Operational Considerations
│   ├── 8.1 Monitoring & Alerting
│   ├── 8.2 Rollback Plan
│   └── 8.3 Security Considerations
├── ❓ 9. Open Questions & Risks (Table)
└── 📎 10. Appendix
```

**Implementation Timeline Section (Section 6)**:

This is the **core visual section** of the TDD. It includes:

1. **Phase Breakdown Table**:
| Phase | Deliverable | Owner | Duration | Start Date | End Date | Dependencies | Status |
|-------|-------------|-------|----------|------------|----------|--------------|--------|
| Phase 1: Setup | Repo scaffolding, CI/CD | TBD | 2d | Week 1 | Week 1 | None | Planned |
| Phase 2: Data Model | Schema design, migration | TBD | 3d | Week 1 | Week 2 | Phase 1 | Planned |
| Phase 3: Core Service | Business logic | TBD | 5d | Week 2 | Week 3 | Phase 2 | Planned |
| Phase 4: API Layer | REST/GraphQL endpoints | TBD | 3d | Week 3 | Week 3 | Phase 3 | Planned |
| Phase 5: Frontend | UI integration | TBD | 4d | Week 3 | Week 4 | Phase 4 | Planned |
| Phase 6: Testing | Unit, integration, E2E | TBD | 3d | Week 4 | Week 4 | Phase 5 | Planned |
| Phase 7: Deployment | Staging, production | TBD | 2d | Week 5 | Week 5 | Phase 6 | Planned |

2. **Timeline Diagram** → Links to FigJam file with visual Gantt chart

3. **Milestones & Gates**:
- Milestone 1: Data model approved (end of Phase 2)
- Milestone 2: API contract signed off (end of Phase 4)
- Milestone 3: Feature complete (end of Phase 5)
- Milestone 4: Production ready (end of Phase 7)

4. **Resource Allocation**:
- Backend engineers: Phases 1-4, 6-7
- Frontend engineers: Phases 5
- DevOps: Phases 1, 7
- QA: Phases 6

**Version Delta** (if updating):
When PRD updates, prepend to Notion page:
```
⚠️ Delta: TDD v{old} → v{new} (triggered by PRD v{old_prd} → v{new_prd})

Added:
• {new requirements}

Modified:
• {changed requirements}

Timeline Changes:
• {added/removed phases, duration changes}
```

---

### Phase 4: Create Design FigJam

Create architecture diagrams in FigJam.

**Step 1: Create FigJam file via Figma API**
```bash
python scripts/figjam-creator.py   --name "TDD-042-v1.0.0 (PRD v2.1.0)"   --output ./figjam-info.json
```

**Step 2: Generate context-aware diagrams**
```bash
python scripts/diagram-generator.py   --tdd ./TDD-content.md   --github-analysis ./github-analysis.json   --prd ./prd-extract.json   --output-dir ./diagrams/
```

**Step 3: User imports into FigJam**
```
📋 FigJam Setup Instructions:

1. Open FigJam file: {figjam_url}
2. File → Import → Select these .excalidraw files:
   • system-architecture.excalidraw
   • data-model.excalidraw
   • timeline.excalidraw
3. The diagrams import with all shapes, colors, and arrows preserved.
4. Arrange on canvas as needed.
5. For Mermaid diagrams (api-flow.mmd, state-machine.mmd):
   • Use Mermaid Live Editor (mermaid.live)
   • Screenshot and paste into FigJam
```

**Diagrams in FigJam**:

| Diagram | Source | Format | Version Watermark |
|---------|--------|--------|-------------------|
| System Architecture | GitHub repo + PRD | Excalidraw | TDD v{X.Y.Z} \| PRD v{A.B.C} \| Repo Analysis |
| Data Model / ERD | PRD entities + schema | Excalidraw | TDD v{X.Y.Z} \| PRD v{A.B.C} \| Data Model |
| API Flow | GitHub routes + PRD | Mermaid → Screenshot | TDD v{X.Y.Z} \| API Flow |
| State Machine | PRD states | Mermaid → Screenshot | TDD v{X.Y.Z} \| State Machine |
| Implementation Timeline | PRD phases + complexity | Excalidraw | TDD v{X.Y.Z} \| Timeline |

**Color Coding**:
- 🟩 Green = New components/entities required by PRD
- 🟦 Blue = Existing components from GitHub repository
- 🟧 Orange = API Gateway / external interfaces
- 🟥 Red = Data stores
- 🟪 Purple = Infrastructure (queues, caches)

---

### Phase 5: Version Registry

Maintain the permanent mapping.

**Registry**: `version-registry.json`
```json
{
  "project_name": "My Product",
  "last_updated": "2026-06-23T14:12:00Z",
  "mappings": [
    {
      "mapping_id": "map-abc123",
      "prd": {
        "id": "PRD-042",
        "version": "2.1.0",
        "notion_url": "https://notion.so/prd-042"
      },
      "tdd": {
        "version": "1.0.0",
        "status": "draft",
        "notion_url": "https://notion.so/tdd-042-v1-0-0",
        "figjam_url": "https://figma.com/file/abc123"
      },
      "github_analysis": {
        "repo": "org/backend",
        "commit": "abc123"
      },
      "created_at": "2026-06-23T14:12:00Z",
      "parent_mapping": null,
      "changelog": "Initial: PRD v2.1.0 → TDD v1.0.0 → FigJam v1.0.0"
    }
  ]
}
```

**Update on PRD version change**:
```json
{
  "mapping_id": "map-def456",
  "prd": {"id": "PRD-042", "version": "2.2.0"},
  "tdd": {
    "version": "1.1.0",
    "status": "draft",
    "notion_url": "...",
    "figjam_url": "..."
  },
  "parent_mapping": "map-abc123",
  "changelog": "PRD v2.2.0 added REQ-005 (real-time notifications). TDD v1.1.0 adds WebSocket + Redis. FigJam updated with new components."
}
```

---

### Phase 6: Final Output

**Present to User**:

```markdown
## ✅ Two Deliverables Complete

### 🎨 1. Design FigJam
**File**: [TDD-042-v1.0.0 (PRD v2.1.0)]({figjam_url})
**Version**: FigJam v1.0.0 (matches TDD v1.0.0)
**Diagrams**:
- System Architecture (6 components: 3 existing, 3 new)
- Data Model (4 entities: 2 existing, 2 new)
- API Flow (5 endpoints: 2 from repo, 3 from PRD)
- State Machine (5 states from PRD lifecycle)
- Implementation Timeline (7 phases)

**Import Status**: Ready for .excalidraw import

---

### 📝 2. Notion TDD with Implementation Timeline
**Page**: [TDD-042-v1.0.0]({notion_tdd_url})
**Version**: TDD v1.0.0 (PRD v2.1.0)
**Status**: Draft
**Key Sections**:
- ✅ Document Metadata with version
- ✅ Version History table
- ✅ PRD Requirements Mapping (all REQ mapped)
- ✅ System Architecture → FigJam link
- ✅ Data Model → FigJam link
- ✅ API Design with code blocks
- ⭐ **Implementation Timeline** (7 phases, 22 days total)
- ✅ Testing Strategy
- ✅ Operational Considerations
- ✅ Open Questions & Risks

**Timeline Summary**:
| Metric | Value |
|--------|-------|
| Total Phases | 7 |
| Total Duration | 22 days |
| Parallel Work Possible | Phases 1-2, 3-4 |
| Critical Path | Phase 1 → 2 → 3 → 4 → 5 → 6 → 7 |
| Risk Buffer | 3 days |

---

### 📋 Version Mapping
PRD v2.1.0 → TDD v1.0.0 → FigJam v1.0.0
Registry: map-abc123

### Next Steps
1. [ ] Review TDD in Notion
2. [ ] Import .excalidraw files into FigJam
3. [ ] Share Notion TDD with engineering team
4. [ ] Update Status to "In Review" in Notion
5. [ ] Once approved, update Status to "Approved"
```

---

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/notion-extract.py` | Extract PRD from Notion |
| `scripts/github-analyzer.py` | Analyze GitHub repo |
| `scripts/notion-tdd-creator.py` | Create TDD page in Notion database |
| `scripts/figjam-creator.py` | Create FigJam file via Figma API |
| `scripts/diagram-generator.py` | Generate context-aware diagrams |
| `scripts/registry-manager.py` | Manage version mappings |

---

## Quality Checklist

- [ ] Notion TDD page created with correct Version property
- [ ] Notion TDD has Implementation Timeline section (Section 6)
- [ ] Timeline includes phase table, milestones, resource allocation
- [ ] FigJam file created with version in name
- [ ] All diagrams have version watermark
- [ ] Diagrams reflect actual repo components (blue) + PRD requirements (green)
- [ ] Version registry updated with Notion + FigJam URLs
- [ ] PRD linked back to TDD in Notion
- [ ] Delta section exists if version update
- [ ] Open questions explicitly listed
