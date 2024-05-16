-- Создаем базу данных, если ее нет
SELECT 'CREATE DATABASE {{ DB_DATABASE }}'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '{{ DB_DATABASE }}')\gexec;

CREATE ROLE root WITH LOGIN PASSWORD 'user';

CREATE USER IF NOT EXISTS {{ DB_REPL_USER }} WITH REPLICATION ENCRYPTED PASSWORD '{{ DB_REPL_PASSWORD }}';

-- Меняем пароль пользователя postgres
ALTER USER postgres WITH PASSWORD '{{ DB_PASSWORD }}';

-- Подключаемся к базе данных
\c {{ DB_DATABASE }};

-- Создаем таблицы, если их нет
CREATE TABLE IF NOT EXISTS phone (PhoneID SERIAL PRIMARY KEY, Phone VARCHAR(30) NOT NULL);
CREATE TABLE IF NOT EXISTS email (EmailID SERIAL PRIMARY KEY, Email VARCHAR(100) NOT NULL);

-- Вставляем данные в таблицы
INSERT INTO phone (PhoneID, Phone) VALUES (DEFAULT, '+7 363 33 335 33');
INSERT INTO email (EmailID, Email) VALUES (DEFAULT, 'lonai@list.ru');