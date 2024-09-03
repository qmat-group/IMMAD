#!/bin/sh

PGHOST=postgres.postgres
PGPORT=5432
PGADMIN=admin
PGPASSWORD=$2
PGLOGIN=postgresql://$PGADMIN:$PGPASSWORD@$PGHOST/postgres

RABBITMQ_HOST=rabbitmq-cluster.rabbitmq
RABBITMQ_USER=$4
RABBITMQ_PASSWORD=$5
RABBITMQ_PORT=5672

EMAIL=$1
ROLE="${EMAIL//[^[:alnum:]]/_}"
CONFIG_FILE="$3/config.yaml"
DB_NAME="immad_$ROLE"

# check if DB_NAME is in PSQL
# if not create that DB, create role IMMAD_USER and
# grant all privilege to IMMAD_USER for DB_NAME
if psql -lqt $PGLOGIN | cut -d \| -f 1 | grep -qw $DB_NAME; then
  exit 0
fi

PASSWORD=`echo $RANDOM | base64 | head -c 20; echo`
psql $PGLOGIN << EOF
DO
\$do\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles
                 WHERE rolname = '$ROLE') THEN
    CREATE ROLE $ROLE LOGIN PASSWORD '$PASSWORD';
  END IF;
END
\$do\$;

CREATE DATABASE $DB_NAME OWNER $ROLE ENCODING 'UTF8' LC_COLLATE='en_US.UTF-8' LC_CTYPE='en_US.UTF-8' TEMPLATE=template0;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME to $ROLE;
EOF

psql $PGLOGIN -c "ALTER ROLE $ROLE WITH PASSWORD '$PASSWORD';"

name=`echo $EMAIL | cut -d @ -f 1`
institution=`echo $EMAIL | cut -d @ -f 2`

cat > $CONFIG_FILE << EOF
---
profile: default
email: $EMAIL
first_name: $name
last_name: $name
institution: $institution
db_engine: postgresql_psycopg2
db_backend: core.psql_dos
db_host: $PGHOST
db_port: $PGPORT
db_name: $DB_NAME
db_username: $ROLE
db_password: $PASSWORD
broker_host: $RABBITMQ_HOST
broker_port: $RABBITMQ_PORT
broker_username: $RABBITMQ_USER
broker_password: $RABBITMQ_PASSWORD
EOF
