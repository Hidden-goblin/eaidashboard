SELECT 'CREATE DATABASE eaidash'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'eaidash')\gexec