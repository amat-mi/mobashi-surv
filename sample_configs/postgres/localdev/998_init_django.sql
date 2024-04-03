CREATE USER django;

CREATE DATABASE mobashisurv OWNER django;

ALTER ROLE django SET client_encoding TO 'utf8';
ALTER ROLE django SET default_transaction_isolation TO 'read committed';
ALTER ROLE django SET timezone TO 'UTC';

GRANT ALL PRIVILEGES ON DATABASE mobashisurv TO django;

\c mobashisurv
CREATE EXTENSION postgis;
