# BookNow Services Configuration

## Environment Template

Copy this file to `.env` and fill in your values:

```bash
# Database Configuration
DB_USER=booknow
DB_PASSWORD=booknow_secure_pass_123
DB_NAME=booknow

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_URL=http://localhost:8000

# Frontend Configuration
FRONTEND_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000/api

# Python Configuration
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1

# Node Configuration
NODE_ENV=development

# Debug Mode (disable in production)
DEBUG=False
```

## Service Discovery

Services communicate via internal Docker network:

- **Backend API:** http://backend:8000
- **Frontend:** http://frontend:3000
- **Database:** postgresql://db:5432

## Health Checks

All services have health checks:

```bash
# Backend Health
docker-compose exec backend python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"

# Frontend Health
docker-compose exec frontend wget -O- http://localhost:3000

# Database Health
docker-compose exec db pg_isready -U booknow
```

## Port Mappings

| Service | Internal | External | URL |
|---------|----------|----------|-----|
| PostgreSQL | 5432 | 5432 | - |
| Backend | 8000 | 8000 | http://localhost:8000 |
| Frontend | 3000 | 3000 | http://localhost:3000 |
| Adminer | 8080 | 8081 | http://localhost:8081 |
| PgAdmin | 80 | 5050 | http://localhost:5050 |
| Nginx | 80,443 | 80,443 | http://localhost |

## Volume Mounts

### Development
- Backend: `./backend/src` → `/app/src` (live reload)
- Frontend: `./frontend/src` → `/app/src` (hot reload)
- Database: `postgres_data` → `/var/lib/postgresql/data`

### Production
- Database only: `postgres_data_prod` → `/var/lib/postgresql/data`
- Static files served by Nginx

## Network

All services connect via `booknow-network`:
- Bridge network
- Auto DNS resolution
- Service-to-service communication

## Resource Limits (Optional)

```yaml
services:
  backend:
    resources:
      limits:
        cpus: '1'
        memory: 1G
      reservations:
        cpus: '0.5'
        memory: 512M
```

## Restart Policies

- **development:** `unless-stopped`
- **production:** `always`

## Logging

- Driver: json-file
- Max size: 10M
- Max files: 3
- View: `docker-compose logs -f`
