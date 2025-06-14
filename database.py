"""
Database operations for the Quotex VIP Channel Bot
"""

import sqlite3
import logging
from datetime import datetime
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Users table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        telegram_id INTEGER UNIQUE NOT NULL,
                        quotex_user_id TEXT NOT NULL,
                        verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        vip_link_id INTEGER,
                        FOREIGN KEY (vip_link_id) REFERENCES vip_links (id)
                    )
                ''')
                
                # VIP Links table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS vip_links (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        link TEXT UNIQUE NOT NULL,
                        is_used BOOLEAN DEFAULT FALSE,
                        used_by INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        used_at TIMESTAMP,
                        FOREIGN KEY (used_by) REFERENCES users (telegram_id)
                    )
                ''')
                
                # Verification attempts table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS verification_attempts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        telegram_id INTEGER NOT NULL,
                        quotex_user_id TEXT NOT NULL,
                        success BOOLEAN NOT NULL,
                        attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    def add_user(self, telegram_id: int, quotex_user_id: str, vip_link_id: int) -> bool:
        """Add a verified user to the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO users (telegram_id, quotex_user_id, vip_link_id)
                    VALUES (?, ?, ?)
                ''', (telegram_id, quotex_user_id, vip_link_id))
                conn.commit()
                logger.info(f"User {telegram_id} added successfully")
                return True
        except sqlite3.Error as e:
            logger.error(f"Error adding user: {e}")
            return False
    
    def is_user_verified(self, telegram_id: int) -> bool:
        """Check if a user is already verified"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1 FROM users WHERE telegram_id = ?', (telegram_id,))
                return cursor.fetchone() is not None
        except sqlite3.Error as e:
            logger.error(f"Error checking user verification: {e}")
            return False
    
    def add_vip_links(self, links: List[str]) -> int:
        """Add multiple VIP links to the database"""
        added_count = 0
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for link in links:
                    try:
                        cursor.execute('INSERT INTO vip_links (link) VALUES (?)', (link.strip(),))
                        added_count += 1
                    except sqlite3.IntegrityError:
                        logger.warning(f"Link already exists: {link}")
                        continue
                conn.commit()
                logger.info(f"Added {added_count} VIP links")
        except sqlite3.Error as e:
            logger.error(f"Error adding VIP links: {e}")
        return added_count
    
    def get_unused_vip_link(self) -> Optional[Tuple[int, str]]:
        """Get an unused VIP link"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, link FROM vip_links 
                    WHERE is_used = FALSE 
                    ORDER BY created_at ASC 
                    LIMIT 1
                ''')
                result = cursor.fetchone()
                return result if result else None
        except sqlite3.Error as e:
            logger.error(f"Error getting unused VIP link: {e}")
            return None
    
    def mark_link_as_used(self, link_id: int, telegram_id: int) -> bool:
        """Mark a VIP link as used"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE vip_links 
                    SET is_used = TRUE, used_by = ?, used_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (telegram_id, link_id))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Error marking link as used: {e}")
            return False
    
    def log_verification_attempt(self, telegram_id: int, quotex_user_id: str, success: bool):
        """Log a verification attempt"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO verification_attempts (telegram_id, quotex_user_id, success)
                    VALUES (?, ?, ?)
                ''', (telegram_id, quotex_user_id, success))
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error logging verification attempt: {e}")
    
    def get_stats(self) -> dict:
        """Get bot statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total users
                cursor.execute('SELECT COUNT(*) FROM users')
                total_users = cursor.fetchone()[0]
                
                # Total links
                cursor.execute('SELECT COUNT(*) FROM vip_links')
                total_links = cursor.fetchone()[0]
                
                # Used links
                cursor.execute('SELECT COUNT(*) FROM vip_links WHERE is_used = TRUE')
                used_links = cursor.fetchone()[0]
                
                # Available links
                available_links = total_links - used_links
                
                # Total verification attempts
                cursor.execute('SELECT COUNT(*) FROM verification_attempts')
                total_attempts = cursor.fetchone()[0]
                
                # Successful verifications
                cursor.execute('SELECT COUNT(*) FROM verification_attempts WHERE success = TRUE')
                successful_verifications = cursor.fetchone()[0]
                
                return {
                    'total_users': total_users,
                    'total_links': total_links,
                    'used_links': used_links,
                    'available_links': available_links,
                    'total_attempts': total_attempts,
                    'successful_verifications': successful_verifications
                }
        except sqlite3.Error as e:
            logger.error(f"Error getting stats: {e}")
            return {}
    
    def get_recent_users(self, limit: int = 20) -> List[dict]:
        """Get recent verified users"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT telegram_id, quotex_user_id, verified_at
                    FROM users 
                    ORDER BY verified_at DESC 
                    LIMIT ?
                ''', (limit,))
                
                users = []
                for row in cursor.fetchall():
                    users.append({
                        'telegram_id': row[0],
                        'quotex_user_id': row[1],
                        'verified_at': row[2]
                    })
                return users
        except sqlite3.Error as e:
            logger.error(f"Error getting recent users: {e}")
            return []
