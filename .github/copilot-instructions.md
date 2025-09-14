# SIIA Copilot Instructions

## Project Overview
SIIA (Sistema Inteligente de Irrigação Automatizada) is a greenhouse automation system with Flask web backend, Kivy mobile app, and IoT integration via MQTT.

## Architecture Components

### Core Services
- **Flask Web App** (`website/app.py`): Main backend with SQLAlchemy models, admin panel, mobile API
- **MQTT Client** (`website/lib/mqtt.py`): Handles IoT sensor data ingestion from greenhouse hardware
- **Mobile App** (`mobile/`): Kivy-based interface for field monitoring
- **PostgreSQL**: Primary database with Docker deployment

### Key Data Flow
1. IoT sensors → MQTT broker → `MQTTClient.process_message()` → SQLAlchemy models
2. Web admin interface uses role-based access with `@admin_required(level)` decorator (levels 2-5)
3. Mobile app communicates via REST API at `/api/mobile/*` endpoints with token authentication

## Development Patterns

### Authentication & Authorization
- Use `@admin_required(level)` for web routes (2=view, 3=edit, 4=manage sessions, 5=admin users)
- Mobile API uses `SessaoUsuario` tokens (7-day expiry) via `/api/mobile/login`
- Passwords hashed with Argon2: `ph.hash(password)` and `ph.verify(hash, password)`

### Database Conventions
- Models in `lib/models.py` with Flask-SQLAlchemy
- Foreign keys use constants: `USUARIO_ID = "usuario.id"`, `CULTURA_ID = "cultura.id"`
- MQTT data goes to `DadoPeriodico` table with real-time sensor readings

### Docker Development
- **Primary workflow**: `./setup.sh` → interactive Docker setup
- **Quick start**: `make start` (web+db) or `make mobile` (includes Kivy app)
- **Database**: `make db-init` to reset/seed data, `make db-clean` for full wipe
- Hot reload enabled for Flask code changes

## Essential Commands

```bash
# Setup & Development
./setup.sh                    # Interactive setup with .env configuration
make start                    # Start web + PostgreSQL
make mobile                   # Include mobile app (requires X11 on Linux)
make logs                     # View all container logs
make shell                    # Access Flask app container

# Database Management  
make db-init                  # Initialize/reset database with model.sql
./db-rm.sh                   # Complete cleanup (containers + volumes)
docker compose exec postgres psql -U lopinhos -d siia  # Direct DB access

# Testing
make test                     # Run full test suite
docker compose exec web pytest tests/test_auth.py -v   # Specific test file
```

## MQTT Integration Details
- Topics follow pattern: `estufa/{sensor_type}` (temperatura, umidade/ar, umidade/solo/#)
- Session-specific soil moisture: `estufa/umidade/solo/{sessao_id}`
- `MQTTClient` runs in background thread, auto-saves to `DadoPeriodico`
- Configure via `.env`: `MQTT_URL`, `MQTT_PORT`, `MQTT_USERNAME`, `MQTT_PASSWORD`

## Mobile API Patterns
- All mobile endpoints return JSON with consistent structure: `{"success": bool, "data": {}, "message": str}`
- Authentication header: `Authorization: Bearer {token}` 
- Key endpoints: `/api/mobile/dashboard` (sensor overview), `/api/mobile/culturas` (crop management)

## Testing Strategy
- `conftest.py` sets up in-memory SQLite for isolated tests
- Test categories: `test_auth.py`, `test_admin_routes.py`, `test_api_mobile.py`, `test_integration.py`
- Use fixtures: `@pytest.fixture` for `app`, `db_session`, `admin_user` setup
- Mock MQTT in tests to avoid broker dependency

## File Structure Navigation
- **Core logic**: `website/app.py` (all Flask routes), `lib/models.py` (SQLAlchemy models)
- **Infrastructure**: `docker-compose.yml` (services), `Dockerfile.web` (Flask), `Makefile` (dev commands)
- **Config**: `.env` (secrets), `init.sql`+`model.sql` (database schema)
- **Mobile**: `mobile/main.py` (entry point), `mobile/src/` (screens/services structure)