import sqlite3
import json
from typing import List, Dict, Tuple
import logging

class SimpleWebpageDBManager:
    def __init__(self, db_path: str = 'webpage_analysis.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS webpages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    title TEXT,
                    content_type TEXT,
                    language_score REAL,
                    cleaned_text TEXT,
                    summary TEXT,
                    keywords TEXT,
                    named_entities TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS webpage_similarities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    webpage1_id INTEGER,
                    webpage2_id INTEGER,
                    similarity_score REAL,
                    FOREIGN KEY (webpage1_id) REFERENCES webpages (id),
                    FOREIGN KEY (webpage2_id) REFERENCES webpages (id),
                    UNIQUE(webpage1_id, webpage2_id)
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_webpages_url ON webpages(url)')
            conn.commit()

    def add_webpage(self, webpage_data: Dict) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO webpages 
                    (url, title, content_type, language_score, cleaned_text, summary, keywords, named_entities)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    webpage_data['url'],
                    webpage_data['title'],
                    webpage_data['content_type'],
                    webpage_data['language_score'],
                    webpage_data.get('cleaned_text', ''),
                    webpage_data.get('summary', ''),
                    json.dumps(webpage_data.get('keywords', [])),
                    json.dumps(webpage_data.get('named_entities', {}))
                ))
                return cursor.lastrowid
            except Exception as e:
                logging.error(f"Error adding webpage to database: {e}")
                raise
    
    def add_similarities(self, similarities: List[Tuple[int, int, float]]):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            try:
                cursor.executemany('''
                    INSERT OR REPLACE INTO webpage_similarities 
                    (webpage1_id, webpage2_id, similarity_score)
                    VALUES (?, ?, ?)
                ''', similarities)
                conn.commit()
            except Exception as e:
                logging.error(f"Error adding similarities to database: {e}")
                raise
    
    def get_webpage_metadata(self, webpage_id: int) -> Dict:
        """Get metadata for a specific webpage"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    id, url, title, content_type, 
                    language_score, summary, keywords, named_entities
                FROM webpages 
                WHERE id = ?
            ''', (webpage_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'url': row[1],
                    'title': row[2],
                    'content_type': row[3],
                    'language_score': row[4],
                    'summary': row[5],
                    'keywords': json.loads(row[6]) if row[6] else [],
                    'named_entities': json.loads(row[7]) if row[7] else {}
                }
            return None

    def get_similar_webpages(self, webpage_id: int, limit: int = 5, threshold: float = 0.5) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    w.id, 
                    w.url, 
                    w.title, 
                    w.content_type,
                    w.cleaned_text,
                    w.summary,
                    w.keywords,
                    w.named_entities,
                    s.similarity_score
                FROM webpages w
                JOIN webpage_similarities s ON 
                    (s.webpage1_id = w.id AND s.webpage2_id = ?) OR
                    (s.webpage2_id = w.id AND s.webpage1_id = ?)
                WHERE w.id != ? AND s.similarity_score >= ?
                ORDER BY s.similarity_score DESC
                LIMIT ?
            ''', (webpage_id, webpage_id, webpage_id, threshold, limit))
            
            results = []
            for row in cursor.fetchall():
                webpage_dict = {
                    'id': row[0],
                    'url': row[1],
                    'title': row[2],
                    'content_type': row[3],
                    'cleaned_text': row[4],
                    'summary': row[5],
                    'keywords': json.loads(row[6]) if row[6] else [],
                    'named_entities': json.loads(row[7]) if row[7] else {},
                    'similarity': row[8]
                }
                results.append(webpage_dict)
            
            return results