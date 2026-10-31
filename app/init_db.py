"""Создаёт и наполняет базу lab.db. Запускать из папки app/:  python init_db.py"""
import sqlite3

db = sqlite3.connect("lab.db")
db.executescript("""
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS comments;

CREATE TABLE users (
    id       INTEGER PRIMARY KEY,
    username TEXT,
    password TEXT,
    secret   TEXT
);

CREATE TABLE comments (
    id     INTEGER PRIMARY KEY,
    author TEXT,
    body   TEXT
);

INSERT INTO users (username, password, secret) VALUES
    ('admin', 'S3cr3tAdminP@ss', 'flag: admin_secret_42'),
    ('alice', 'qwerty123',       'flag: alice_secret'),
    ('bob',   'password',        'flag: bob_secret');

INSERT INTO comments (author, body) VALUES
    ('Настасья', 'Привет! Это тестовая гостевая книга.'),
    ('Гость',    'Оставьте свой отзыв ниже.');
""")
db.commit()
db.close()
print("lab.db создана и наполнена")
