"""
Нарочно уязвимое веб-приложение (гостевая книга) для лабораторной работы 2.
ВНИМАНИЕ: содержит СПЕЦИАЛЬНО оставленные уязвимости. Запускать только локально,
в сеть не выставлять. Уязвимости помечены комментариями "# VULN".

Уязвимости (OWASP Top 10 2021):
  VULN 1 — SQL Injection          -> A03:2021 Injection   (во входе и в поиске)
  VULN 2 — Stored XSS             -> A03:2021 Injection    (в гостевой книге)
"""

import sqlite3
from flask import (
    Flask, request, redirect, url_for, session, render_template, g
)

app = Flask(__name__)
app.secret_key = "insecure-demo-key"   # заведомо слабый ключ (это демо)
DB = "lab.db"


def get_db():
    db = getattr(g, "_db", None)
    if db is None:
        db = g._db = sqlite3.connect(DB)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_db(exc):
    db = getattr(g, "_db", None)
    if db is not None:
        db.close()


@app.route("/")
def index():
    db = get_db()
    comments = db.execute(
        "SELECT author, body FROM comments ORDER BY id DESC"
    ).fetchall()
    return render_template("index.html", comments=comments)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        db = get_db()
        # VULN 1 (SQL Injection): пользовательский ввод подставляется в SQL
        # напрямую через форматирование строки. Можно обойти аутентификацию
        # payload-ом  admin' --
        query = ("SELECT * FROM users WHERE username = '%s' AND password = '%s'"
                 % (username, password))
        row = db.execute(query).fetchone()
        if row:
            session["user"] = row["username"]
            return redirect(url_for("profile"))
        error = "Неверный логин или пароль"
    return render_template("login.html", error=error)


@app.route("/search")
def search():
    q = request.args.get("q", "")
    results = []
    if q:
        db = get_db()
        # VULN 1 (SQL Injection): та же проблема в поиске по авторам.
        # Через UNION SELECT можно выгрузить логины и пароли из таблицы users.
        query = ("SELECT author, body FROM comments WHERE author LIKE '%%%s%%'"
                 % q)
        results = db.execute(query).fetchall()
    return render_template("search.html", results=results, q=q)


@app.route("/comment", methods=["POST"])
def comment():
    author = request.form.get("author", "Аноним") or "Аноним"
    body = request.form.get("body", "")
    db = get_db()
    # Вставка сделана параметризованно (здесь SQLi нет) — уязвимость в выводе.
    db.execute(
        "INSERT INTO comments (author, body) VALUES (?, ?)", (author, body)
    )
    db.commit()
    return redirect(url_for("index"))


@app.route("/profile")
def profile():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("profile.html")


@app.route("/account")
def account():
    # VULN 3 (IDOR / Broken Access Control, A01:2021): идентификатор аккаунта
    # берётся прямо из параметра запроса ?id=, принадлежность пользователю
    # не проверяется. Запрос к БД параметризован (SQLi здесь нет) — проблема
    # именно в отсутствии контроля доступа: подставив чужой id, можно
    # прочитать секрет любого аккаунта, и даже без входа в систему.
    uid = request.args.get("id", "1")
    db = get_db()
    row = db.execute(
        "SELECT username, secret FROM users WHERE id = ?", (uid,)
    ).fetchone()
    if row is None:
        return "Аккаунт не найден", 404
    return render_template("account.html", acc=row)


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))


if __name__ == "__main__":
    # debug=False специально: включённый debug=True добавил бы ещё одну
    # уязвимость (A05: Security Misconfiguration — консоль Werkzeug).
    app.run(host="127.0.0.1", port=5000, debug=False)
