import sqlite3
import os

DATABASE = os.path.join("db", "social.db")

def init_db():
    if not os.path.exists("db"):
        os.makedirs("db")
    if not os.path.exists(DATABASE):
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            bio TEXT,
            profile_pic TEXT
        )
        """)

        # Posts table
        cursor.execute("""
        CREATE TABLE posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            image TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """)

        # Follows table
        cursor.execute("""
        CREATE TABLE follows (
            follower_id INTEGER,
            following_id INTEGER,
            FOREIGN KEY(follower_id) REFERENCES users(id),
            FOREIGN KEY(following_id) REFERENCES users(id)
        )
        """)

        # Likes table
        cursor.execute("""
        CREATE TABLE likes (
            user_id INTEGER,
            post_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(post_id) REFERENCES posts(id)
        )
        """)

        conn.commit()
        conn.close()
        print("✅ Database initialized at", DATABASE)
    else:
        print("ℹ️ Database already exists at", DATABASE)

if __name__ == "__main__":
    init_db()
