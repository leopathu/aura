#!/bin/bash
# Database Backup Script for Aura

# Configuration
BACKUP_DIR="/backups"
DB_NAME="aura_db"
DB_USER="aura_user"
DB_HOST="postgres"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/aura_backup_${TIMESTAMP}.sql.gz"
RETENTION_DAYS=7

# Create backup directory if it doesn't exist
mkdir -p ${BACKUP_DIR}

# Perform backup
echo "Starting database backup..."
PGPASSWORD=${POSTGRES_PASSWORD} pg_dump \
    -h ${DB_HOST} \
    -U ${DB_USER} \
    -d ${DB_NAME} \
    --format=custom \
    --clean \
    --if-exists \
    | gzip > ${BACKUP_FILE}

if [ $? -eq 0 ]; then
    echo "Backup completed successfully: ${BACKUP_FILE}"
    
    # Calculate file size
    SIZE=$(du -h ${BACKUP_FILE} | cut -f1)
    echo "Backup size: ${SIZE}"
    
    # Clean up old backups
    echo "Cleaning up backups older than ${RETENTION_DAYS} days..."
    find ${BACKUP_DIR} -name "aura_backup_*.sql.gz" -mtime +${RETENTION_DAYS} -delete
    
    echo "Backup process completed!"
else
    echo "Backup failed!"
    exit 1
fi

# List recent backups
echo "Recent backups:"
ls -lh ${BACKUP_DIR}/aura_backup_*.sql.gz | tail -5
