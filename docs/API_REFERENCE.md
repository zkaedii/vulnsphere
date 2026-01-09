# API Reference

## Base URL

```
http://localhost:8000
```

## Endpoints

### GET /

Root endpoint - returns system information.

**Response:**
```json
{
  "name": "VulnSphere PRIME",
  "version": "1.0.0",
  "status": "operational",
  "engine": "ZKAEDI PRIME",
  "fractal_order": 0.618
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "active_scans": 0,
  "websocket_connections": 0
}
```

### POST /api/v1/scan/network

Initiate network vulnerability scan.

**Request Body:**
```json
{
  "192.168.1.1": ["192.168.1.2", "192.168.1.3"],
  "192.168.1.2": ["192.168.1.1"],
  "192.168.1.3": ["192.168.1.1"]
}
```

**Response:**
```json
{
  "status": "success",
  "scan_id": "scan_123",
  "converged": true,
  "iterations": 5000,
  "phase": "stable_detection",
  "vulnerabilities_detected": 3
}
```

## WebSocket

### Endpoint: /ws

Real-time updates for vulnerability scans.

**Message Types:**

1. **Subscribe to scan:**
```json
{
  "type": "subscribe_scan",
  "scan_id": "scan_123"
}
```

2. **MDM Suppression:**
```json
{
  "type": "mdm_suppression",
  "probe": {
    "id": "probe_1",
    "target_node": "192.168.1.1",
    "energy": 5.0
  }
}
```

**Received Messages:**

1. **Vulnerability detected:**
```json
{
  "type": "vuln_detected",
  "nodeId": "192.168.1.1",
  "cve": "CVE-2024-0001",
  "severity": "critical"
}
```

2. **Chaos mode:**
```json
{
  "type": "chaos_mode",
  "message": "Chaos mode activated"
}
```

## Authentication

Currently, authentication is not implemented. For production, add API key authentication.
