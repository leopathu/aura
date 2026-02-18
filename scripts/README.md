# Scripts

Helper scripts for development and deployment.

## Development Scripts

### dev-start.sh
Start the development environment with Docker Compose.
```bash
./scripts/dev-start.sh
```

This script:
- Creates necessary .env files if missing
- Pulls latest Docker images
- Builds containers
- Starts all services in order
- Shows service URLs and status

### dev-stop.sh
Stop all development services.
```bash
./scripts/dev-stop.sh
```

### logs.sh
View logs for all services or a specific service.
```bash
# All services
./scripts/logs.sh

# Specific service
./scripts/logs.sh backend
./scripts/logs.sh frontend
./scripts/logs.sh postgres
```

## Database Scripts

### migrate.sh
Run database migrations using Alembic.
```bash
./scripts/migrate.sh
```

### backup.sh
Create a database backup.
```bash
./scripts/backup.sh
```

Backups are stored in `database/backups/` with timestamp.

## Usage Examples

```bash
# Start development
./scripts/dev-start.sh

# View backend logs
./scripts/logs.sh backend

# Run migrations
./scripts/migrate.sh

# Create backup
./scripts/backup.sh

# Stop everything
./scripts/dev-stop.sh
```

## Production

For production deployment, use `docker-compose.prod.yml`:

```bash
docker compose -f docker-compose.prod.yml up -d
```
