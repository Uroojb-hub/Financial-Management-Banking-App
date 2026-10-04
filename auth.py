import bcrypt
from sqlalchemy import create_engine, text

# Database connection setup
import os

# If running on Streamlit Cloud, use SQLite; otherwise use local setup
DB_URL = os.getenv("DATABASE_URL", "sqlite:///users.db")
engine = create_engine(DB_URL)

# Password Hashing Function
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

# Password Verification Function
def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

# Register User
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

# Login User
def login_user(identifier, password):
    clean_id = identifier.strip()
    # Checks if input matches either username OR email
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
