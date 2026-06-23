# Excalidraw JSON Format Reference

## File Structure
```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "prd-to-tech-design-skill",
  "elements": [...],
  "appState": {
    "gridSize": 20,
    "viewBackgroundColor": "#ffffff"
  },
  "files": {}
}
```

## Element Types

### Rectangle
```json
{
  "id": "unique-id",
  "type": "rectangle",
  "x": 100, "y": 100,
  "width": 200, "height": 100,
  "angle": 0,
  "strokeColor": "#1976d2",
  "backgroundColor": "#e3f2fd",
  "fillStyle": "solid",
  "strokeWidth": 2,
  "strokeStyle": "solid",
  "roughness": 1,
  "opacity": 100,
  "roundness": {"type": 3, "value": 8},
  "boundElements": [{"type": "text", "id": "text-id"}]
}
```

### Text
```json
{
  "id": "text-id",
  "type": "text",
  "x": 100, "y": 130,
  "width": 200, "height": 40,
  "text": "Component Name",
  "fontSize": 16,
  "fontFamily": 1,
  "textAlign": "center",
  "verticalAlign": "middle",
  "containerId": "rectangle-id"
}
```

### Arrow
```json
{
  "id": "arrow-id",
  "type": "arrow",
  "x": 300, "y": 150,
  "width": 100, "height": 0,
  "points": [[0, 0], [100, 0]],
  "endArrowhead": "arrow"
}
```

### Ellipse
```json
{
  "id": "ellipse-id",
  "type": "ellipse",
  "x": 100, "y": 100,
  "width": 50, "height": 50,
  "backgroundColor": "#1976d2"
}
```

## Color Scheme for Architecture Diagrams
| Component Type | Fill | Stroke |
|---------------|------|--------|
| Existing System | `#e3f2fd` | `#1565c0` |
| New Component | `#e8f5e9` | `#2e7d32` |
| External Service | `#fff3e0` | `#ef6c00` |
| Data Store | `#fce4ec` | `#c62828` |
| User/Client | `#ffffff` | `#424242` |
| Connection | — | `#666666` |
