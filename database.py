import sqlite3
import secrets
from typing import List, Optional, Tuple


class Database:
    def __init__(self, db_path: str = "wishlist.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Таблица пользователей
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Таблица хотелок (без категорий, с completed)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wishes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                wish_text TEXT NOT NULL,
                photo_id TEXT,
                video_id TEXT,
                completed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Таблица приглашений
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invitations (
                token TEXT PRIMARY KEY,
                owner_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (owner_id) REFERENCES users(user_id)
            )
        """)

        # Таблица друзей
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS friendships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                friend_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (friend_id) REFERENCES users(user_id),
                UNIQUE(user_id, friend_id)
            )
        """)

        conn.commit()
        conn.close()

    def add_user(self, user_id: int, username: str = None, first_name: str = None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO users (user_id, username, first_name)
            VALUES (?, ?, ?)
        """, (user_id, username, first_name))
        conn.commit()
        conn.close()

    def add_wish(self, user_id: int, wish_text: str, photo_id: str = None, video_id: str = None) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO wishes (user_id, wish_text, photo_id, video_id)
            VALUES (?, ?, ?, ?)
        """, (user_id, wish_text, photo_id, video_id))
        wish_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return wish_id

    def get_wishes(self, user_id: int) -> List[Tuple]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, wish_text, photo_id, video_id, completed, created_at
            FROM wishes
            WHERE user_id = ?
            ORDER BY completed ASC, created_at DESC
        """, (user_id,))
        wishes = cursor.fetchall()
        conn.close()
        return wishes

    def delete_wish(self, user_id: int, wish_id: int) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM wishes
            WHERE id = ? AND user_id = ?
        """, (wish_id, user_id))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

    def mark_completed(self, user_id: int, wish_id: int, completed: bool) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE wishes
            SET completed = ?
            WHERE id = ? AND user_id = ?
        """, (1 if completed else 0, wish_id, user_id))
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return updated

    def create_invitation(self, user_id: int) -> str:
        token = secrets.token_urlsafe(16)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM invitations WHERE owner_id = ?", (user_id,))
        cursor.execute("""
            INSERT INTO invitations (token, owner_id)
            VALUES (?, ?)
        """, (token, user_id))
        conn.commit()
        conn.close()
        return token

    def get_owner_by_token(self, token: str) -> Optional[int]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT owner_id FROM invitations
            WHERE token = ?
        """, (token,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def get_user_info(self, user_id: int) -> Optional[Tuple[str, str]]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT username, first_name FROM users
            WHERE user_id = ?
        """, (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result if result else None

    def add_friend(self, user_id: int, friend_id: int) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO friendships (user_id, friend_id)
                VALUES (?, ?)
            """, (user_id, friend_id))
            cursor.execute("""
                INSERT OR IGNORE INTO friendships (user_id, friend_id)
                VALUES (?, ?)
            """, (friend_id, user_id))
            conn.commit()
            success = True
        except:
            success = False
        finally:
            conn.close()
        return success

    def get_friends(self, user_id: int) -> List[Tuple[int, str, str]]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.user_id, u.username, u.first_name
            FROM friendships f
            JOIN users u ON f.friend_id = u.user_id
            WHERE f.user_id = ?
            ORDER BY u.first_name
        """, (user_id,))
        friends = cursor.fetchall()
        conn.close()
        return friends

    def are_friends(self, user_id: int, friend_id: int) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM friendships
            WHERE user_id = ? AND friend_id = ?
        """, (user_id, friend_id))
        result = cursor.fetchone()[0] > 0
        conn.close()
        return result
