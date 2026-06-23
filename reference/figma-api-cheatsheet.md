# Figma API Cheatsheet

## Authentication
- Personal access token from Figma account settings
- Scope: `file_read`, `file_write` (for creating files)

## Key Endpoints
```
POST /v1/files                    → Create new file (returns file_key)
GET  /v1/files/{file_key}         → Get file content
GET  /v1/files/{file_key}/comments → Get comments
POST /v1/files/{file_key}/comments → Add comment
```

## FigJam Specifics
- FigJam files are created with `editor_type: "figjam"` in POST /v1/files
- REST API does NOT support adding shapes/nodes to FigJam programmatically
- Workaround: Use Figma Plugin API (requires running a plugin in the browser)
- Alternative: Generate Excalidraw files → import into FigJam via UI

## Excalidraw → FigJam Import
1. Open FigJam
2. File → Import
3. Select `.excalidraw` file
4. All shapes, text, and arrows import natively
5. Colors and styles are preserved

## Recommended Workflow
1. Generate diagrams as `.excalidraw` files (programmatic)
2. Create empty FigJam file via API (optional)
3. Provide user with import instructions
4. User drags `.excalidraw` files into FigJam
