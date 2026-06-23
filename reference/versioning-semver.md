# SemVer for PRD/TDD Versioning

## PRD Versioning
- **MAJOR** (X.0.0): Fundamental scope change, new business requirements, architecture shift
- **MINOR** (x.Y.0): New features added, requirements expanded, new user stories
- **PATCH** (x.y.Z): Clarifications, typo fixes, acceptance criteria updates, no scope change

## TDD Versioning
- **MAJOR** (X.0.0): Architecture rewrite, tech stack change, breaking API changes
- **MINOR** (x.Y.0): New components, API additions, schema changes
- **PATCH** (x.y.Z): Implementation detail updates, estimates revised, no structural change

## Mapping Rules
1. PRD v1.0.0 → TDD v1.0.0 (initial)
2. PRD v1.1.0 (new features) → TDD v1.1.0 (new components)
3. PRD v2.0.0 (scope rewrite) → TDD v2.0.0 (architecture rewrite)
4. PRD v2.0.0 → TDD v1.2.0 (same architecture, new features) — VALID if architecture unchanged
5. PRD v1.0.0 → TDD v2.0.0 (architecture rewrite without PRD change) — VALID for tech debt

## Version Registry Format
```json
{
  "mapping_id": "map-abc123",
  "prd": {"id": "PRD-042", "version": "2.1.0"},
  "tdd": {"version": "1.0.0", "status": "draft"},
  "parent_mapping": null,
  "changelog": "Initial mapping"
}
```
