"""SQLite storage for training data with async queue system."""
import sqlite3
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class TrainingDataDB:
    """SQLite database for storing training examples with async queue."""
    
    def __init__(self, db_path: str, batch_size: int = 100, max_queue_size: int = 10000):
        self.db_path = db_path
        self.batch_size = batch_size
        self.max_queue_size = max_queue_size
        
        # Async queue for writes
        self.write_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self.batch_buffer: List[Dict[str, Any]] = []
        self.batch_lock = asyncio.Lock()
        
        # Worker task
        self.worker_task: Optional[asyncio.Task] = None
        self.running = False
        
        # Statistics
        self.stats = {
            "queued": 0,
            "written": 0,
            "dropped": 0,
            "errors": 0,
        }
        
        self._ensure_db()
    
    async def start(self):
        """Start the background worker."""
        self.running = True
        self.worker_task = asyncio.create_task(self._worker())
        logger.info("Database queue worker started")
    
    async def stop(self):
        """Stop the worker and flush remaining items."""
        self.running = False
        
        # Flush remaining items in buffer
        async with self.batch_lock:
            if self.batch_buffer:
                await self._flush_batch()
        
        # Wait for queue to drain
        while not self.write_queue.empty():
            await asyncio.sleep(0.1)
        
        # Cancel worker
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Database queue worker stopped")
    
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
        """Insert a training example (queued, non-blocking)."""
        if scenario_id is None:
            scenario_id = f"scenario_{datetime.now().timestamp()}"
        
        example = {
            "scenario_id": scenario_id,
            "scenario_json": json.dumps(scenario),
            "reasoning_json": json.dumps(reasoning),
            "validation_status": validation_status,
            "validation_error": validation_error,
        }
        
        # Try to put in queue (non-blocking with backpressure)
        try:
            self.write_queue.put_nowait(example)
            self.stats["queued"] += 1
        except asyncio.QueueFull:
            # Queue is full - drop or wait based on policy
            # For now, we'll wait briefly then drop if still full
            try:
                await asyncio.wait_for(self.write_queue.put(example), timeout=0.1)
                self.stats["queued"] += 1
            except asyncio.TimeoutError:
                self.stats["dropped"] += 1
                logger.warning(f"Queue full, dropping example {scenario_id}")
    
    async def _worker(self):
        """Background worker that processes the write queue."""
        logger.info("Database write worker started")
        
        while self.running:
            try:
                # Collect batch from queue
                batch = []
                timeout = 1.0  # Flush after 1 second even if batch not full
                
                # Get first item (blocking)
                try:
                    item = await asyncio.wait_for(self.write_queue.get(), timeout=timeout)
                    batch.append(item)
                except asyncio.TimeoutError:
                    # Timeout - flush any pending batch
                    if batch:
                        await self._flush_batch(batch)
                    continue
                
                # Collect more items up to batch_size or timeout
                deadline = asyncio.get_event_loop().time() + 0.1  # 100ms to collect batch
                while len(batch) < self.batch_size:
                    remaining_time = deadline - asyncio.get_event_loop().time()
                    if remaining_time <= 0:
                        break
                    
                    try:
                        item = await asyncio.wait_for(
                            self.write_queue.get(),
                            timeout=remaining_time
                        )
                        batch.append(item)
                    except asyncio.TimeoutError:
                        break
                
                # Flush batch
                if batch:
                    await self._flush_batch(batch)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in database worker: {e}", exc_info=True)
                self.stats["errors"] += 1
                await asyncio.sleep(1)  # Brief pause on error
        
        # Flush any remaining items
        remaining = []
        while not self.write_queue.empty():
            try:
                remaining.append(self.write_queue.get_nowait())
            except asyncio.QueueEmpty:
                break
        
        if remaining:
            await self._flush_batch(remaining)
        
        logger.info("Database write worker stopped")
    
    async def _flush_batch(self, batch: List[Dict[str, Any]]):
        """Flush batch to database."""
        if not batch:
            return
        
        # Run in thread pool to avoid blocking event loop
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._write_batch,
                batch
            )
            self.stats["written"] += len(batch)
        except Exception as e:
            logger.error(f"Error flushing batch: {e}")
            self.stats["errors"] += len(batch)
    
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
        """Flush any pending batches (wait for queue to drain)."""
        # Wait for queue to be processed
        max_wait = 30  # Maximum wait time in seconds
        start_time = asyncio.get_event_loop().time()
        
        while not self.write_queue.empty():
            if asyncio.get_event_loop().time() - start_time > max_wait:
                logger.warning(f"Flush timeout after {max_wait}s, {self.write_queue.qsize()} items still queued")
                break
            await asyncio.sleep(0.1)
        
        logger.info(f"Database flush complete. Stats: {self.stats}")
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        return {
            "queue_size": self.write_queue.qsize(),
            "max_queue_size": self.max_queue_size,
            "queued_total": self.stats["queued"],
            "written_total": self.stats["written"],
            "dropped_total": self.stats["dropped"],
            "errors_total": self.stats["errors"],
        }
    
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

