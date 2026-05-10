# RTI-Lens Deployment Guide

Complete guide for deploying RTI-Lens in development, staging, and production environments.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Development Setup](#development-setup)
- [Database Setup](#database-setup)
- [Environment Configuration](#environment-configuration)
- [Running the Application](#running-the-application)
- [Production Deployment](#production-deployment)
- [Docker Deployment](#docker-deployment)
- [Monitoring & Observability](#monitoring--observability)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

**Minimum:**
- CPU: 4 cores
- RAM: 8GB
- Storage: 20GB SSD
- OS: Ubuntu 20.04+, macOS 12+, or Windows 11 with WSL2

**Recommended:**
- CPU: 8 cores
- RAM: 16GB
- Storage: 50GB SSD
- OS: Ubuntu 22.04 LTS

### Software Dependencies

**Required:**
- Python 3.10 or higher
- Node.js 18 or higher
- PostgreSQL 14 or higher
- MongoDB 6 or higher

**Optional:**
- Docker & Docker Compose (for containerized deployment)
- Nginx (for production reverse proxy)
- Redis (for caching, future enhancement)

---

## Development Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd IDP
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import fastapi; import sqlalchemy; print('Backend dependencies OK')"
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Verify installation
npm list react vite
```

### 4. PageIndex Library Setup

```bash
cd pageindex_lib

# Install in development mode
pip install -e .

# Verify installation
python -c "import pageindex_lib; print('PageIndex library OK')"
```

---

## Database Setup

### PostgreSQL Setup

**Option 1: Local Installation**

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# macOS
brew install postgresql@14
brew services start postgresql@14

# Start PostgreSQL
sudo systemctl start postgresql  # Linux
brew services start postgresql@14  # macOS
```

**Option 2: Docker**

```bash
docker run -d \
  --name rti-postgres \
  -e POSTGRES_USER=rti_user \
  -e POSTGRES_PASSWORD=rti_password \
  -e POSTGRES_DB=rti_lens \
  -p 5432:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:14
```

**Create Database:**

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database and user
CREATE DATABASE rti_lens;
CREATE USER rti_user WITH PASSWORD 'rti_password';
GRANT ALL PRIVILEGES ON DATABASE rti_lens TO rti_user;
\q
```

**Run Migrations:**

```bash
cd backend

# Initialize database schema
python -c "from database import Base, engine; Base.metadata.create_all(bind=engine)"

# Verify tables
psql -U rti_user -d rti_lens -c "\dt"
```

### MongoDB Setup

**Option 1: MongoDB Atlas (Recommended)**

1. Create account at [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
2. Create free M0 cluster
3. Enable Vector Search on cluster
4. Get connection string
5. Add to `.env` file

**Option 2: Local Installation**

```bash
# Ubuntu/Debian
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
sudo apt update
sudo apt install -y mongodb-org
sudo systemctl start mongod

# macOS
brew tap mongodb/brew
brew install mongodb-community@6.0
brew services start mongodb-community@6.0
```

**Option 3: Docker**

```bash
docker run -d \
  --name rti-mongodb \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=admin_password \
  -p 27017:27017 \
  -v mongodb_data:/data/db \
  mongo:6.0
```

**Create Vector Search Index:**

```javascript
// Connect to MongoDB
mongosh "mongodb://localhost:27017"

use rti_lens

// Create vector search index
db.embeddings.createIndex(
  {
    "embedding": "vector"
  },
  {
    name: "vector_index",
    vectorSearchOptions: {
      type: "knnVector",
      numDimensions: 384,  // all-MiniLM-L6-v2 dimension
      similarity: "cosine"
    }
  }
)
```

---

## Environment Configuration

### Backend Environment Variables

Create `backend/.env`:

```bash
# Database
DATABASE_URL=postgresql://rti_user:rti_password@localhost:5432/rti_lens
MONGODB_URI=mongodb://localhost:27017/rti_lens

# Groq API
GROQ_API_KEY=your_groq_api_key_here

# Solana (optional)
SOLANA_PRIVATE_KEY=your_base58_private_key_here
SOLANA_NETWORK=devnet  # or mainnet

# ElevenLabs (optional)
ELEVENLABS_API_KEY=your_elevenlabs_key_here

# Backboard.io (optional)
BACKBOARD_API_KEY=your_backboard_key_here

# Application
DEBUG=true
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Rate Limiting
RATE_LIMIT_STANDARD=100  # requests per minute
RATE_LIMIT_LLM=10
RATE_LIMIT_BLOCKCHAIN=5
```

### Frontend Environment Variables

Create `frontend/.env`:

```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_SOLANA_NETWORK=devnet
VITE_ENABLE_BLOCKCHAIN=true
VITE_ENABLE_VOICE=true
```

### API Keys Setup

**Groq API (Required):**
1. Sign up at [console.groq.com](https://console.groq.com)
2. Create API key
3. Add to `backend/.env`

**Solana (Optional):**
```bash
# Generate new keypair
solana-keygen new --outfile ~/.config/solana/devnet.json

# Get private key in base58
solana-keygen pubkey ~/.config/solana/devnet.json
```

**ElevenLabs (Optional):**
1. Sign up at [elevenlabs.io](https://elevenlabs.io)
2. Get API key from dashboard
3. Add to `backend/.env`

---

## Running the Application

### Development Mode

**Terminal 1: Backend**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2: Frontend**
```bash
cd frontend
npm run dev
```

**Access Application:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Data Ingestion

**Ingest CIC Orders:**

```bash
cd backend

# Place TXT files in data/cic_orders_txt/
# Run ingestion script
python scripts/ingest_orders.py

# Build BM25 index
python scripts/build_bm25_index.py

# Generate PageIndex trees
python scripts/generate_pageindex.py

# Build knowledge graph
python scripts/build_knowledge_graph.py
```

**Verify Data:**

```bash
# Check database
psql -U rti_user -d rti_lens -c "SELECT COUNT(*) FROM cases;"
psql -U rti_user -d rti_lens -c "SELECT COUNT(*) FROM paragraphs;"

# Check generated files
ls -lh data/*.pkl data/*.json
```

---

## Production Deployment

### Architecture Overview

```mermaid
graph TB
    subgraph "Load Balancer"
        LB[Nginx/Cloudflare]
    end

    subgraph "Application Servers"
        FE1[Frontend Server 1]
        FE2[Frontend Server 2]
        BE1[Backend Server 1]
        BE2[Backend Server 2]
    end

    subgraph "Data Layer"
        PG[(PostgreSQL<br/>Primary)]
        PGR[(PostgreSQL<br/>Replica)]
        MDB[(MongoDB Atlas)]
    end

    subgraph "External Services"
        GROQ[Groq API]
        SOL[Solana Mainnet]
    end

    LB --> FE1
    LB --> FE2
    FE1 --> BE1
    FE2 --> BE2
    BE1 --> PG
    BE2 --> PG
    PG --> PGR
    BE1 --> MDB
    BE2 --> MDB
    BE1 --> GROQ
    BE2 --> GROQ
    BE1 --> SOL
    BE2 --> SOL

    style LB fill:#0ea5e9,stroke:#0284c7,color:#fff
    style PG fill:#336791,stroke:#2d5a7b,color:#fff
    style MDB fill:#47a248,stroke:#3d8b40,color:#fff
```

### Server Setup

**1. Provision Servers**

Recommended: 2 application servers + 1 database server

```bash
# Application Server (Ubuntu 22.04)
- 4 vCPUs
- 8GB RAM
- 50GB SSD
- Public IP

# Database Server
- 4 vCPUs
- 16GB RAM
- 100GB SSD
- Private network only
```

**2. Install Dependencies**

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python
sudo apt install python3.10 python3.10-venv python3-pip -y

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y

# Install Nginx
sudo apt install nginx -y

# Install PostgreSQL client
sudo apt install postgresql-client -y
```

**3. Deploy Backend**

```bash
# Create application user
sudo useradd -m -s /bin/bash rti-app
sudo su - rti-app

# Clone and setup
git clone <repository-url> /home/rti-app/rti-lens
cd /home/rti-app/rti-lens/backend

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy production environment
cp .env.example .env
nano .env  # Edit with production values

# Test backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

**4. Deploy Frontend**

```bash
cd /home/rti-app/rti-lens/frontend

# Install dependencies
npm ci --production

# Build for production
npm run build

# Output is in dist/
ls -la dist/
```

**5. Configure Systemd Services**

**Backend Service:** `/etc/systemd/system/rti-backend.service`

```ini
[Unit]
Description=RTI-Lens Backend API
After=network.target postgresql.service

[Service]
Type=simple
User=rti-app
WorkingDirectory=/home/rti-app/rti-lens/backend
Environment="PATH=/home/rti-app/rti-lens/backend/venv/bin"
ExecStart=/home/rti-app/rti-lens/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable rti-backend
sudo systemctl start rti-backend
sudo systemctl status rti-backend
```

**6. Configure Nginx**

**Nginx Config:** `/etc/nginx/sites-available/rti-lens`

```nginx
# Frontend
server {
    listen 80;
    server_name your-domain.com;

    root /home/rti-app/rti-lens/frontend/dist;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for LLM endpoints
        proxy_read_timeout 60s;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req zone=api_limit burst=20 nodelay;
}
```

**Enable site:**

```bash
sudo ln -s /etc/nginx/sites-available/rti-lens /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

**7. SSL Certificate (Let's Encrypt)**

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
sudo systemctl reload nginx
```

---

## Docker Deployment

### Docker Compose Setup

**`docker-compose.yml`:**

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_USER: rti_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: rti_lens
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U rti_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  mongodb:
    image: mongo:6.0
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD}
    volumes:
      - mongodb_data:/data/db
    ports:
      - "27017:27017"

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://rti_user:${POSTGRES_PASSWORD}@postgres:5432/rti_lens
      MONGODB_URI: mongodb://admin:${MONGO_PASSWORD}@mongodb:27017/rti_lens?authSource=admin
      GROQ_API_KEY: ${GROQ_API_KEY}
      SOLANA_PRIVATE_KEY: ${SOLANA_PRIVATE_KEY}
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      mongodb:
        condition: service_started
    volumes:
      - ./backend:/app
      - ./data:/app/data
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend
    environment:
      VITE_API_BASE_URL: http://backend:8000

volumes:
  postgres_data:
  mongodb_data:
```

**Backend Dockerfile:**

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Frontend Dockerfile:**

```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Build application
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

**Deploy with Docker Compose:**

```bash
# Create .env file
cp .env.example .env
nano .env  # Add your API keys

# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## Monitoring & Observability

### Application Logs

**Backend Logs:**
```bash
# Systemd service
sudo journalctl -u rti-backend -f

# Docker
docker-compose logs -f backend
```

**Frontend Logs:**
```bash
# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### Health Checks

**Backend Health Endpoint:**
```bash
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "database": "connected",
  "mongodb": "connected",
  "groq_api": "available"
}
```

**Database Health:**
```bash
# PostgreSQL
psql -U rti_user -d rti_lens -c "SELECT 1;"

# MongoDB
mongosh --eval "db.adminCommand('ping')"
```

### Performance Monitoring

**Backboard.io Integration:**

The application includes Backboard.io SDK for workflow tracking:

```python
# Already integrated in backend/routers/query_assistant.py
from backboard import Backboard

bb = Backboard(api_key=os.getenv("BACKBOARD_API_KEY"))

# Tracks:
# - RAG retrieval latency
# - LLM generation time
# - End-to-end request duration
# - Error rates
```

View metrics at: https://backboard.io/dashboard

---

## Troubleshooting

### Common Issues

**1. Database Connection Error**

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check connection
psql -U rti_user -d rti_lens -c "SELECT 1;"

# Check DATABASE_URL in .env
cat backend/.env | grep DATABASE_URL
```

**2. Groq API Rate Limit**

```
Error: Rate limit exceeded
```

Solution: Implement request queuing or upgrade Groq plan

**3. MongoDB Vector Search Not Working**

```bash
# Verify vector index exists
mongosh
use rti_lens
db.embeddings.getIndexes()

# Recreate if missing (see MongoDB Setup section)
```

**4. Frontend Can't Connect to Backend**

```bash
# Check CORS settings in backend/.env
CORS_ORIGINS=http://localhost:5173

# Check frontend API URL
cat frontend/.env | grep VITE_API_BASE_URL

# Test backend directly
curl http://localhost:8000/health
```

**5. BM25 Index Missing**

```
Error: bm25_pageindex.pkl not found
```

Solution:
```bash
cd backend
python scripts/build_bm25_index.py
```

### Debug Mode

Enable detailed logging:

```bash
# backend/.env
DEBUG=true
LOG_LEVEL=DEBUG

# Restart backend
sudo systemctl restart rti-backend
```

### Performance Issues

**Slow RAG Retrieval:**
- Check PostgreSQL query performance: `EXPLAIN ANALYZE`
- Verify indexes exist on `paragraphs` table
- Consider increasing `shared_buffers` in PostgreSQL config

**Slow LLM Generation:**
- Groq API latency (external, cannot optimize)
- Consider caching common queries
- Implement request batching

---

## Backup & Recovery

### Database Backup

**PostgreSQL:**
```bash
# Backup
pg_dump -U rti_user rti_lens > backup_$(date +%Y%m%d).sql

# Restore
psql -U rti_user rti_lens < backup_20240510.sql
```

**MongoDB:**
```bash
# Backup
mongodump --uri="mongodb://localhost:27017/rti_lens" --out=backup_$(date +%Y%m%d)

# Restore
mongorestore --uri="mongodb://localhost:27017/rti_lens" backup_20240510/
```

### Automated Backups

**Cron Job:** `/etc/cron.daily/rti-backup`

```bash
#!/bin/bash
BACKUP_DIR=/backups/rti-lens
DATE=$(date +%Y%m%d)

# PostgreSQL backup
pg_dump -U rti_user rti_lens | gzip > $BACKUP_DIR/postgres_$DATE.sql.gz

# MongoDB backup
mongodump --uri="mongodb://localhost:27017/rti_lens" --archive=$BACKUP_DIR/mongo_$DATE.archive --gzip

# Keep only last 7 days
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete
find $BACKUP_DIR -name "*.archive" -mtime +7 -delete
```

---

## Security Checklist

- [ ] Change default database passwords
- [ ] Use environment variables for secrets (never commit to git)
- [ ] Enable SSL/TLS for all external connections
- [ ] Configure firewall (UFW/iptables)
- [ ] Implement rate limiting
- [ ] Regular security updates (`apt update && apt upgrade`)
- [ ] Monitor logs for suspicious activity
- [ ] Backup encryption
- [ ] API key rotation policy
- [ ] Database connection encryption

---

## Scaling Considerations

### Horizontal Scaling

**Backend:**
- Run multiple backend instances behind load balancer
- Use shared PostgreSQL and MongoDB
- Implement Redis for session management (future)

**Frontend:**
- Serve static files from CDN
- Multiple frontend servers behind load balancer

### Vertical Scaling

**Database:**
- Increase PostgreSQL `shared_buffers` and `work_mem`
- Add read replicas for query load
- MongoDB Atlas auto-scaling

**Application:**
- Increase Uvicorn workers: `--workers 8`
- Increase system resources (CPU/RAM)

---

## Support

For deployment issues:
- Check logs first
- Review troubleshooting section
- GitHub Issues: [Link]
- Email: devops@rti-lens.example.com
