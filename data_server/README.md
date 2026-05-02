# data_server README

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Database
Create a .env file from .env.example:
```bash
cp .env.example .env
```
Update MariaDB credentials in .env

### 3. Initialize Database Schema
```bash
mysql -h <host> -u <user> -p <database> < migrations/001_initial_schema.sql
```

### 4. Create Admin User (optional, for testing)
```bash
python scripts/create_user.py --username admin --password secret
```

### 5. Run Server
**Development:**
```bash
python app.py
```

**Production (with gunicorn):**
```bash
gunicorn -w 4 -b 0.0.0.0:5001 app:create_app()
```

## API Documentation
See [API_CONTRACT.md](API_CONTRACT.md) for full endpoint documentation.

## Quick Test
```bash
# Login
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"secret"}'

# Health check
curl http://localhost:5001/health
```
