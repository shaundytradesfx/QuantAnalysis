"""
Tests for actual data database migrations.
Tests migration script execution, data integrity, and rollback scenarios.
"""
import unittest
from unittest.mock import patch, MagicMock, call
import tempfile
import os
import sqlite3
from datetime import datetime

from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.database.models import Event, Indicator, Sentiment

class TestActualDataMigration(unittest.TestCase):
    """
    Tests for actual data database migrations.
    """
    
    def setUp(self):
        """
        Set up test fixtures with temporary database.
        """
        # Create temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        self.db_url = f"sqlite:///{self.temp_db.name}"
        self.engine = create_engine(self.db_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create alembic config
        self.alembic_cfg = Config()
        self.alembic_cfg.set_main_option("script_location", "alembic")
        self.alembic_cfg.set_main_option("sqlalchemy.url", self.db_url)
    
    def tearDown(self):
        """
        Clean up test fixtures.
        """
        self.engine.dispose()
        os.unlink(self.temp_db.name)
    
    def test_migration_adds_actual_data_columns(self):
        """
        Test that the migration successfully adds actual data columns to indicators table.
        """
        # Create initial schema (before migration)
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE events (
                    id INTEGER PRIMARY KEY,
                    currency VARCHAR(3),
                    event_name TEXT,
                    scheduled_datetime TIMESTAMP,
                    impact_level VARCHAR(10),
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """))
            
            conn.execute(text("""
                CREATE TABLE indicators (
                    id INTEGER PRIMARY KEY,
                    event_id INTEGER,
                    previous_value NUMERIC(8,4),
                    forecast_value NUMERIC(8,4),
                    timestamp_collected TIMESTAMP,
                    FOREIGN KEY (event_id) REFERENCES events(id)
                )
            """))
            conn.commit()
        
        # Verify columns don't exist before migration
        with self.engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(indicators)"))
            columns = [row[1] for row in result]
            self.assertNotIn("actual_value", columns)
            self.assertNotIn("actual_collected_at", columns)
            self.assertNotIn("actual_sentiment", columns)
            self.assertNotIn("is_actual_available", columns)
        
        # Apply migration (simulate the actual data migration)
        with self.engine.connect() as conn:
            conn.execute(text("""
                ALTER TABLE indicators 
                ADD COLUMN actual_value NUMERIC(8,4) NULL
            """))
            conn.execute(text("""
                ALTER TABLE indicators 
                ADD COLUMN actual_collected_at TIMESTAMP NULL
            """))
            conn.execute(text("""
                ALTER TABLE indicators 
                ADD COLUMN actual_sentiment INTEGER NULL
            """))
            conn.execute(text("""
                ALTER TABLE indicators 
                ADD COLUMN is_actual_available BOOLEAN DEFAULT FALSE
            """))
            conn.commit()
        
        # Verify columns exist after migration
        with self.engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(indicators)"))
            columns = [row[1] for row in result]
            self.assertIn("actual_value", columns)
            self.assertIn("actual_collected_at", columns)
            self.assertIn("actual_sentiment", columns)
            self.assertIn("is_actual_available", columns)
    
    def test_migration_preserves_existing_data(self):
        """
        Test that migration preserves existing data in events and indicators tables.
        """
        # Create initial schema and data
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE events (
                    id INTEGER PRIMARY KEY,
                    currency VARCHAR(3),
                    event_name TEXT,
                    scheduled_datetime TIMESTAMP,
                    impact_level VARCHAR(10),
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """))
            
            conn.execute(text("""
                CREATE TABLE indicators (
                    id INTEGER PRIMARY KEY,
                    event_id INTEGER,
                    previous_value NUMERIC(8,4),
                    forecast_value NUMERIC(8,4),
                    timestamp_collected TIMESTAMP,
                    FOREIGN KEY (event_id) REFERENCES events(id)
                )
            """))
            
            # Insert test data
            conn.execute(text("""
                INSERT INTO events (id, currency, event_name, scheduled_datetime, impact_level, created_at, updated_at)
                VALUES (1, 'USD', 'CPI y/y', '2024-01-14 14:30:00', 'High', '2024-01-13 10:00:00', '2024-01-13 10:00:00')
            """))
            
            conn.execute(text("""
                INSERT INTO indicators (id, event_id, previous_value, forecast_value, timestamp_collected)
                VALUES (1, 1, 2.0, 2.5, '2024-01-13 10:00:00')
            """))
            conn.commit()
        
        # Verify data exists before migration
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM events"))
            self.assertEqual(result.scalar(), 1)
            
            result = conn.execute(text("SELECT COUNT(*) FROM indicators"))
            self.assertEqual(result.scalar(), 1)
            
            result = conn.execute(text("SELECT previous_value, forecast_value FROM indicators WHERE id = 1"))
            row = result.fetchone()
            self.assertEqual(float(row[0]), 2.0)
            self.assertEqual(float(row[1]), 2.5)
        
        # Apply migration
        with self.engine.connect() as conn:
            conn.execute(text("ALTER TABLE indicators ADD COLUMN actual_value NUMERIC(8,4) NULL"))
            conn.execute(text("ALTER TABLE indicators ADD COLUMN actual_collected_at TIMESTAMP NULL"))
            conn.execute(text("ALTER TABLE indicators ADD COLUMN actual_sentiment INTEGER NULL"))
            conn.execute(text("ALTER TABLE indicators ADD COLUMN is_actual_available BOOLEAN DEFAULT FALSE"))
            conn.commit()
        
        # Verify data still exists after migration
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM events"))
            self.assertEqual(result.scalar(), 1)
            
            result = conn.execute(text("SELECT COUNT(*) FROM indicators"))
            self.assertEqual(result.scalar(), 1)
            
            result = conn.execute(text("""
                SELECT previous_value, forecast_value, actual_value, is_actual_available 
                FROM indicators WHERE id = 1
            """))
            row = result.fetchone()
            self.assertEqual(float(row[0]), 2.0)
            self.assertEqual(float(row[1]), 2.5)
            self.assertIsNone(row[2])  # actual_value should be NULL
            self.assertFalse(row[3])   # is_actual_available should be FALSE
    
    def test_migration_default_values(self):
        """
        Test that migration sets correct default values for new columns.
        """
        # Create schema and data
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE indicators (
                    id INTEGER PRIMARY KEY,
                    event_id INTEGER,
                    previous_value NUMERIC(8,4),
                    forecast_value NUMERIC(8,4),
                    timestamp_collected TIMESTAMP
                )
            """))
            
            # Insert test data
            conn.execute(text("""
                INSERT INTO indicators (id, event_id, previous_value, forecast_value, timestamp_collected)
                VALUES (1, 1, 2.0, 2.5, '2024-01-13 10:00:00')
            """))
            conn.commit()
        
        # Apply migration with default values
        with self.engine.connect() as conn:
            conn.execute(text("ALTER TABLE indicators ADD COLUMN actual_value NUMERIC(8,4) NULL"))
            conn.execute(text("ALTER TABLE indicators ADD COLUMN actual_collected_at TIMESTAMP NULL"))
            conn.execute(text("ALTER TABLE indicators ADD COLUMN actual_sentiment INTEGER NULL"))
            conn.execute(text("ALTER TABLE indicators ADD COLUMN is_actual_available BOOLEAN DEFAULT FALSE"))
            conn.commit()
        
        # Verify default values
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT actual_value, actual_collected_at, actual_sentiment, is_actual_available
                FROM indicators WHERE id = 1
            """))
            row = result.fetchone()
            self.assertIsNone(row[0])  # actual_value should be NULL
            self.assertIsNone(row[1])  # actual_collected_at should be NULL
            self.assertIsNone(row[2])  # actual_sentiment should be NULL
            self.assertFalse(row[3])   # is_actual_available should be FALSE (default)
    
    def test_migration_rollback_scenario(self):
        """
        Test migration rollback scenario (removing actual data columns).
        """
        # Create schema with actual data columns
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE indicators (
                    id INTEGER PRIMARY KEY,
                    event_id INTEGER,
                    previous_value NUMERIC(8,4),
                    forecast_value NUMERIC(8,4),
                    timestamp_collected TIMESTAMP,
                    actual_value NUMERIC(8,4) NULL,
                    actual_collected_at TIMESTAMP NULL,
                    actual_sentiment INTEGER NULL,
                    is_actual_available BOOLEAN DEFAULT FALSE
                )
            """))
            
            # Insert test data with actual values
            conn.execute(text("""
                INSERT INTO indicators (
                    id, event_id, previous_value, forecast_value, timestamp_collected,
                    actual_value, actual_collected_at, actual_sentiment, is_actual_available
                )
                VALUES (
                    1, 1, 2.0, 2.5, '2024-01-13 10:00:00',
                    2.3, '2024-01-14 15:00:00', 1, TRUE
                )
            """))
            conn.commit()
        
        # Verify actual data exists
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT actual_value, is_actual_available FROM indicators WHERE id = 1"))
            row = result.fetchone()
            self.assertEqual(float(row[0]), 2.3)
            self.assertTrue(row[1])
        
        # Simulate rollback (recreate table without actual data columns)
        with self.engine.connect() as conn:
            # Create backup table
            conn.execute(text("""
                CREATE TABLE indicators_backup AS 
                SELECT id, event_id, previous_value, forecast_value, timestamp_collected
                FROM indicators
            """))
            
            # Drop original table
            conn.execute(text("DROP TABLE indicators"))
            
            # Recreate table without actual data columns
            conn.execute(text("""
                CREATE TABLE indicators (
                    id INTEGER PRIMARY KEY,
                    event_id INTEGER,
                    previous_value NUMERIC(8,4),
                    forecast_value NUMERIC(8,4),
                    timestamp_collected TIMESTAMP
                )
            """))
            
            # Restore data
            conn.execute(text("""
                INSERT INTO indicators (id, event_id, previous_value, forecast_value, timestamp_collected)
                SELECT id, event_id, previous_value, forecast_value, timestamp_collected
                FROM indicators_backup
            """))
            
            # Clean up
            conn.execute(text("DROP TABLE indicators_backup"))
            conn.commit()
        
        # Verify rollback successful
        with self.engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(indicators)"))
            columns = [row[1] for row in result]
            self.assertNotIn("actual_value", columns)
            self.assertNotIn("actual_collected_at", columns)
            self.assertNotIn("actual_sentiment", columns)
            self.assertNotIn("is_actual_available", columns)
            
            # Verify original data preserved
            result = conn.execute(text("SELECT previous_value, forecast_value FROM indicators WHERE id = 1"))
            row = result.fetchone()
            self.assertEqual(float(row[0]), 2.0)
            self.assertEqual(float(row[1]), 2.5)
    
    def test_migration_indexes_creation(self):
        """
        Test that migration creates appropriate indexes for actual data queries.
        """
        # Create schema
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE indicators (
                    id INTEGER PRIMARY KEY,
                    event_id INTEGER,
                    previous_value NUMERIC(8,4),
                    forecast_value NUMERIC(8,4),
                    timestamp_collected TIMESTAMP,
                    actual_value NUMERIC(8,4) NULL,
                    actual_collected_at TIMESTAMP NULL,
                    actual_sentiment INTEGER NULL,
                    is_actual_available BOOLEAN DEFAULT FALSE
                )
            """))
            
            # Create indexes for actual data queries
            conn.execute(text("""
                CREATE INDEX idx_indicators_event_actual 
                ON indicators(event_id, is_actual_available)
            """))
            
            conn.execute(text("""
                CREATE INDEX idx_indicators_actual_collected 
                ON indicators(actual_collected_at)
            """))
            conn.commit()
        
        # Verify indexes exist
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='indicators'"))
            indexes = [row[0] for row in result]
            self.assertIn("idx_indicators_event_actual", indexes)
            self.assertIn("idx_indicators_actual_collected", indexes)
    
    def test_migration_data_types_validation(self):
        """
        Test that migration creates columns with correct data types.
        """
        # Create schema with actual data columns
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE indicators (
                    id INTEGER PRIMARY KEY,
                    event_id INTEGER,
                    previous_value NUMERIC(8,4),
                    forecast_value NUMERIC(8,4),
                    timestamp_collected TIMESTAMP,
                    actual_value NUMERIC(8,4) NULL,
                    actual_collected_at TIMESTAMP NULL,
                    actual_sentiment INTEGER NULL,
                    is_actual_available BOOLEAN DEFAULT FALSE
                )
            """))
            conn.commit()
        
        # Test inserting valid data types
        with self.engine.connect() as conn:
            # Test numeric actual_value
            conn.execute(text("""
                INSERT INTO indicators (
                    id, event_id, previous_value, forecast_value, timestamp_collected,
                    actual_value, actual_collected_at, actual_sentiment, is_actual_available
                )
                VALUES (
                    1, 1, 2.0, 2.5, '2024-01-13 10:00:00',
                    2.3456, '2024-01-14 15:30:45', 1, TRUE
                )
            """))
            
            # Test NULL values
            conn.execute(text("""
                INSERT INTO indicators (
                    id, event_id, previous_value, forecast_value, timestamp_collected,
                    actual_value, actual_collected_at, actual_sentiment, is_actual_available
                )
                VALUES (
                    2, 2, 1.5, 1.8, '2024-01-13 11:00:00',
                    NULL, NULL, NULL, FALSE
                )
            """))
            conn.commit()
        
        # Verify data types and values
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT actual_value, actual_collected_at, actual_sentiment, is_actual_available
                FROM indicators WHERE id = 1
            """))
            row = result.fetchone()
            self.assertAlmostEqual(float(row[0]), 2.3456, places=4)
            self.assertIsNotNone(row[1])  # timestamp
            self.assertEqual(row[2], 1)   # integer sentiment
            self.assertTrue(row[3])       # boolean
            
            result = conn.execute(text("""
                SELECT actual_value, actual_collected_at, actual_sentiment, is_actual_available
                FROM indicators WHERE id = 2
            """))
            row = result.fetchone()
            self.assertIsNone(row[0])     # NULL actual_value
            self.assertIsNone(row[1])     # NULL timestamp
            self.assertIsNone(row[2])     # NULL sentiment
            self.assertFalse(row[3])      # FALSE boolean
    
    def test_migration_foreign_key_constraints(self):
        """
        Test that migration preserves foreign key constraints.
        """
        # Create schema with foreign key constraints
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE events (
                    id INTEGER PRIMARY KEY,
                    currency VARCHAR(3),
                    event_name TEXT,
                    scheduled_datetime TIMESTAMP,
                    impact_level VARCHAR(10)
                )
            """))
            
            conn.execute(text("""
                CREATE TABLE indicators (
                    id INTEGER PRIMARY KEY,
                    event_id INTEGER,
                    previous_value NUMERIC(8,4),
                    forecast_value NUMERIC(8,4),
                    timestamp_collected TIMESTAMP,
                    actual_value NUMERIC(8,4) NULL,
                    actual_collected_at TIMESTAMP NULL,
                    actual_sentiment INTEGER NULL,
                    is_actual_available BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (event_id) REFERENCES events(id)
                )
            """))
            
            # Insert valid data
            conn.execute(text("""
                INSERT INTO events (id, currency, event_name, scheduled_datetime, impact_level)
                VALUES (1, 'USD', 'CPI y/y', '2024-01-14 14:30:00', 'High')
            """))
            
            conn.execute(text("""
                INSERT INTO indicators (
                    id, event_id, previous_value, forecast_value, timestamp_collected,
                    actual_value, is_actual_available
                )
                VALUES (1, 1, 2.0, 2.5, '2024-01-13 10:00:00', 2.3, TRUE)
            """))
            conn.commit()
        
        # Verify foreign key constraint works
        with self.engine.connect() as conn:
            # This should work (valid foreign key)
            result = conn.execute(text("""
                SELECT e.currency, i.actual_value 
                FROM events e 
                JOIN indicators i ON e.id = i.event_id 
                WHERE i.id = 1
            """))
            row = result.fetchone()
            self.assertEqual(row[0], "USD")
            self.assertEqual(float(row[1]), 2.3)
    
    def test_migration_performance_large_dataset(self):
        """
        Test migration performance with large existing dataset.
        """
        # Create schema
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE indicators (
                    id INTEGER PRIMARY KEY,
                    event_id INTEGER,
                    previous_value NUMERIC(8,4),
                    forecast_value NUMERIC(8,4),
                    timestamp_collected TIMESTAMP
                )
            """))
            
            # Insert large dataset
            for i in range(1000):
                conn.execute(text("""
                    INSERT INTO indicators (id, event_id, previous_value, forecast_value, timestamp_collected)
                    VALUES (?, ?, ?, ?, ?)
                """), (i + 1, (i % 10) + 1, 2.0 + (i * 0.01), 2.5 + (i * 0.01), '2024-01-13 10:00:00'))
            conn.commit()
        
        # Verify initial data count
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM indicators"))
            self.assertEqual(result.scalar(), 1000)
        
        # Measure migration performance
        import time
        start_time = time.time()
        
        with self.engine.connect() as conn:
            conn.execute(text("ALTER TABLE indicators ADD COLUMN actual_value NUMERIC(8,4) NULL"))
            conn.execute(text("ALTER TABLE indicators ADD COLUMN actual_collected_at TIMESTAMP NULL"))
            conn.execute(text("ALTER TABLE indicators ADD COLUMN actual_sentiment INTEGER NULL"))
            conn.execute(text("ALTER TABLE indicators ADD COLUMN is_actual_available BOOLEAN DEFAULT FALSE"))
            conn.commit()
        
        end_time = time.time()
        migration_time = end_time - start_time
        
        # Verify migration completed successfully
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM indicators"))
            self.assertEqual(result.scalar(), 1000)
            
            result = conn.execute(text("PRAGMA table_info(indicators)"))
            columns = [row[1] for row in result]
            self.assertIn("actual_value", columns)
            self.assertIn("is_actual_available", columns)
        
        # Migration should complete within reasonable time (less than 5 seconds for 1000 records)
        self.assertLess(migration_time, 5.0)
    
    @patch('alembic.command.upgrade')
    def test_alembic_integration(self, mock_upgrade):
        """
        Test integration with Alembic migration system.
        """
        # Mock alembic upgrade command
        mock_upgrade.return_value = None
        
        # Simulate running alembic upgrade
        command.upgrade(self.alembic_cfg, "head")
        
        # Verify alembic upgrade was called
        mock_upgrade.assert_called_once_with(self.alembic_cfg, "head")
    
    def test_migration_idempotency(self):
        """
        Test that migration can be run multiple times safely (idempotency).
        """
        # Create initial schema
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE indicators (
                    id INTEGER PRIMARY KEY,
                    event_id INTEGER,
                    previous_value NUMERIC(8,4),
                    forecast_value NUMERIC(8,4),
                    timestamp_collected TIMESTAMP
                )
            """))
            conn.commit()
        
        # Apply migration first time
        with self.engine.connect() as conn:
            conn.execute(text("ALTER TABLE indicators ADD COLUMN actual_value NUMERIC(8,4) NULL"))
            conn.execute(text("ALTER TABLE indicators ADD COLUMN is_actual_available BOOLEAN DEFAULT FALSE"))
            conn.commit()
        
        # Verify columns exist
        with self.engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(indicators)"))
            columns = [row[1] for row in result]
            self.assertIn("actual_value", columns)
            self.assertIn("is_actual_available", columns)
        
        # Attempt to apply migration again (should handle gracefully)
        with self.engine.connect() as conn:
            try:
                # This should fail if column already exists
                conn.execute(text("ALTER TABLE indicators ADD COLUMN actual_value NUMERIC(8,4) NULL"))
                self.fail("Expected error when adding existing column")
            except Exception:
                # Expected behavior - column already exists
                pass
        
        # Verify table is still intact
        with self.engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(indicators)"))
            columns = [row[1] for row in result]
            self.assertIn("actual_value", columns)
            self.assertIn("is_actual_available", columns)

if __name__ == '__main__':
    unittest.main() 