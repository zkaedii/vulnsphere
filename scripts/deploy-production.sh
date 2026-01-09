#!/bin/bash

echo "🔱 Deploying VulnSphere PRIME to Production"
echo "============================================"

# Build Docker images
docker-compose build

# Deploy
docker-compose up -d

# Run health checks
sleep 20
curl -f http://localhost:8000/health || exit 1

echo "✅ Deployment successful!"
echo "🔱 VulnSphere PRIME is LIVE"
