# 🔧 Communication Fixes Applied to Production Setup

## Overview

Based on the modifications made to the development Docker setup, the following communication fixes have been applied to the production setup to ensure seamless service-to-service communication.

## 🐳 **Docker Networking Fixes**

### **1. Custom Docker Network**
**Issue:** Default Docker networking can cause service discovery issues
**Fix Applied:**
```yaml
# Development setup uses:
networks:
  default:
    name: docuai_network

# Production setup uses:
networks:
  backend_network:
    driver: bridge
    internal: true
  frontend_network:
    driver: bridge
    name: docuai_prod_network
```

### **2. Service Name Communication**
**Issue:** Services need to communicate using Docker service names
**Fix Applied:**
- Database: `postgres:5432` (not localhost:5432)
- Redis: `redis:6379` (not localhost:6379) 
- Backend: `backend:8000` (not localhost:8000)

## 📡 **CORS Configuration Fixes**

### **3. Environment-Aware CORS Origins**
**Issue:** Production needs different allowed origins than development
**Fix Applied in `backend/app/main.py`:**
```python
# Configure CORS origins based on environment
cors_origins = [
    "http://localhost:3000",  # Docker frontend (dev)
    "http://localhost:5173",  # Vite dev server
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173"
]

# Add production origins
if settings.ENVIRONMENT == "production":
    cors_origins.extend([
        "http://localhost:8080",  # Local production test
        "https://localhost:8080", # Local production test with SSL
        # Add actual production domains for AWS deployment
    ])
```

### **4. Nginx CORS Preflight Handling**
**Issue:** Browser preflight OPTIONS requests need proper handling
**Fix Applied in nginx configurations:**
```nginx
# Handle CORS preflight requests
if ($request_method = 'OPTIONS') {
    add_header 'Access-Control-Allow-Origin' '*';
    add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS';
    add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type';
    add_header 'Access-Control-Max-Age' 1728000;
    add_header 'Content-Type' 'text/plain; charset=utf-8';
    add_header 'Content-Length' 0;
    return 204;
}
```

## 🌐 **Nginx Proxy Fixes**

### **5. Frontend API Proxying**
**Issue:** Frontend needs to proxy API requests to backend
**Fix Applied:**
- Development: Frontend nginx proxies `/api/v1/` to `http://backend:8000`
- Production: Main nginx handles all routing, but same proxy pattern applied

### **6. Proper Proxy Headers**
**Issue:** Backend needs to know real client IP and protocol
**Fix Applied:**
```nginx
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header Connection "";
proxy_http_version 1.1;
```

## 📁 **Volume and Path Fixes**

### **7. Consistent Volume Mapping**
**Issue:** File paths need to be consistent across containers
**Fix Applied:**
```yaml
volumes:
  - uploads_data:/app/uploads
  - vector_data:/app/langchain_vector_db
  - openai_vectors:/app/openai_direct_vectors
```

### **8. Upload Directory Configuration**
**Issue:** Upload directory must be accessible to all services
**Fix Applied:**
```yaml
environment:
  - UPLOAD_DIR=/app/uploads  # Same path in all containers
```

## 🔒 **Security and Communication**

### **9. Redis Password Protection**
**Issue:** Production Redis needs password protection
**Fix Applied:**
```yaml
# Redis service
redis:
  command: redis-server --requirepass ${REDIS_PASSWORD}

# Client connections
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
```

### **10. Network Isolation**
**Issue:** Production needs network segmentation
**Fix Applied:**
- Backend network: Internal only (database, redis, backend, celery)
- Frontend network: External access (nginx, frontend, backend)

## 🧪 **Testing Communication**

### **Validation Commands:**
```bash
# Test service-to-service communication
docker-compose -f docker-compose.local-prod.yml exec frontend curl http://backend:8000/api/v1/health

# Test database connection
docker-compose -f docker-compose.local-prod.yml exec backend python -c "from app.database import engine; print(engine.connect())"

# Test Redis connection
docker-compose -f docker-compose.local-prod.yml exec celery python -c "import redis; r=redis.from_url('redis://:password@redis:6379/0'); print(r.ping())"

# Test nginx routing
curl http://localhost:8080/api/v1/health
curl http://localhost:8080/health
```

## 📋 **Checklist for New Environments**

When setting up a new environment, ensure:
- [ ] Custom Docker network configured
- [ ] Service names used for internal communication
- [ ] CORS origins updated for environment
- [ ] Nginx proxy headers configured
- [ ] Volume paths consistent
- [ ] Environment variables set correctly
- [ ] Network isolation implemented
- [ ] Health checks working

## 🚨 **Common Issues and Solutions**

### **Issue: "Connection refused" errors**
**Cause:** Using localhost instead of service names
**Solution:** Use Docker service names (backend, postgres, redis)

### **Issue: CORS errors in browser**
**Cause:** Missing allowed origins or preflight handling
**Solution:** Update CORS origins and ensure nginx handles OPTIONS requests

### **Issue: File upload failures**
**Cause:** Upload directory not mounted or accessible
**Solution:** Verify volume mounts and UPLOAD_DIR environment variable

### **Issue: Database connection timeouts**
**Cause:** Incorrect connection string or network issues
**Solution:** Use service name in DATABASE_URL and check network configuration

---

**💡 Note:** These fixes have been tested in the development environment and applied to the production setup. The local production test environment (`docker-compose.local-prod.yml`) includes all these fixes for validation before AWS deployment. 