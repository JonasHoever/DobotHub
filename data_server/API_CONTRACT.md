# API Contract: DobotHub Client ↔ data_server

## Overview
- **data_server**: Stateless cloud service (MariaDB, auth, project storage, collaboration)
- **DobotHub Client**: Local offline-first app (robot control, sequences, scripts, sync queue)
- **Connection**: HTTPS REST + optional WebSocket for presence/events
- **Auth Model**: Shared team login → JWT token → multiple concurrent sessions

---

## Auth Endpoints

### POST /api/auth/login
**Request:**
```json
{
  "username": "team_user",
  "password": "team_password"
}
```
**Response (200):**
```json
{
  "ok": true,
  "token": "eyJ0eXA...",
  "expires_in": 86400,
  "user_id": "user_123",
  "session_id": "sess_abc"
}
```
**Response (401):** `{ "error": "Invalid credentials" }`

---

### POST /api/auth/validate
**Headers:** `Authorization: Bearer <token>`  
**Response (200):**
```json
{
  "ok": true,
  "user_id": "user_123",
  "session_id": "sess_abc",
  "token_expires_in": 3600
}
```
**Response (401):** `{ "error": "Token invalid or expired" }`

---

### POST /api/auth/logout
**Headers:** `Authorization: Bearer <token>`  
**Response (200):** `{ "ok": true }`

---

## Project Storage Endpoints

### GET /api/projects
**Headers:** `Authorization: Bearer <token>`  
**Response (200):**
```json
{
  "projects": [
    {
      "id": "proj_123",
      "name": "color_sorting",
      "type": "sequence",
      "updated_by": "user_123",
      "updated_at": 1714734961,
      "revision": 5,
      "locked_by": null,
      "locked_at": null
    },
    {
      "id": "proj_124",
      "name": "blockly_demo",
      "type": "script",
      "updated_by": "user_123",
      "updated_at": 1714734800,
      "revision": 2,
      "locked_by": null,
      "locked_at": null
    }
  ]
}
```

---

### GET /api/projects/<project_id>
**Headers:** `Authorization: Bearer <token>`  
**Response (200):**
```json
{
  "project": {
    "id": "proj_123",
    "name": "color_sorting",
    "type": "sequence",
    "content": {
      "steps": [
        { "type": "move_to", "params": { "x": 200, "y": 0, "z": 50, "r": 0 } }
      ]
    },
    "blockly_xml": null,
    "python_code": null,
    "revision": 5,
    "updated_by": "user_123",
    "updated_at": 1714734961,
    "checksum": "sha256:abc123"
  }
}
```

---

### POST /api/projects
**Headers:** `Authorization: Bearer <token>`  
**Request:**
```json
{
  "name": "new_project",
  "type": "sequence",
  "content": { "steps": [] },
  "blockly_xml": null,
  "python_code": null
}
```
**Response (201):**
```json
{
  "project": {
    "id": "proj_new",
    "name": "new_project",
    "type": "sequence",
    "revision": 1,
    "updated_by": "user_123",
    "updated_at": 1714734961,
    "checksum": "sha256:def456"
  }
}
```

---

### PUT /api/projects/<project_id>
**Headers:** `Authorization: Bearer <token>`  
**Request:**
```json
{
  "content": { "steps": [...] },
  "blockly_xml": null,
  "python_code": null,
  "expected_revision": 5,
  "change_reason": "User edit: added move step"
}
```
**Response (200):** Project with new revision = 6

**Response (409 Conflict):**
```json
{
  "error": "revision_mismatch",
  "local_revision": 5,
  "server_revision": 6,
  "server_updated_by": "other_user",
  "server_updated_at": 1714734900,
  "server_content": { "steps": [...] }
}
```

---

### DELETE /api/projects/<project_id>
**Headers:** `Authorization: Bearer <token>`  
**Response (200):** `{ "ok": true }`

---

## Collaboration Endpoints

### POST /api/projects/<project_id>/lock
**Headers:** `Authorization: Bearer <token>`  
**Request:** `{ "session_id": "sess_abc", "ttl_seconds": 300 }`  
**Response (200):**
```json
{
  "locked": true,
  "locked_by": "user_123",
  "locked_until": 1714735261
}
```
**Response (409):**
```json
{
  "error": "locked_by_other",
  "locked_by": "other_user",
  "locked_until": 1714735261
}
```

---

### POST /api/projects/<project_id>/unlock
**Headers:** `Authorization: Bearer <token>`  
**Request:** `{ "session_id": "sess_abc" }`  
**Response (200):** `{ "ok": true }`

---

### POST /api/projects/<project_id>/presence
**Headers:** `Authorization: Bearer <token>`  
**Request:** `{ "session_id": "sess_abc", "action": "online" }`  
**Response (200):**
```json
{
  "presence": [
    { "user_id": "user_123", "session_id": "sess_abc", "last_heartbeat": 1714734961 },
    { "user_id": "user_123", "session_id": "sess_def", "last_heartbeat": 1714734960 }
  ]
}
```

---

### POST /api/projects/<project_id>/events
**Headers:** `Authorization: Bearer <token>`  
**Request:**
```json
{
  "event_type": "step_added",
  "step_index": 2,
  "step_data": { "type": "move_to", "params": {...} },
  "session_id": "sess_abc"
}
```
**Response (201):**
```json
{
  "event_id": "evt_456",
  "sequence": 10,
  "timestamp": 1714734961
}
```

---

### GET /api/projects/<project_id>/events?since=<sequence_num>
**Headers:** `Authorization: Bearer <token>`  
**Response (200):**
```json
{
  "events": [
    { "sequence": 10, "event_id": "evt_456", "event_type": "step_added", "timestamp": 1714734961, "user_id": "user_123" },
    { "sequence": 11, "event_id": "evt_457", "event_type": "step_edited", "timestamp": 1714734962, "user_id": "user_123" }
  ]
}
```

---

## Error Responses

All endpoints return one of:
- **200 OK** — success
- **201 Created** — resource created
- **400 Bad Request** — malformed input
- **401 Unauthorized** — missing/invalid token
- **403 Forbidden** — user lacks permission
- **404 Not Found** — resource not found
- **409 Conflict** — revision mismatch or lock conflict
- **500 Internal Server Error** — server error (log included)

---

## Data Models

### Project (in data_server)
```json
{
  "id": "proj_XYZ",
  "name": "string (unique per team)",
  "type": "sequence|script|blockly",
  "content": "JSON (sequence steps or blockly metadata)",
  "blockly_xml": "string (Blockly workspace XML) or null",
  "python_code": "string (generated Python code) or null",
  "revision": "integer (incremented on update)",
  "updated_by": "user_id",
  "updated_at": "unix timestamp",
  "locked_by": "user_id or null",
  "locked_until": "unix timestamp or null",
  "checksum": "sha256 hash for conflict detection"
}
```

### ProjectVersion (audit trail)
```json
{
  "id": "ver_ABC",
  "project_id": "proj_XYZ",
  "revision": 5,
  "content_snapshot": "full project JSON",
  "changed_by": "user_id",
  "changed_at": "unix timestamp",
  "change_reason": "User edit: added move step"
}
```

### CollaborationEvent
```json
{
  "id": "evt_456",
  "project_id": "proj_XYZ",
  "sequence": 10,
  "event_type": "step_added|step_edited|step_deleted|...",
  "payload": "JSON-specific to event type",
  "user_id": "user_id",
  "session_id": "sess_ABC",
  "timestamp": "unix timestamp"
}
```

### Presence
```json
{
  "user_id": "user_123",
  "session_id": "sess_ABC",
  "project_id": "proj_XYZ",
  "status": "online|idle|offline",
  "last_heartbeat": "unix timestamp"
}
```

---

## Client Sync Behavior

1. **Always write local first**: Before calling PUT /api/projects/<project_id>, DobotHub saves to local filesystem.
2. **Queue sync jobs**: Each remote operation goes into a retry queue with exponential backoff.
3. **Conflict resolution**: On 409, surface conflict dialog to user. Options:
   - Keep local (discard server changes)
   - Accept server (overwrite local)
   - Duplicate (save as new local project)
4. **Offline resilience**: If data_server unreachable, continue offline; queue jobs retry on reconnect.
5. **Lock semantics**: Before editing, acquire lock. Release on save or timeout. Lock is advisory (not enforced at data layer).

---

## Offline-First Principle

- ✅ All local save/load works without network
- ✅ All robot control (jog, sequence play, etc.) works offline
- ✅ Cloud sync is purely additive; no blocking operations
- ✅ Feature gates: cloud features hidden until authenticated
- ✅ Backward compat: existing sequences.json, scripts/, positions.json remain untouched
