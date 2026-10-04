import os
import bcrypt
from sqlalchemy import create_engine, text

# Force SQLite on cloud platforms if local MySQL fails to connect
try:
    engine = create_engine("mysql+pymysql://root:Yonkoluffy$3B@localhost:3306/paysim", connect_args={"connect_timeout": 2})
    # Test connection
    with engine.connect() as conn:
        pass
except Exception:
    # If local MySQL is unreachable (like on Streamlit Cloud), use SQLite
    engine = create_engine("sqlite:///users.db")

# 2. Auto-Create Table Setup
# Generates the users table automatically depending on the active database engine
with engine.connect() as conn:
    if "sqlite" in str(engine.url):
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            );
        """))
    else:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL
            );
        """))
    conn.commit()

# 3. Password Hashing
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

# 4. Password Verification
def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

# 5. User Registration
def register_user(username, email, password):
    hashed_pw = hash_password(password)
    query = text("INSERT INTO users (username, email, password_hash) VALUES (:username, :email, :password_hash)")
    
    try:
        with engine.connect() as conn:
            conn.execute(query, {"username": username, "email": email, "password_hash": hashed_pw})
            conn.commit()
        return True, "User registered successfully!"
    except Exception as e:
        return False, f"Error: {e}"

# 6. User Login
def login_user(identifier, password):
    clean_id = identifier.strip()
    query = text("""
        SELECT password_hash, username 
        FROM users 
        WHERE LOWER(username) = LOWER(:id) OR LOWER(email) = LOWER(:id)
    """)
    
    with engine.connect() as conn:
        result = conn.execute(query, {"id": clean_id}).fetchone()
        
    if result:
        stored_hash, db_username = result
        if verify_password(password.strip(), stored_hash):
            return True, f"Welcome back, {db_username}!"
        else:
            return False, "Incorrect password!"
    else:
        return False, "User or Email not found!"
