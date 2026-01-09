# Deployment Guide

## Quick Start

### Using Docker Compose

```bash
# Clone repository
git clone https://github.com/zkaedi/vulnsphere-prime.git
cd vulnsphere-prime

# Copy environment file
cp env.example .env

# Start all services
docker-compose up -d

# Access the platform
# Frontend: http://localhost:3000
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## Manual Installation

### Backend

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Run server
uvicorn backend.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Production Deployment

### Using Docker

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Using Kubernetes

```bash
kubectl apply -f deploy/kubernetes/
```

## Environment Variables

See `env.example` for all available configuration options.

Key variables:
- `FRACTAL_ALPHA`: Fractal order (default: 0.618)
- `PHI`: Golden ratio (default: 1.618)
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string

## Health Checks

```bash
curl http://localhost:8000/health
```

## Troubleshooting

### eBPF Issues

eBPF requires privileged mode. Ensure Docker is running with `--privileged` flag.

### Database Connection

Ensure PostgreSQL and Redis are running and accessible.

### Port Conflicts

Modify ports in `docker-compose.yml` if conflicts occur.
