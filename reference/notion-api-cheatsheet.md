# Notion API Cheatsheet

## Authentication
- Integration token from https://www.notion.so/my-integrations
- Required capabilities: Read content, Read user information

## Key Endpoints
```
GET  /v1/pages/{page_id}          → Page metadata + properties
GET  /v1/blocks/{block_id}/children → Page content blocks
POST /v1/databases/{db_id}/query  → Query database entries
```

## Common Property Types
| Type | JSON Path | Example |
|------|-----------|---------|
| Title | `.properties.Name.title[0].plain_text` | "User Export PRD" |
| Rich Text | `.properties.Version.rich_text[0].plain_text` | "2.1.0" |
| Select | `.properties.Status.select.name` | "Ready for Tech Design" |
| Multi-select | `.properties.Tags.multi_select[].name` | ["Backend", "P0"] |
| Date | `.properties.Due.date.start` | "2026-06-30" |
| Relation | `.properties.Related_PRD.relation[].id` | ["page-id-1"] |

## Page ID Formats
- With dashes: `abc12345-6789-0def-1234-567890abcdef`
- Without dashes: `abc1234567890def1234567890abcdef`
- In URL: `https://notion.so/workspace/abc12345-6789-0def-1234-567890abcdef`

## Block Types for PRD Parsing
- `heading_1`, `heading_2`, `heading_3` — Section headers
- `paragraph` — Body text
- `bulleted_list_item` — Bullet points (requirements, AC)
- `numbered_list_item` — Numbered lists
- `to_do` — Checklist items
- `code` — Code blocks
- `quote` — Callouts/notes
- `divider` — Horizontal rules
- `table` — Structured data (rare in PRDs)
