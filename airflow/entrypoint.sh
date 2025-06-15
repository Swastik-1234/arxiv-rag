#!/bin/bash
set -e

# Clean up any existing PID files and processes
echo "Cleaning up any existing Airflow processes..."
pkill -f "airflow webserver" || true
pkill -f "airflow scheduler" || true
rm -f /opt/airflow/airflow-webserver.pid
rm -f /opt/airflow/airflow-scheduler.pid
sleep 2

# Initialize Airflow database
echo "Initializing Airflow database..."
airflow db migrate

# Create admin user
echo "Creating admin user..."
airflow users create \
    --username ${AIRFLOW_ADMIN_USER:-admin} \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password ${AIRFLOW_ADMIN_PASSWORD:-admin} || echo "Admin user already exists"

# Start webserver as daemon and scheduler in foreground
echo "Starting Airflow webserver and scheduler..."
airflow webserver --port 8080 --daemon &
airflow scheduler
