from flask import Flask, render_template, request
from datetime import datetime
import sqlite3

app = Flask(__name__)

BASE_PRICE = 3500
EVERSEND_BASE = "https://eversend.me/premiummovies"
TELEGRAM_GROUP_LINK = "https://t.me/+cwJ1bPtsoChjMDI0"

def init_db():
    conn = sqlite3.connect("sales.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ref TEXT,
            amount INTEGER,
            commission INTEGER,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/", methods=["GET", "POST"])
def index():
    affiliate_link = None
    error_message = None

    if request.method == "POST":
        ref = request.form.get("ref").strip()
        price_input = request.form.get("price").strip()

        if not ref or not price_input:
            error_message = "Please fill in all fields."
        else:
            try:
                price = int(price_input)
                if price < BASE_PRICE:
                    error_message = f"❌ Minimum allowed price is {BASE_PRICE} UGX."
                else:
                    # Regenerate link
                    affiliate_link = f"{EVERSEND_BASE}?amount={price}&ref={ref}"
            except ValueError:
                error_message = "Please enter a valid number for price."

    return render_template("index.html",
                           affiliate_link=affiliate_link,
                           error_message=error_message,
                           base_price=BASE_PRICE)


@app.route("/thankyou")
def thankyou():
    ref = request.args.get("ref")
    amount = request.args.get("amount")

    if not ref or not amount:
        return "Invalid redirect — missing parameters."

    try:
        amount = int(amount)
    except ValueError:
        return "Invalid amount."

    commission = amount - BASE_PRICE
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Save sale in DB
    conn = sqlite3.connect("sales.db")
    conn.execute(
        "INSERT INTO sales (ref, amount, commission, created_at) VALUES (?, ?, ?, ?)",
        (ref, amount, commission, created_at)
    )
    conn.commit()
    conn.close()

    return render_template("thankyou.html",
                           ref=ref,
                           amount=amount,
                           commission=commission,
                           telegram_link=TELEGRAM_GROUP_LINK)


@app.route("/sales")
def view_sales():
    conn = sqlite3.connect("sales.db")
    cursor = conn.execute("SELECT ref, amount, commission, created_at FROM sales ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return render_template("sales.html", sales=rows)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
