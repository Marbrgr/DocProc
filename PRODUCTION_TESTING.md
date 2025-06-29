# 🧪 Production Testing Guide

## Overview

Before deploying to AWS, it's crucial to test your production Docker setup locally to identify and resolve potential issues. This guide provides a structured approach to validate your production configuration.

## 🎯 Why Test Production Setup Locally?

### **Critical Issues to Catch Early:**
- **Network Communication:** Service-to-service communication in production networks
- **Environment Variables:** Production configuration vs development
- **Resource Constraints:** Production memory/CPU limits
- **Security Settings:** Authentication, CORS, rate limiting
- **SSL/TLS Issues:** Certificate problems (when testing with real certs)
- **Performance:** Production optimization settings

### **Cost Savings:**
- Avoid expensive AWS debugging cycles
- Prevent production downtime
- Reduce deployment rollbacks

## 🚀 Local Production Test Setup

### **Prerequisites**
1. **Environment File:** Create production `.env` with secure values:
   ```bash
   # Copy and modify
   cp env.example .env
   ```

2. **Production Values Required:**
   ```env
   # Database
   POSTGRES_DB=docuai_prod
   POSTGRES_USER=secure_user
   POSTGRES_PASSWORD=very_secure_password_32chars

   # Redis
   REDIS_PASSWORD=secure_redis_password_here

   # API Keys
   OPENAI_API_KEY=your_real_openai_key

   # Security
   JWT_SECRET_KEY=super_secure_jwt_key_minimum_32_characters

   # Environment
   ENVIRONMENT=production
   ```

### **Start Local Production Test**
```bash
# Run the local production test
docker-local-prod.bat

# Or manually:
docker-compose -f docker-compose.local-prod.yml up --build -d
```

**Access Points:**
- **Application:** http://localhost:8080
- **API:** http://localhost:8080/api/v1/
- **Health:** http://localhost:8080/health

## ✅ Testing Checklist

### **1. Infrastructure Tests**
- [ ] All containers start successfully
- [ ] Health checks pass for all services
- [ ] Networks are properly isolated
- [ ] Volume persistence works

```bash
# Check container status
docker-compose -f docker-compose.local-prod.yml ps

# Check health
curl http://localhost:8080/health
curl http://localhost:8080/api/v1/health
```

### **2. Authentication & Security**
- [ ] User registration works
- [ ] User login works
- [ ] JWT tokens are generated and validated
- [ ] Protected routes require authentication
- [ ] CORS policies work correctly

### **3. Document Processing**
- [ ] File upload works through reverse proxy
- [ ] Background processing via Celery works
- [ ] OCR text extraction works
- [ ] AI document analysis works
- [ ] Document storage persists

### **4. Database & Redis**
- [ ] PostgreSQL connection works
- [ ] Data persists after container restart
- [ ] Redis connection with password works
- [ ] Celery tasks queue/process correctly

### **5. Performance Tests**
- [ ] Multiple concurrent uploads
- [ ] Rate limiting works (test with rapid API calls)
- [ ] Large file uploads (test nginx upload size limits)
- [ ] Memory usage under load

### **6. Network & Proxy Tests**
- [ ] Frontend serves through nginx
- [ ] API calls route through nginx
- [ ] Static file serving works
- [ ] Error pages display correctly

## 🔍 Debugging Commands

### **Container Logs**
```bash
# All services
docker-compose -f docker-compose.local-prod.yml logs -f

# Specific service
docker-compose -f docker-compose.local-prod.yml logs -f backend
docker-compose -f docker-compose.local-prod.yml logs -f nginx
docker-compose -f docker-compose.local-prod.yml logs -f celery
```

### **Service Health**
```bash
# Check backend health
docker-compose -f docker-compose.local-prod.yml exec backend curl http://localhost:8000/api/v1/health

# Check database connection
docker-compose -f docker-compose.local-prod.yml exec postgres pg_isready -U $POSTGRES_USER

# Check Redis connection
docker-compose -f docker-compose.local-prod.yml exec redis redis-cli --pass $REDIS_PASSWORD ping
```

### **Resource Usage**
```bash
# Container resource usage
docker stats

# Detailed container info
docker-compose -f docker-compose.local-prod.yml exec backend top
```

## 🚨 Common Issues & Solutions

### **Issue: Containers won't start**
**Solution:** Check environment variables
```bash
# Verify .env file
cat .env

# Check container logs
docker-compose -f docker-compose.local-prod.yml logs
```

### **Issue: Frontend can't reach backend**
**Solution:** Check nginx configuration and networks
```bash
# Test nginx config
docker-compose -f docker-compose.local-prod.yml exec nginx nginx -t

# Check network connectivity
docker-compose -f docker-compose.local-prod.yml exec frontend curl http://backend:8000/api/v1/health
```

### **Issue: Database connection fails**
**Solution:** Verify database credentials and health
```bash
# Test database connection
docker-compose -f docker-compose.local-prod.yml exec backend python -c "from app.database import engine; print(engine.connect())"
```

### **Issue: Celery tasks not processing**
**Solution:** Check Redis connection and worker status
```bash
# Check Celery worker status
docker-compose -f docker-compose.local-prod.yml exec celery celery -A app.celery_config inspect active

# Check Redis connection
docker-compose -f docker-compose.local-prod.yml exec celery python -c "import redis; r=redis.from_url('redis://:password@redis:6379/0'); print(r.ping())"
```

## 📊 Production Readiness Criteria

### **✅ Ready for AWS Deployment**
- [ ] All tests pass consistently
- [ ] No memory leaks after extended testing
- [ ] Error handling works properly
- [ ] Logs are appropriate for production
- [ ] Performance meets requirements
- [ ] Security settings validated

### **❌ Not Ready - Common Red Flags**
- [ ] Intermittent container failures
- [ ] Memory usage constantly increasing
- [ ] Database connection timeouts
- [ ] Frontend/backend communication issues
- [ ] Missing environment variables
- [ ] Celery workers crashing

## 🔄 Cleanup

### **Stop and Remove**
```bash
# Stop containers
docker-compose -f docker-compose.local-prod.yml down

# Remove volumes (careful - destroys data!)
docker-compose -f docker-compose.local-prod.yml down -v

# Remove images
docker-compose -f docker-compose.local-prod.yml down --rmi all
```

## 🎯 Next Steps

Once local production testing passes:

1. **Document Issues Found:** Keep track of what was fixed
2. **Update Production Config:** Apply lessons learned to AWS setup
3. **SSL Certificate Preparation:** Get real certificates for AWS
4. **AWS Infrastructure Setup:** Apply tested configuration to cloud
5. **Deployment Pipeline:** Set up CI/CD with tested Docker configs

## 📝 Test Results Template

```markdown
## Local Production Test Results

**Date:** [DATE]
**Tester:** [NAME]
**Docker Version:** [VERSION]

### Infrastructure ✅/❌
- [ ] All containers started
- [ ] Health checks passed
- [ ] Networks properly isolated

### Functionality ✅/❌
- [ ] Authentication works
- [ ] Document upload works
- [ ] Processing completes
- [ ] Data persists

### Performance ✅/❌
- [ ] Response times acceptable
- [ ] No memory leaks observed
- [ ] Rate limiting works

### Issues Found:
1. [Issue description and resolution]
2. [Issue description and resolution]

### Ready for AWS Deployment: YES/NO
**Reason if NO:** [Explanation]
```

---

**💡 Pro Tip:** Run this test suite multiple times and at different times of day to catch intermittent issues that might only appear under certain conditions. 