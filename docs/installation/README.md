# Installation Guide

This guide covers various installation methods for SupportOps Automator, from quick Docker deployment to production-ready setups.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start with Docker Compose](#quick-start-with-docker-compose)
- [Coolify Deployment](#coolify-deployment)
- [Manual Installation](#manual-installation)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Environment Configuration](#environment-configuration)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

**Minimum Requirements:**
- CPU: 2 cores
- RAM: 4GB
- Storage: 20GB
- OS: Linux (Ubuntu 20.04+), macOS, Windows with WSL2

**Recommended for Production:**
- CPU: 4+ cores
- RAM: 8GB+
- Storage: 100GB+ SSD
- OS: Linux (Ubuntu 22.04 LTS)

### Software Dependencies

**Required:**
- Docker 24.0+ and Docker Compose 2.0+
- Git

**For Development:**
- Python 3.11+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+

## Quick Start with Docker Compose

The fastest way to get SupportOps Automator running is with Docker Compose.

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/supportops-automator.git
cd supportops-automator
```

### 2. Configure Environment

```bash
# Copy the environment template
cp .env.example .env

# Generate secure keys
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"
python3 -c "import secrets; print('ENCRYPTION_KEY=' + secrets.token_urlsafe(32))"

# Edit the .env file with your values
nano .env
```

**Essential Environment Variables:**

```env
# Database Configuration
DATABASE_PASSWORD=your_secure_database_password
DATABASE_URL=postgresql://supportops:your_secure_database_password@postgres:5432/supportops

# Security Keys (use the generated values above)
SECRET_KEY=your_generated_secret_key
JWT_SECRET_KEY=your_generated_jwt_secret
ENCRYPTION_KEY=your_generated_encryption_key

# Admin User Configuration
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@yourcompany.com
ADMIN_PASSWORD=your_secure_admin_password
ADMIN_FULL_NAME=System Administrator

# Application Configuration
ENVIRONMENT=production
CORS_ORIGINS=https://yourdomain.com
```

### 3. Deploy the Stack

```bash
# Start all services in detached mode
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 4. Verify Installation

1. **Check Service Health:**
   ```bash
   # Backend health check
   curl http://localhost:8000/health
   
   # Frontend health check
   curl http://localhost:3000/health
   ```

2. **Access the Application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

3. **Login with Admin Credentials:**
   - Username: `admin` (or your configured value)
   - Password: Your configured admin password

### 5. Post-Installation Setup

1. **Configure Integrations:**
   - Navigate to Settings → Integrations
   - Add your third-party service credentials
   - Test connections

2. **Create Additional Users:**
   - Go to User Management
   - Add team members with appropriate roles

3. **Set Up Automation Rules:**
   - Visit Rules section
   - Create your first automation workflow

## Coolify Deployment

Coolify provides one-click deployment for SupportOps Automator.

### 1. Prepare Your Repository

Ensure your repository contains:
- `docker-compose.yml`
- `.env.example`
- All application files

### 2. Coolify Configuration

1. **Create New Project** in Coolify
2. **Connect Repository** (GitHub/GitLab)
3. **Select Docker Compose** deployment type
4. **Configure Environment Variables:**

```env
# Copy from .env.example and customize
DATABASE_PASSWORD=generate_secure_password
SECRET_KEY=generate_32_char_key
JWT_SECRET_KEY=generate_32_char_key
ENCRYPTION_KEY=generate_32_char_key
ADMIN_PASSWORD=generate_secure_password
```

### 3. Database Setup

1. **Create PostgreSQL Database** in Coolify
2. **Update Environment Variables:**
   ```env
   DATABASE_URL=postgresql://username:password@db_host:5432/database_name
   DATABASE_HOST=your_db_host
   DATABASE_PASSWORD=your_db_password
   ```

### 4. Deploy

1. **Click Deploy** in Coolify
2. **Monitor Deployment** logs
3. **Verify Services** are running
4. **Access Application** via provided URL

### 5. SSL Configuration

Coolify automatically handles SSL certificates:
- Enable "Generate SSL Certificate"
- Configure custom domain if needed
- Verify HTTPS access

## Manual Installation

For custom deployments or development environments.

### 1. System Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3.11 python3.11-venv python3-pip nodejs npm postgresql-15 redis-server nginx git curl

# Install Docker (optional, for containerized services)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

### 2. Database Setup

```bash
# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE supportops;
CREATE USER supportops WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE supportops TO supportops;
ALTER USER supportops CREATEDB;
\q
EOF
```

### 3. Redis Setup

```bash
# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Verify Redis is running
redis-cli ping
```

### 4. Backend Installation

```bash
# Clone repository
git clone https://github.com/your-org/supportops-automator.git
cd supportops-automator/backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database and security settings

# Run database migrations
alembic upgrade head

# Create admin user
python scripts/create_admin.py

# Start backend server
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 5. Frontend Installation

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install

# Build for production
npm run build

# Serve with nginx or use development server
npm run preview
```

### 6. Nginx Configuration

```nginx
# /etc/nginx/sites-available/supportops-automator
server {
    listen 80;
    server_name yourdomain.com;

    # Frontend
    location / {
        root /path/to/supportops-automator/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/supportops-automator /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Kubernetes Deployment

For scalable production deployments.

### 1. Prerequisites

- Kubernetes cluster (1.25+)
- kubectl configured
- Helm 3.0+

### 2. Namespace Creation

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: supportops-automator
```

```bash
kubectl apply -f namespace.yaml
```

### 3. Database Deployment

```yaml
# postgres-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: supportops-automator
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        env:
        - name: POSTGRES_DB
          value: "supportops"
        - name: POSTGRES_USER
          value: "supportops"
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc
```

### 4. Application Deployment

```yaml
# backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: supportops-automator
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: supportops-automator/backend:latest
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: database-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: secret-key
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 5. Service and Ingress

```yaml
# services.yaml
apiVersion: v1
kind: Service
metadata:
  name: backend-service
  namespace: supportops-automator
spec:
  selector:
    app: backend
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP

---
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
  namespace: supportops-automator
spec:
  selector:
    app: frontend
  ports:
  - port: 3000
    targetPort: 3000
  type: ClusterIP
```

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: supportops-ingress
  namespace: supportops-automator
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - yourdomain.com
    secretName: supportops-tls
  rules:
  - host: yourdomain.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: backend-service
            port:
              number: 8000
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 3000
```

## Environment Configuration

### Security Configuration

```env
# Generate secure random keys
SECRET_KEY=your_32_character_secret_key_here
JWT_SECRET_KEY=your_32_character_jwt_secret_here
ENCRYPTION_KEY=your_32_character_encryption_key_here

# Password policy
PASSWORD_MIN_LENGTH=8
REQUIRE_SPECIAL_CHARS=true
SESSION_TIMEOUT_MINUTES=30

# Rate limiting
RATE_LIMIT_ENABLED=true
MAX_REQUESTS_PER_MINUTE=100
```

### Database Configuration

```env
# PostgreSQL connection
DATABASE_URL=postgresql://user:password@host:port/database
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=supportops
DATABASE_USER=supportops
DATABASE_PASSWORD=your_secure_password

# Connection pooling
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
```

### Integration Configuration

```env
# Slack
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_SIGNING_SECRET=your-slack-signing-secret

# Trello
TRELLO_API_KEY=your-trello-api-key
TRELLO_API_SECRET=your-trello-api-secret

# Notion
NOTION_API_KEY=your-notion-api-key

# Google Sheets
GOOGLE_SHEETS_CREDENTIALS_JSON=/path/to/credentials.json
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Failed

**Symptoms:**
- Backend fails to start
- "Connection refused" errors

**Solutions:**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Verify database exists
sudo -u postgres psql -l | grep supportops

# Test connection
psql -h localhost -U supportops -d supportops
```

#### 2. Frontend Build Errors

**Symptoms:**
- npm build fails
- Missing dependencies

**Solutions:**
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check Node.js version
node --version  # Should be 20+
```

#### 3. Docker Compose Issues

**Symptoms:**
- Services fail to start
- Port conflicts

**Solutions:**
```bash
# Check port usage
sudo netstat -tlnp | grep :8000

# View detailed logs
docker-compose logs --tail=50 backend

# Restart services
docker-compose down
docker-compose up -d
```

#### 4. Permission Errors

**Symptoms:**
- File access denied
- Database permission errors

**Solutions:**
```bash
# Fix file permissions
sudo chown -R $USER:$USER /path/to/supportops-automator

# Database permissions
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE supportops TO supportops;"
```

### Performance Issues

#### 1. Slow API Responses

**Diagnostics:**
```bash
# Check database performance
sudo -u postgres psql supportops -c "SELECT * FROM pg_stat_activity;"

# Monitor system resources
htop
iostat -x 1
```

**Solutions:**
- Increase database connection pool size
- Add database indexes
- Enable Redis caching
- Scale backend replicas

#### 2. High Memory Usage

**Solutions:**
```bash
# Limit Docker memory usage
echo 'COMPOSE_DOCKER_CLI_BUILD=1' >> .env
echo 'DOCKER_BUILDKIT=1' >> .env

# Optimize PostgreSQL settings
# Edit postgresql.conf:
shared_buffers = 256MB
effective_cache_size = 1GB
```

### Getting Help

If you encounter issues not covered here:

1. **Check Logs:**
   ```bash
   # Docker Compose
   docker-compose logs -f

   # Manual installation
   tail -f /var/log/supportops-automator/app.log
   ```

2. **Enable Debug Mode:**
   ```env
   DEBUG=true
   LOG_LEVEL=DEBUG
   ```

3. **Community Support:**
   - GitHub Issues: Report bugs and get help
   - Discord: Real-time community support
   - Documentation: Check our comprehensive docs

4. **Professional Support:**
   - Email: support@supportops-automator.com
   - Enterprise support plans available

---

**Next Steps:**
- [Configuration Guide](../configuration/README.md) - Detailed configuration options
- [User Guide](../user-guide/README.md) - How to use the platform
- [Security Guide](../security/README.md) - Security best practices

