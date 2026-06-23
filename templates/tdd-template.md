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
| 1.0.0 | {A.B.C} | {date} | Claude | Initial design |

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
