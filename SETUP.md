# 🚀 DobotHub Cloud Integration — Quick Start

## Architecture Overview

```
┌─────────────────┐         HTTPS REST         ┌──────────────────┐
│   DobotHub      │  ◄────────────────────►   │   data_server    │
│   (Client)      │     /api/auth/*            │   (Cloud Backend)│
│   Port 8080     │     /api/cloud/*           │   Port 5001      │
└─────────────────┘         MariaDB            └──────────────────┘
   - Local Sequences                              - User Auth (JWT)
   - Blockly Scripts                              - Project Storage
   - Robot I/O Control                            - Collaboration
```

---

## Setup Instructions

### 1. Start data_server (Cloud Backend)

```bash
cd data_server

# Install & setup (one-time)
./install.sh

# Configure database
cp .env.example .env
# Edit .env and set:
#  - MARIADB_PASSWORD (match your MariaDB setup)
#  - JWT_SECRET (any secure string)

# Create test user
source venv/bin/activate
python3 scripts/create_user.py --username admin --password geheim

# Start server
./start.sh
# Output: Starting Flask server on http://0.0.0.0:5001
```

### 2. Start DobotHub Client

```bash
cd ..  # Back to Dobot root

# Install dependencies (one-time)
./install.sh

# Start client on port 8080 (avoid macOS port 5000 conflict)
./start.sh 8080
# Output: Starting Flask server on http://localhost:8080
```

### 3. Test Integration

```bash
# In a new terminal, from Dobot root
python3 test_integration.py
```

Expected output:
```
✓ Server health check
✓ Client homepage loads
✓ Client status: not authenticated
✓ Server login endpoint
✓ Client login proxy
✓ Client status: authenticated + online
✓ Get cloud projects list
```

### 4. Test in Browser

1. Open **http://localhost:8080** (or your client IP:8080)
2. Click **"Login"** button (top right)
3. Enter credentials:
   - Username: `admin`
   - Password: `geheim`
4. Verify cloud status shows **"● ONLINE (admin)"** in header
5. Click **"Logout"** to test revocation

---

## Offline Mode Test

To test offline-first behavior:

1. Login successfully (verify online status)
2. Stop data_server: `Ctrl+C` in server terminal
3. Try to save a project
4. Expected: Save succeeds locally (status: 202 Accepted)
5. Restart data_server
6. Changes sync automatically when connection restored

---

## Configuration

### Client (.env)
Set where data_server is located:
```bash
export DOBOT_DATA_SERVER=http://your-server-ip:5001
```

### Server (data_server/.env)
```
CORS_ORIGINS=http://localhost:8080,http://192.168.x.x:8080
MARIADB_HOST=localhost
MARIADB_USER=dobot_user
MARIADB_PASSWORD=your_password
JWT_SECRET=your-jwt-secret-key
```

---

## Endpoints

### Client Endpoints
- `GET /` — UI homepage
- `GET /api/auth/status` — Get auth status
- `POST /api/auth/login` — Login (proxies to data_server)
- `POST /api/auth/logout` — Logout
- `GET /api/cloud/projects` — List remote projects
- `POST /api/cloud/projects` — Save project to cloud

### Server Endpoints (data_server)
- `GET /health` — Health check
- `POST /api/auth/login` — Authenticate user
- `POST /api/auth/logout` — Revoke session
- `POST /api/auth/validate` — Check token validity
- `GET /api/projects` — List projects
- `POST /api/projects` — Create project
- `PUT /api/projects/<id>` — Update project (with conflict detection)
- `DELETE /api/projects/<id>` — Delete project
- `POST /api/projects/<id>/lock` — Acquire advisory lock
- `POST /api/projects/<id>/unlock` — Release lock
- `POST /api/projects/<id>/presence` — Heartbeat for collaboration
- `POST /api/projects/<id>/events` — Append collaboration event
- `GET /api/projects/<id>/events?since=<seq>` — Replay events

---

## Troubleshooting

### Port Conflict on macOS
Port 5000 is used by Control Center. Use 8080 or higher for client.

### SSL/LibreSSL Warning
Harmless warning on macOS. Use `requests` with `urllib3` v1.x or ignore the warning.

### Database Connection Refused
```
pymysql.err.OperationalError: (1045, "Access denied for user 'dobot_user'")
```
- Verify MariaDB is running
- Check MARIADB_PASSWORD in `.env` matches database user
- Create user: `CREATE USER 'dobot_user'@'localhost' IDENTIFIED BY 'password';`
- Grant permissions: `GRANT ALL ON dobot_hub.* TO 'dobot_user'@'localhost';`

### CORS Errors
If frontend can't reach server, update `CORS_ORIGINS` in `data_server/.env`:
```
CORS_ORIGINS=http://localhost:8080,http://client-ip:8080
```

---

## Files & Structure

```
Dobot/
├── web_server.py           # Client backend (DobotHub)
├── static/index.html       # Client UI with login modal
├── requirements.txt        # Client dependencies
├── start.sh               # Client launcher (now with port param)
├── install.sh             # Client setup
├── test_integration.py    # Integration tests
├── data_server/
│   ├── app.py            # Server entrypoint
│   ├── config.py         # Config loader
│   ├── models.py         # SQLAlchemy ORM
│   ├── utils.py          # JWT + auth utils
│   ├── routes/
│   │   ├── auth.py       # Login/logout/validate
│   │   ├── projects.py   # CRUD + revision conflict detection
│   │   └── collab.py     # Lock/presence/events
│   ├── migrations/
│   │   └── 001_initial_schema.sql
│   ├── scripts/
│   │   ├── create_user.py
│   │   └── test_auth_api.py
│   ├── requirements.txt
│   ├── start.sh          # Server launcher
│   ├── install.sh        # Server setup
│   ├── .env              # Configuration (create from .env.example)
│   ├── .env.example      # Config template
│   └── README.md
```

---

## Next Steps

- ✅ Phase 1-2: API contract, models, migrations
- ✅ Phase 3: Authentication endpoints
- ✅ Phase 4: Client integration + login UI
- 🟡 Phase 5: Conflict resolution UI
- ⏳ Phase 6: Collaboration features (lock, events, presence)
- ⏳ Phase 7: Multi-user testing
- ⏳ Phase 8: Production deployment

---

## Support

For issues:
1. Check server logs: `tail -f data_server/data_server.log`
2. Check client network calls: Browser DevTools → Network tab
3. Run `python3 test_integration.py` to identify failing point
4. Review code in [data_server/routes/](data_server/routes/)
