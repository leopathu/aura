#!/bin/bash
# Database Restore Script for Aura

# Check if backup file is provided
if [ -z "$1" ]; then
    echo "Usage: ./restore.sh <backup_file>"
    echo "Example: ./restore.sh /backups/aura_backup_20260218_120000.sql.gz"
    exit 1
fi

BACKUP_FILE=$1
DB_NAME="aura_db"
DB_USER="aura_user"
DB_HOST="postgres"

# Check if backup file exists
if [ ! -f "${BACKUP_FILE}" ]; then
    echo "Error: Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

# Confirm restoration
echo "WARNING: This will restore the database from: ${BACKUP_FILE}"
echo "Current database will be overwritten!"
read -p "Are you sure you want to continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

# Perform restore
echo "Starting database restore..."
gunzip -c ${BACKUP_FILE} | PGPASSWORD=${POSTGRES_PASSWORD} pg_restore \
    -h ${DB_HOST} \
    -U ${DB_USER} \
    -d ${DB_NAME} \
    --clean \
    --if-exists \
    --no-owner \
    --no-privileges

if [ $? -eq 0 ]; then
    echo "Restore completed successfully!"
else
    echo "Restore failed!"
    exit 1
fi
