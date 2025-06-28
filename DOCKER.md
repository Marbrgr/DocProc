# 🐳 Docker Deployment Guide

## Overview

DocuMind AI uses Docker for containerized deployment with separate configurations for development and production environments.

## 📋 Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Docker Compose v2.0+
- At least 4GB RAM available for containers
- 10GB free disk space

## 🚀 Quick Start

### Development Environment

1. **Clone and navigate to project:**
   ```bash
   cd doc-proc
   ```

2. **Set up environment:**
   ```bash
   copy env.example .env
   # Edit .env with your API keys and settings
   ```

3. **Start development environment:**
   ```bash
   # Windows
   docker-dev.bat
   
   # Linux/Mac
   docker-compose up --build -d
   ```

4. **Access services:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/api/v1/health
   - Flower (Celery): http://localhost:5555
   - Database: localhost:5432

### Production Environment

1. **Set up production environment:**
   ```bash
   copy env.example .env
   # Edit .env with SECURE production values
   ```

2. **Generate SSL certificates:**
   ```bash
   mkdir -p nginx/ssl
   # Add your SSL certificate files:
   # nginx/ssl/cert.pem
   # nginx/ssl/key.pem
   ```

3. **Start production environment:**
   ```bash
   # Windows
   docker-prod.bat
   
   # Linux/Mac
   docker-compose -f docker-compose.prod.yml up --build -d
   ```

## 🏗️ Architecture

### Services

| Service | Description | Port | Dependencies |
|---------|-------------|------|--------------|
| **postgres** | PostgreSQL database | 5432 | - |
| **redis** | Redis cache/message broker | 6379 | - |
| **backend** | FastAPI application | 8000 | postgres, redis |
| **celery** | Background task worker | - | postgres, redis |
| **frontend** | React application | 80/3000 | backend |
| **nginx** | Reverse proxy (prod only) | 80/443 | frontend, backend |
| **flower** | Celery monitoring (dev only) | 5555 | redis |

### Volumes

- `postgres_data`: Database persistence
- `redis_data`: Redis persistence
- `uploads_data`: Document uploads
- `vector_data`: LangChain vector database
- `openai_vectors`: OpenAI vector database

## 🔧 Configuration

### Environment Variables

Required variables in `.env`:

```env
# Database
POSTGRES_DB=docuai
POSTGRES_USER=docuai_user
POSTGRES_PASSWORD=secure_password_here

# Redis
REDIS_PASSWORD=redis_password_here

# API Keys
OPENAI_API_KEY=your_openai_key_here

# Security
JWT_SECRET_KEY=your_32_char_jwt_secret_here

# Application
ENVIRONMENT=development|production
```

### Development vs Production

| Feature | Development | Production |
|---------|-------------|------------|
| **SSL** | HTTP only | HTTPS required |
| **Database** | Exposed port | Internal network |
| **Redis** | No password | Password protected |
| **Celery** | 2 workers | 4 workers |
| **Frontend** | Dev server | Nginx static |
| **Security** | Relaxed | Hardened headers |
| **Logging** | Debug level | Info level |

## 📊 Monitoring

### Health Checks

All services include health checks:

```bash
# Check all services
docker-compose ps

# Check specific service
docker-compose exec backend curl http://localhost:8000/api/v1/health
```

### Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 -f
```

### Celery Monitoring

Development includes Flower for Celery monitoring:
- URL: http://localhost:5555
- Monitor tasks, workers, and queues

## 🔄 Common Operations

### Database Operations

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Access database
docker-compose exec postgres psql -U docuai_user -d docuai

# Backup database
docker-compose exec postgres pg_dump -U docuai_user docuai > backup.sql

# Restore database
docker-compose exec -T postgres psql -U docuai_user docuai < backup.sql
```

### Application Updates

```bash
# Rebuild specific service
docker-compose build backend
docker-compose up -d backend

# Update all services
docker-compose pull
docker-compose up --build -d
```

### Scaling

```bash
# Scale Celery workers
docker-compose up -d --scale celery=3

# Check scaled services
docker-compose ps
```

## 🐛 Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Find process using port
netstat -ano | findstr :8000
# Kill process or change port in docker-compose.yml
```

**Out of disk space:**
```bash
# Clean up unused containers/images
docker system prune -a

# Remove specific volumes (⚠️ DATA LOSS)
docker-compose down -v
```

**Database connection issues:**
```bash
# Check database logs
docker-compose logs postgres

# Reset database
docker-compose down
docker volume rm doc-proc_postgres_data
docker-compose up -d
```

**SSL certificate issues (production):**
```bash
# Generate self-signed certificate for testing
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem -out nginx/ssl/cert.pem
```

### Performance Tuning

**Memory issues:**
- Increase Docker Desktop memory limit
- Reduce Celery concurrency
- Add swap file on Linux

**Slow builds:**
- Use Docker layer caching
- Multi-stage builds already implemented
- Consider using Docker BuildKit

## 🔒 Security

### Production Security Checklist

- [ ] Strong passwords in `.env`
- [ ] Valid SSL certificates
- [ ] Firewall configured
- [ ] Regular security updates
- [ ] Log monitoring setup
- [ ] Backup strategy implemented
- [ ] Rate limiting configured
- [ ] CORS properly configured

### Network Security

Production uses isolated networks:
- `backend_network`: Database and internal services
- `frontend_network`: Public-facing services

## 📈 Scaling

### Horizontal Scaling

```bash
# Scale backend instances
docker-compose up -d --scale backend=3

# Scale Celery workers
docker-compose up -d --scale celery=5
```

### Load Balancing

Nginx configuration includes upstream load balancing for multiple backend instances.

## 🚀 Deployment Platforms

### Railway
```bash
# Install Railway CLI
npm install -g @railway/cli

# Deploy
railway login
railway init
railway up
```

### DigitalOcean App Platform
- Use docker-compose.prod.yml
- Configure environment variables
- Set up managed database

### AWS ECS/Fargate
- Convert to ECS task definitions
- Use RDS for database
- Use ElastiCache for Redis

## 📝 Best Practices

1. **Always use volumes for persistent data**
2. **Keep secrets in environment variables**
3. **Use health checks for all services**
4. **Implement proper logging**
5. **Regular backups of data volumes**
6. **Monitor resource usage**
7. **Keep images updated**
8. **Use specific image tags in production**

## 🆘 Support

For issues:
1. Check logs: `docker-compose logs -f`
2. Verify environment variables
3. Check Docker resources (memory/disk)
4. Review this documentation
5. Check GitHub issues 