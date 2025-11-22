import eel
import hashlib
from db import get_connection

eel.init('web')

# Register
@eel.expose
def register_user(fullname, email, phone, password):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        hashed = hashlib.sha256(password.encode()).hexdigest()

        sql = "INSERT INTO users (fullname, email, phone, password) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (fullname, email, phone, hashed))

        conn.commit()
        return "success"

    except Exception as e:
        print(e)
        return "error"

# Login
@eel.expose
def login_user(email, password):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        hashed = hashlib.sha256(password.encode()).hexdigest()
        sql = "SELECT * FROM users WHERE email = %s AND password = %s"
        cursor.execute(sql, (email, hashed))

        user = cursor.fetchone()

        if user:
            return {
                "status": "success",
                "fullname": user["fullname"],
                "email": user["email"]
            }
        else:
            return { "status": "invalid" }

    except Exception as e:
        print(e)
        return { "status": "error" }

# Fungsi untuk menyimpan informasi transaksi
@eel.expose
def create_transaction(email, product, account_number, amount):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        admin_fee = 1500
        total = amount + admin_fee

        sql = """
            INSERT INTO transactions (user_email, product, account_number, amount, admin_fee, total)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (email, product, account_number, amount, admin_fee, total))
        conn.commit()

        return cursor.lastrowid  

    except Exception as e:
        print(e)
        return "error"


# Fungsi untuk menampilkan invoice transaksi user menggunakan transaksi ID
@eel.expose
def get_transaction(transaction_id):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        sql = "SELECT * FROM transactions WHERE id = %s"
        cursor.execute(sql, (transaction_id,))
        trx = cursor.fetchone()

        return trx

    except Exception as e:
        print(e)
        return None

# Fungsi untuk menampilkan transaksi user
@eel.expose
def get_transactions_by_user(email):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        sql = "SELECT * FROM transactions WHERE user_email = %s ORDER BY created_at DESC"
        cursor.execute(sql, (email,))
        transactions = cursor.fetchall()

        # Mengubah timestamp ke string
        for t in transactions:
            if isinstance(t["created_at"], (bytes, bytearray)):
                t["created_at"] = str(t["created_at"])
            else:
                t["created_at"] = t["created_at"].strftime("%Y-%m-%d %H:%M:%S")

        return transactions

    except Exception as e:
        print(e)
        return []

# get stats
@eel.expose
def get_dashboard_stats(email):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Total transaksi
        sql_count = "SELECT COUNT(*) AS total_transactions FROM transactions WHERE user_email = %s"
        cursor.execute(sql_count, (email,))
        total_trx = cursor.fetchone()["total_transactions"]

        # Total pengeluaran 
        sql_sum = "SELECT IFNULL(SUM(total), 0) AS total_spent FROM transactions WHERE user_email = %s AND status='success'"
        cursor.execute(sql_sum, (email,))
        total_spent = cursor.fetchone()["total_spent"]

        return {
            "total_transactions": total_trx,
            "total_spent": total_spent
        }

    except Exception as e:
        print(e)
        return {
            "total_transactions": 0,
            "total_spent": 0
        }


eel.start(
    'index.html',
    cmdline_args=['--start-maximized']
)
