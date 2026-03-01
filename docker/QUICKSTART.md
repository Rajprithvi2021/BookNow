# BookNow Docker Deployment Guide

## Quick Start

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 2GB free disk space

### Start Services

**Linux/Mac:**
```bash
cd docker
chmod +x start.sh
./start.sh
```

**Windows:**
```bash
cd docker
start.bat
```

## Accessing Services

Once running, access:
- **Frontend:** http://localhost:3000
- **Backend:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Database (Adminer):** http://localhost:8081

## Database Access

**Connection String:**
```
postgresql://booknow:booknow_secure_pass_123@localhost:5432/booknow
```

**Credentials:**
- Host: localhost
- Port: 5432
- User: booknow
- Password: booknow_secure_pass_123
- Database: booknow

## Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Checking Status

```bash
# View running containers
docker ps

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
```

## Troubleshooting

### Port Already in Use
```bash
# Find and kill process using port
lsof -i :8000
kill -9 <PID>

# Or change port in docker-compose.yml
```

### Database Connection Error
```bash
# Restart database
docker-compose restart db

# Check logs
docker-compose logs db
```

### Build Issues
```bash
# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

## Advanced Usage

### Run Commands in Containers

```bash
# Seed database
docker-compose exec backend python -m scripts.seed_db

# Run tests
docker-compose exec backend pytest

# Access database shell
docker-compose exec db psql -U booknow -d booknow
```

### View Container Details
```bash
# CPU/Memory usage
docker stats

# Container logs with timestamps
docker logs --timestamps booknow-backend

# Inspect container
docker inspect booknow-backend
```

## Configuration

### Environment Variables

Edit `.env` file to customize:
```bash
DB_USER=booknow
DB_PASSWORD=your_secure_password
FRONTEND_URL=http://localhost:3000
```

### Resource Limits

Modify `docker-compose.yml`:
```yaml
services:
  backend:
    resources:
      limits:
        memory: 1G
```

## Production Deployment

For production, use separate config:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

Requires:
- `.env.prod` with secure passwords
- SSL certificates in `nginx/ssl/`
- Properly configured domain names

## Support

Check `/DOCKER.md` for comprehensive documentation.

