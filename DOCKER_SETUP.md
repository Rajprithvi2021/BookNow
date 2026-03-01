# 🐳 BookNow Docker Setup Guide

Complete Docker containerization for the BookNow appointment booking system.

## 📁 Docker Structure

```
docker/
├── 📄 start.sh                   # Linux/Mac startup script
├── 📄 start.bat                  # Windows startup script
├── 📄 docker-compose.dev.yml     # Development configuration
├── 📄 docker-compose.prod.yml    # Production configuration
├── 📄 DOCKER.md                  # Detailed documentation
├── 📄 QUICKSTART.md              # Quick start guide
├── 📄 README.md                  # Services overview
│
├── 📁 backend/
│   └── Dockerfile                # Backend Python image
│
├── 📁 frontend/
│   └── Dockerfile                # Frontend Next.js image
│
├── 📁 nginx/
│   ├── nginx.conf                # Reverse proxy configuration
│   └── ssl/                      # SSL certificates (production)
│
└── 📁 database/
    └── init-db.sql               # Database initialization script
```

## 🚀 Quick Start (All Platforms)

### Prerequisites
```bash
# Check Docker installation
docker --version        # Docker 20.10+
docker-compose version  # Docker Compose 2.0+
```

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

## 📊 Services

| Service | Port | Purpose |
|---------|------|---------|
| **PostgreSQL** | 5432 | Database |
| **Backend API** | 8000 | FastAPI application |
| **Frontend** | 3000 | Next.js application |
| **Adminer** | 8081 | DB Management (Dev) |
| **PgAdmin** | 5050 | PostgreSQL UI (Dev) |
| **Nginx** | 80/443 | Reverse Proxy (Prod) |

## 🌐 Access URLs

After startup:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Database Adminer:** http://localhost:8081
- **PgAdmin:** http://localhost:5050

## 🗄️ Database Credentials

```
Host:     localhost:5432
User:     booknow
Password: booknow_secure_pass_123
Database: booknow
```

## 📋 Configuration

### Environment File (.env)
```bash
# Copy template
cp .env.example .env

# Edit with your settings
DB_PASSWORD=your_secure_password
API_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
```

## 🛠️ Common Commands

```bash
# View all containers
docker ps

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Access container shell
docker-compose exec backend bash

# Run database commands
docker-compose exec db psql -U booknow -d booknow
```

## 🔄 Development Workflow

### Hot Reload Enabled
- **Backend:** Changes auto-reload with Uvicorn
- **Frontend:** Changes hot-reload with Next.js HMR
- **Database:** Persisted in Docker volume

### Code Changes
```bash
# Edit code in your editor
# Changes automatically apply to running containers

# View backend logs
docker-compose logs -f backend

# View frontend logs
docker-compose logs -f frontend
```

## 🧪 Running Tests

```bash
# Run all tests
docker-compose exec backend pytest -v

# Run specific test file
docker-compose exec backend pytest tests/test_concurrency.py -v

# Run with coverage
docker-compose exec backend pytest --cov=src
```

## 🌱 Database Operations

```bash
# Seed demo data
docker-compose exec backend python -m scripts.seed_db

# Database backup
docker-compose exec db pg_dump -U booknow booknow > backup.sql

# Database restore
docker-compose exec -T db psql -U booknow booknow < backup.sql

# Access database shell
docker-compose exec db psql -U booknow -d booknow
```

## 🔐 Production Deployment

### Setup Production Environment
```bash
# Create production config
cp docker/docker-compose.prod.yml docker-compose.yml

# Create secure .env.prod
DB_PASSWORD=<32-char-random-password>
API_URL=https://api.booknow.example.com
FRONTEND_URL=https://booknow.example.com
```

### Deploy
```bash
# Build and start
docker-compose up -d

# Verify all services running
docker ps

# View logs
docker-compose logs -f
```

### SSL/TLS Certificates
```bash
# Place certificates in nginx/ssl/
nginx/ssl/
├── cert.pem
└── key.pem

# Update nginx.conf with paths
```

## 🚨 Troubleshooting

### Port Already in Use
```bash
# Find process using port
lsof -i :8000      # Backend
lsof -i :3000      # Frontend
lsof -i :5432      # Database

# Kill process
kill -9 <PID>
```

### Database Connection Failed
```bash
# Restart database
docker-compose restart db

# Check database logs
docker-compose logs db

# Verify health
docker-compose ps
```

### Backend Health Check Failing
```bash
# Check logs
docker-compose logs backend

# Test API health directly
curl http://localhost:8000/api/health

# Verify database connection
docker-compose exec backend python -c "from src.db.connection import SessionLocal; SessionLocal()"
```

### Frontend Cannot Connect to Backend
```bash
# Verify API URL
docker-compose exec frontend cat .env.local

# Test from frontend container
docker-compose exec frontend wget -O- http://backend:8000/api/health

# Check Docker network
docker network inspect docker_booknow-network
```

## 📈 Performance

### Development Mode
- Single worker Uvicorn
- Hot reload enabled
- All debug logging

### Production Mode
- Multi-worker Uvicorn (4x CPU cores)
- Optimized builds
- Nginx caching
- Database tuning

```yaml
# Check resource usage
docker stats --no-stream

# Limit resources
resources:
  limits:
    cpus: '2'
    memory: 2G
```

## 🧹 Cleanup

```bash
# Stop and remove containers
docker-compose down

# Remove volumes (DELETE DATA!)
docker-compose down -v

# Remove images
docker rmi booknow-backend:latest booknow-frontend:latest

# Total cleanup
docker system prune -a
```

## 📖 Documentation Files

- **DOCKER.md** - Comprehensive Docker reference
- **QUICKSTART.md** - Quick start guide
- **README.md** - Services overview
- **.env.example** - Configuration template

## 🔗 Service Communication

### Internal (Container to Container)
```
backend    → http://db:5432
frontend   → http://backend:8000/api
nginx      → http://backend:8000
           → http://frontend:3000
```

### External (Host Machine)
```
browser    → http://localhost:3000 (frontend)
            http://localhost:8000 (backend)
postman    → http://localhost:8000/api/*
```

## 🔄 Deployment Options

### Docker Compose (Recommended for small deployments)
```bash
docker-compose -f docker/docker-compose.prod.yml up -d
```

### Docker Swarm
```bash
docker swarm init
docker stack deploy -c docker-compose.prod.yml booknow
```

### Kubernetes
```bash
kompose convert -f docker-compose.prod.yml
kubectl apply -f <generated-manifests>
```

### Cloud Platforms
- **AWS ECS:** Push images, use docker-compose as task definition
- **DigitalOcean App:** Upload docker-compose.yml
- **Heroku:** Use container Stack
- **Railway/Render:** Deploy from container registry

## 📝 Environment Variables

### Required (Development)
- DB_USER
- DB_PASSWORD
- DB_NAME

### Optional
- API_PORT (default: 8000)
- FRONTEND_URL (default: http://localhost:3000)
- NODE_ENV (default: development)

### Production Only
- POSTGRES_SSL_MODE
- SECRET_KEY
- ALLOWED_HOSTS

## 🎓 Learning Resources

- Docker: https://docs.docker.com/
- Docker Compose: https://docs.docker.com/compose/
- PostgreSQL: https://www.postgresql.org/docs/
- FastAPI: https://fastapi.tiangolo.com/
- Next.js: https://nextjs.org/docs

## 🐛 Getting Help

1. **Check logs:** `docker-compose logs -f`
2. **Review .env:** Verify all variables are set
3. **Run health checks:** `docker ps` (all containers should be "Up")
4. **Check connectivity:** `docker network inspect`
5. **Review documentation:** See DOCKER.md for detailed info

## 📞 Support

For issues:
- Check error messages in logs
- Verify Docker installation
- Ensure ports are available
- Check disk space (at least 2GB free)
- Review configuration files

---

**Last Updated:** 2026-03-01
**Version:** 1.0.0
**Status:** ✅ Production Ready

Happy Dockerizing! 🐳✨
