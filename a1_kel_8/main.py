import eel
import mysql.connector
from mysql.connector import Error
from datetime import datetime, date
import hashlib

# Inisialisasi folder frontend (web)
eel.init('web')

current_user = None

# Fungsi koneksi ke database MySQL
def create_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',          
            user='root',               
            password='',               
            database='manajemen_kadaluarsa'
        )
        if connection.is_connected():
            print("✅ Koneksi ke database berhasil.")
            return connection
    except Error as e:
        print(f"❌ Gagal konek ke database: {e}")
        return None
    
    
@eel.expose  # penting! agar bisa dipanggil dari JS
def register_user(name, email, password):
    connection = create_connection()
    cursor = connection.cursor()

    # Hash password biar aman
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()

    query = "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)"
    cursor.execute(query, (name, email, hashed_pw))
    connection.commit()

    cursor.close()
    connection.close()
    return "success"

@eel.expose
def login_user(email, password):
    global current_user  
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()

    if user:
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        if hashed_pw == user['password']:
            current_user = email 
            print("✅ Login berhasil untuk:", email)
            return "success"
        else:
            print("❌ Password salah untuk:", email)
            return "wrong_password"
    else:
        print("❌ Email tidak ditemukan:", email)
        return "not_found"
    
@eel.expose
def update_profile(email, name):
    try:
        connection = create_connection()
        cursor = connection.cursor()
        
        query = "UPDATE users SET name = %s WHERE email = %s"
        cursor.execute(query, (name, email))
        connection.commit()

        cursor.close()
        connection.close()
        print(f"✅ Profil diperbarui untuk {email}")
        return "success"
    except Exception as e:
        print(f"❌ Gagal update profil: {e}")
        return "error"
    
@eel.expose
def get_foods_by_user():
    global current_user
    if not current_user:
        print("❌ Tidak ada user login.")
        return []

    connection = create_connection()
    cursor = connection.cursor(dictionary=True)

    query = "SELECT * FROM foods WHERE user_email = %s ORDER BY id DESC"
    cursor.execute(query, (current_user,))
    rows = cursor.fetchall()
    cursor.close()
    connection.close()

    for row in rows:
        if isinstance(row["tanggal_dibuat"], datetime):
            row["tanggal_dibuat"] = format_datetime(row["tanggal_dibuat"])
        if isinstance(row.get("tanggal_edit"), datetime):
            row["tanggal_edit"] = format_datetime(row["tanggal_edit"])
        if isinstance(row["created_at"], datetime):
            row["created_at"] = format_datetime(row["created_at"])
        if isinstance(row["updated_at"], datetime):
            row["updated_at"] = format_datetime(row["updated_at"])
        if isinstance(row["tanggal_expired"], date):
            row["tanggal_expired"] = format_date(row["tanggal_expired"])


    print(f"🍽️ Mengambil data makanan milik: {current_user}")
    return rows

@eel.expose
def add_food(nama_makanan, jumlah, tanggal_expired):
    global current_user
    if not current_user:
        print("❌ Tidak ada user login.")
        return "not_logged_in"

    connection = create_connection()
    cursor = connection.cursor()

    query = """
    INSERT INTO foods (user_email, nama_makanan, jumlah, tanggal_dibuat, tanggal_expired, created_at, updated_at)
    VALUES (%s, %s, %s, NOW(), %s, NOW(), NOW())
    """
    cursor.execute(query, (current_user, nama_makanan, jumlah, tanggal_expired))
    connection.commit()

    cursor.close()
    connection.close()

    print(f"✅ Makanan '{nama_makanan}' berhasil ditambahkan oleh {current_user}")
    return "success"

@eel.expose
def get_food_by_id(food_id):
    global current_user
    if not current_user:
        print("❌ Tidak ada user login.")
        return None

    connection = create_connection()
    cursor = connection.cursor(dictionary=True)

    query = "SELECT * FROM foods WHERE id = %s AND user_email = %s"
    cursor.execute(query, (food_id, current_user))
    food = cursor.fetchone()

    cursor.close()
    connection.close()

    print(f"📌 Mengambil data makanan ID {food_id}")
    return food

@eel.expose
def update_food(food_id, nama_makanan, jumlah, tanggal_expired):
    global current_user
    if not current_user:
        print("❌ User belum login.")
        return "not_logged_in"

    try:
        connection = create_connection()
        cursor = connection.cursor()

        query = """
        UPDATE foods 
        SET nama_makanan = %s, jumlah = %s, tanggal_expired = %s, 
            tanggal_edit = NOW(), updated_at = NOW()
        WHERE id = %s AND user_email = %s
        """
        
        cursor.execute(query, (nama_makanan, jumlah, tanggal_expired, food_id, current_user))
        connection.commit()

        cursor.close()
        connection.close()

        print(f"✏️ Makanan ID {food_id} berhasil diperbarui.")
        return "success"
    
    except Exception as e:
        print(f"❌ Error update: {e}")
        return "error"
    
@eel.expose
def delete_food(food_id):
    global current_user
    if not current_user:
        print("❌ User belum login.")
        return "not_logged_in"

    try:
        connection = create_connection()
        cursor = connection.cursor()

        query = "DELETE FROM foods WHERE id = %s AND user_email = %s"
        cursor.execute(query, (food_id, current_user))
        connection.commit()

        cursor.close()
        connection.close()

        print(f"🗑️ Makanan ID {food_id} berhasil dihapus.")
        return "success"

    except Exception as e:
        print(f"❌ Error menghapus makanan: {e}")
        return "error"

@eel.expose
def format_datetime(dt):
    if dt is None:
        return None
    return dt.strftime("%Y-%m-%dT%H:%M:%S")

@eel.expose
def format_date(d):
    if d is None:
        return None
    return d.strftime("%Y-%m-%dT00:00:00")

@eel.expose
def update_password(current_password, new_password):
    global current_user
    if not current_user:
        return "not_logged_in"

    connection = create_connection()
    cursor = connection.cursor(dictionary=True)

    # Ambil user
    cursor.execute("SELECT password FROM users WHERE email = %s", (current_user,))
    user = cursor.fetchone()

    if not user:
        cursor.close()
        connection.close()
        return "user_not_found"

    # Hash password lama untuk dicocokkan
    hashed_current = hashlib.sha256(current_password.encode()).hexdigest()

    if hashed_current != user["password"]:
        cursor.close()
        connection.close()
        return "wrong_password"

    # Hash password baru
    hashed_new = hashlib.sha256(new_password.encode()).hexdigest()

    cursor.execute("UPDATE users SET password = %s WHERE email = %s", (hashed_new, current_user))
    connection.commit()

    cursor.close()
    connection.close()

    return "success"

@eel.expose
def delete_account(password):
    global current_user
    if not current_user:
        return "not_logged_in"

    connection = create_connection()
    cursor = connection.cursor(dictionary=True)

    # Ambil user
    cursor.execute("SELECT password FROM users WHERE email = %s", (current_user,))
    user = cursor.fetchone()

    if not user:
        cursor.close()
        connection.close()
        return "user_not_found"

    # Cek password
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    if hashed_pw != user["password"]:
        cursor.close()
        connection.close()
        return "wrong_password"

    # Hapus semua makanan milik user
    cursor.execute("DELETE FROM foods WHERE user_email = %s", (current_user,))

    # Hapus akun user
    cursor.execute("DELETE FROM users WHERE email = %s", (current_user,))
    connection.commit()

    cursor.close()
    connection.close()

    current_user = None
    return "success"

@eel.expose
def reset_password(email, new_password):
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)

    # cek apakah email ada
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()

    if not user:
        cursor.close()
        connection.close()
        return "not_found"

    # hash password baru
    hashed_pw = hashlib.sha256(new_password.encode()).hexdigest()

    cursor.execute("UPDATE users SET password = %s WHERE email = %s", (hashed_pw, email))
    connection.commit()

    cursor.close()
    connection.close()

    return "success"

@eel.expose
def logout():
    global current_user
    current_user = None
    print("🔒 User logged out.")
    return "success"

# Jalankan Eel
if __name__ == '__main__':
    print("Running the app, u might wanna keep waiting just like arsenal fans waiting for ucl trophy...")
    eel.start('register.html', mode='chrome', cmdline_args=['--start-fullscreen'], port=8001)
