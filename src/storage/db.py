"""SQLite storage for training data."""
import sqlite3
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class TrainingDataDB:
    """SQLite database for storing training examples."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.batch_queue: List[Dict[str, Any]] = []
        self.batch_size = 1000
        self.lock = asyncio.Lock()
        self._ensure_db()
    
    def _ensure_db(self):
        """Ensure database and table exist."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS training_examples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scenario_id TEXT UNIQUE,
                scenario_json TEXT NOT NULL,
                reasoning_json TEXT NOT NULL,
                validation_status TEXT NOT NULL,
                validation_error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_validation_status 
            ON training_examples(validation_status)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at 
            ON training_examples(created_at)
        """)
        
        conn.commit()
        conn.close()
    
    async def insert(
        self,
        scenario: Dict[str, Any],
        reasoning: Dict[str, Any],
        validation_status: str = "VALID",
        validation_error: Optional[str] = None,
        scenario_id: Optional[str] = None
    ):
        """Insert a training example (batched)."""
        if scenario_id is None:
            scenario_id = f"scenario_{datetime.now().timestamp()}"
        
        example = {
            "scenario_id": scenario_id,
            "scenario_json": json.dumps(scenario),
            "reasoning_json": json.dumps(reasoning),
            "validation_status": validation_status,
            "validation_error": validation_error,
        }
        
        async with self.lock:
            self.batch_queue.append(example)
            
            if len(self.batch_queue) >= self.batch_size:
                await self._flush_batch()
    
    async def _flush_batch(self):
        """Flush batch to database."""
        if not self.batch_queue:
            return
        
        batch = self.batch_queue.copy()
        self.batch_queue.clear()
        
        # Run in thread pool to avoid blocking
        await asyncio.get_event_loop().run_in_executor(
            None,
            self._write_batch,
            batch
        )
    
    def _write_batch(self, batch: List[Dict[str, Any]]):
        """Write batch to database (synchronous)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for example in batch:
                cursor.execute("""
                    INSERT OR REPLACE INTO training_examples
                    (scenario_id, scenario_json, reasoning_json, validation_status, validation_error, updated_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    example["scenario_id"],
                    example["scenario_json"],
                    example["reasoning_json"],
                    example["validation_status"],
                    example["validation_error"],
                ))
            
            conn.commit()
        except Exception as e:
            logger.error(f"Error writing batch: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    async def flush(self):
        """Flush any pending batches."""
        async with self.lock:
            await self._flush_batch()
    
    def get_valid_examples(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get validated examples."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = """
            SELECT scenario_json, reasoning_json
            FROM training_examples
            WHERE validation_status = 'VALID'
            ORDER BY created_at DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        examples = []
        for row in rows:
            examples.append({
                "scenario": json.loads(row["scenario_json"]),
                "reasoning": json.loads(row["reasoning_json"]),
            })
        
        return examples
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN validation_status = 'VALID' THEN 1 ELSE 0 END) as valid,
                SUM(CASE WHEN validation_status = 'INVALID' THEN 1 ELSE 0 END) as invalid
            FROM training_examples
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        return {
            "total": row[0] or 0,
            "valid": row[1] or 0,
            "invalid": row[2] or 0,
        }

