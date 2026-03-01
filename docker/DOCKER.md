# BookNow Docker Documentation

Complete Docker setup for the BookNow appointment booking system.

## Directory Structure

```
docker/
├── start.sh                 # Linux/Mac startup script
├── start.bat               # Windows startup script
├── docker-compose.dev.yml  # Development environment
├── docker-compose.prod.yml # Production environment
├── backend/
│   └── Dockerfile          # Backend API image
├── frontend/
│   └── Dockerfile          # Frontend app image
├── nginx/
│   ├── nginx.conf          # Reverse proxy config
│   └── ssl/                # SSL certificates (production)
└── database/
    └── init-db.sql         # Database initialization
```

## Quick Start

### Linux/Mac
```bash
cd docker
chmod +x start.sh
./start.sh
```

### Windows
```bash
cd docker
start.bat
```

## Manual Setup

### Development Environment

```bash
# From project root
docker-compose -f docker/docker-compose.dev.yml up -d

# View logs
docker-compose -f docker/docker-compose.dev.yml logs -f

# Stop services
docker-compose -f docker/docker-compose.dev.yml down
```

### Production Environment

```bash
# Create .env.prod with production secrets
cp .env.example .env.prod

# Edit .env.prod with production credentials
DB_PASSWORD=<secure-password>
API_URL=https://api.booknow.example.com
FRONTEND_URL=https://booknow.example.com

# Run production setup
docker-compose -f docker/docker-compose.prod.yml up -d
```

## Services

### 1. Database (PostgreSQL 15)
- **Container:** booknow-db
- **Port:** 5432
- **User:** booknow
- **Database:** booknow
- **Volume:** postgres_data:/var/lib/postgresql/data

### 2. Backend API (FastAPI)
- **Container:** booknow-backend
- **Port:** 8000
- **Health Check:** http://localhost:8000/api/health
- **API Docs:** http://localhost:8000/docs
- **Features:** Auto-reload, hot-swap code changes

### 3. Frontend (Next.js)
- **Container:** booknow-frontend
- **Port:** 3000
- **URL:** http://localhost:3000
- **Features:** Hot module reload (HMR)

### 4. Adminer (Dev Only)
- **Container:** booknow-adminer
- **Port:** 8081
- **URL:** http://localhost:8081
- **Use:** Database management UI

### 5. PgAdmin (Dev Only)
- **Container:** booknow-pgadmin
- **Port:** 5050
- **URL:** http://localhost:5050
- **Credentials:** admin@booknow.dev / admin

### 6. Nginx (Prod Only)
- **Container:** booknow-nginx
- **Port:** 80, 443
- **Config:** nginx.conf
- **Function:** Reverse proxy & load balancer

## Environment Variables

### .env File
```bash
# Database
DB_USER=booknow
DB_PASSWORD=booknow_secure_pass_123
DB_NAME=booknow

# API
API_HOST=0.0.0.0
API_PORT=8000

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000/api

# Logging
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
```

## Database Access

### From Container
```bash
docker-compose exec db psql -U booknow -d booknow
```

### From Local
```bash
psql -h localhost -U booknow -d booknow -p 5432
```

### From Adminer (Dev)
1. Open http://localhost:8081
2. Server: db
3. Username: booknow
4. Password: booknow_secure_pass_123
5. Database: booknow

## Common Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db
```

### Restart Services
```bash
# All
docker-compose restart

# Specific
docker-compose restart backend
docker-compose restart frontend
```

### Remove Everything
```bash
# Stop and remove containers
docker-compose down

# Also remove volumes (WARNING: deletes data)
docker-compose down -v

# Remove images
docker rmi booknow-backend:latest booknow-frontend:latest
```

### Build Images
```bash
# Rebuild all
docker-compose build --no-cache

# Rebuild backend only
docker-compose build --no-cache backend

# Rebuild frontend only
docker-compose build --no-cache frontend
```

### Shell Access
```bash
# Backend container
docker-compose exec backend bash

# Frontend container
docker-compose exec frontend sh

# Database container
docker-compose exec db sh
```

### Run Commands in Container
```bash
# Seed database
docker-compose exec backend python -m scripts.seed_db

# Run tests
docker-compose exec backend pytest

# Django shell (if enabled)
docker-compose exec backend python manage.py shell
```

## Troubleshooting

### Port Already in Use
```bash
# Find service using port
lsof -i :8000  # Backend
lsof -i :3000  # Frontend
lsof -i :5432  # Database

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml
ports:
  - "8001:8000"  # Map 8001 to 8000
```

### Database Connection Error
```bash
# Check database health
docker-compose exec db pg_isready -U booknow

# Restart database
docker-compose restart db

# Check database logs
docker-compose logs db
```

### Backend Health Check Failing
```bash
# Check backend logs
docker-compose logs backend

# Verify settings
docker-compose exec backend python -c "from src.core.config import Settings; print(Settings())"

# Check database connection
docker-compose exec backend python -c "from src.db.connection import SessionLocal; s = SessionLocal(); print('DB OK')"
```

### Frontend Not Connecting to Backend
```bash
# Verify API URL in frontend
docker-compose exec frontend cat .env.local

# Test API from frontend container
docker-compose exec frontend wget -O- http://backend:8000/api/health
```

## Performance Tuning

### Development
- **Uvicorn:** Single worker (--reload enabled)
- **Next.js:** Fast refresh for development
- **PostgreSQL:** Default settings

### Production
- **Uvicorn:** Multiple workers (4x CPU cores)
- **Next.js:** Optimized build
- **PostgreSQL:** 256MB shared_buffers, 1GB effective_cache_size
- **Nginx:** Gzip compression, caching headers

## Security Considerations

### Development
- ⚠️ Debug mode enabled
- ⚠️ CORS: Allow all origins
- ⚠️ No HTTPS
- ⚠️ Default passwords

### Production
- ✅ Debug mode disabled
- ✅ CORS: Specific origins only
- ✅ HTTPS only (Nginx)
- ✅ Strong passwords (via .env.prod)
- ✅ No public database access
- ✅ Health checks enabled
- ✅ Resource limits set
- ✅ Logging enabled

## Monitoring & Logging

### View Metrics
```bash
# CPU/Memory usage
docker stats

# Container details
docker inspect booknow-backend

# Network stats
docker network inspect booknow-network
```

### Persistent Logs
```bash
# Enable persistent logging in docker-compose
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

# View logs
docker logs --tail 100 -f booknow-backend
```

## Deployment

### AWS ECS
1. Push images to ECR
2. Create ECS task definition using docker-compose
3. Deploy with `docker-compose up`

### Docker Swarm
```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.prod.yml booknow

# View status
docker stack services booknow
```

### Kubernetes
```bash
# Generate k8s manifests from docker-compose
docker-compose convert

# Or use Kompose
kompose convert -f docker-compose.prod.yml
```

### DigitalOcean App Platform
1. Connect GitHub repo
2. Upload docker-compose.yml
3. Set environment variables
4. Deploy

## Maintenance

### Regular Tasks
- Monitor disk space
- Backup database (`docker-compose exec db pg_dump`)
- Review logs for errors
- Update dependencies
- Security patches

### Cleanup
```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove unused networks
docker network prune

# Full cleanup
docker system prune -a
```

## Support

For issues or questions:
1. Check logs: `docker-compose logs`
2. Verify .env configuration
3. Review error messages
4. Run health checks
5. Check resource limits

---

**Last Updated:** 2026-03-01
**Version:** 1.0.0
