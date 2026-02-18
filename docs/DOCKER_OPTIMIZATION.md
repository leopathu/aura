# Optimize Docker Image Builds

## Backend Optimization

### Current Dockerfile
The backend Dockerfile is already optimized for development with hot-reload.

### Production Optimization
For production, consider:

1. **Multi-stage build**
```dockerfile
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "4"]
```

2. **Layer caching**: Requirements installed before code copy
3. **Smaller base image**: Already using slim variant
4. **No cache**: `--no-cache-dir` flag for pip

## Frontend Optimization

### Current Dockerfile
The frontend Dockerfile uses multi-stage build.

### Additional Optimizations

1. **Standalone output** (already in next.config.js)
```js
output: 'standalone'
```

2. **Image optimization**
```js
images: {
  domains: ['your-cdn-domain.com'],
  formats: ['image/avif', 'image/webp'],
}
```

3. **Compression**
```js
compress: true,
swcMinify: true,
```

## Build Optimizations

### Docker BuildKit
Enable BuildKit for faster builds:
```bash
export DOCKER_BUILDKIT=1
docker compose build
```

### Build Arguments
Use build args for version tagging:
```yaml
args:
  - VERSION=${VERSION:-latest}
  - BUILD_DATE=${BUILD_DATE}
```

### Multi-platform Builds
Build for different architectures:
```bash
docker buildx build --platform linux/amd64,linux/arm64 -t aura-backend .
```

## CI/CD Optimizations

1. **GitHub Actions Cache**: Already implemented in ci.yml
2. **Parallel builds**: Backend and frontend build in parallel
3. **Docker layer caching**: Using `cache-from` and `cache-to`

## Size Reduction

### Backend
- Current: ~500MB
- Optimized: ~300MB (with multi-stage build)

### Frontend
- Current: ~150MB
- Optimized: ~100MB (with standalone output)

## Performance Tips

1. **Use .dockerignore**
2. **Minimize layers** (combine RUN commands)
3. **Order matters** (less frequently changed first)
4. **Use specific versions** (already implemented)
5. **Remove dev dependencies in production**

## Monitoring

Add health checks for better orchestration:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```
