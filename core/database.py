import sqlite3
import os
import json
from loguru import logger
from datetime import datetime

class Database:
    """
    Persistent findings database for SWATH using SQLite.
    """
    
    def __init__(self, db_path="~/.swath/history.db"):
        self.db_path = os.path.expanduser(db_path)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        conn = self._get_conn()
        cur = conn.cursor()
        
        # We assume scans table already exists from original codebase, but we'll add targets, assets, findings
        
        cur.executescript('''
        CREATE TABLE IF NOT EXISTS targets (
            id INTEGER PRIMARY KEY,
            domain TEXT UNIQUE NOT NULL,
            program TEXT,
            platform TEXT,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_scanned TIMESTAMP,
            scope_status TEXT,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY,
            target_id INTEGER REFERENCES targets(id),
            type TEXT NOT NULL,
            value TEXT NOT NULL,
            source TEXT,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP,
            is_alive BOOLEAN DEFAULT 1,
            metadata TEXT,
            UNIQUE(target_id, type, value)
        );

        CREATE TABLE IF NOT EXISTS findings (
            id INTEGER PRIMARY KEY,
            target_id INTEGER REFERENCES targets(id),
            asset_id INTEGER REFERENCES assets(id),
            scan_id INTEGER,
            severity TEXT NOT NULL,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            evidence TEXT,
            tool TEXT NOT NULL,
            template_id TEXT,
            is_verified BOOLEAN DEFAULT 0,
            is_false_positive BOOLEAN DEFAULT 0,
            is_reported BOOLEAN DEFAULT 0,
            platform TEXT,
            report_url TEXT,
            bounty_amount REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(target_id, type, title, tool)
        );

        CREATE TABLE IF NOT EXISTS asset_changes (
            id INTEGER PRIMARY KEY,
            target_id INTEGER REFERENCES targets(id),
            asset_id INTEGER REFERENCES assets(id),
            scan_id INTEGER,
            change_type TEXT NOT NULL,
            field_changed TEXT,
            old_value TEXT,
            new_value TEXT,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ''')
        
        conn.commit()
        conn.close()

    def upsert_target(self, domain, program=None, platform=None):
        conn = self._get_conn()
        try:
            conn.execute('''
                INSERT INTO targets (domain, program, platform, last_scanned)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(domain) DO UPDATE SET
                    program=coalesce(?, program),
                    platform=coalesce(?, platform),
                    last_scanned=CURRENT_TIMESTAMP
            ''', (domain, program, platform, program, platform))
            conn.commit()
            
            cur = conn.execute('SELECT id FROM targets WHERE domain = ?', (domain,))
            return cur.fetchone()['id']
        except sqlite3.Error as e:
            logger.error(f"DB Error upserting target {domain}: {e}")
        finally:
            conn.close()
            
    def upsert_asset(self, target_id, asset_type, value, source, metadata=None):
        conn = self._get_conn()
        try:
            meta_str = json.dumps(metadata) if metadata else None
            conn.execute('''
                INSERT INTO assets (target_id, type, value, source, metadata, last_seen)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(target_id, type, value) DO UPDATE SET
                    last_seen=CURRENT_TIMESTAMP,
                    is_alive=1,
                    metadata=coalesce(?, metadata)
            ''', (target_id, asset_type, value, source, meta_str, meta_str))
            conn.commit()
            
            cur = conn.execute('SELECT id FROM assets WHERE target_id = ? AND type = ? AND value = ?', 
                               (target_id, asset_type, value))
            return cur.fetchone()['id']
        except sqlite3.Error as e:
            logger.error(f"DB Error upserting asset {value}: {e}")
        finally:
            conn.close()

    def add_finding(self, target_id, asset_id, scan_id, severity, finding_type, title, description=None, evidence=None, tool="unknown", template_id=None):
        conn = self._get_conn()
        try:
            conn.execute('''
                INSERT INTO findings (target_id, asset_id, scan_id, severity, type, title, description, evidence, tool, template_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(target_id, type, title, tool) DO UPDATE SET
                    updated_at=CURRENT_TIMESTAMP,
                    scan_id=?,
                    evidence=coalesce(?, evidence)
            ''', (target_id, asset_id, scan_id, severity, finding_type, title, description, evidence, tool, template_id, scan_id, evidence))
            conn.commit()
            
            cur = conn.execute('SELECT id FROM findings WHERE target_id = ? AND type = ? AND title = ? AND tool = ?', 
                               (target_id, finding_type, title, tool))
            return cur.fetchone()['id']
        except sqlite3.Error as e:
            logger.error(f"DB Error adding finding {title}: {e}")
        finally:
            conn.close()
