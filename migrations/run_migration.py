#!/usr/bin/env python3
"""
Database Migration Runner
Applies migrations to the SQLite database with automatic backup
"""

import sqlite3
import shutil
from pathlib import Path
from datetime import datetime
import sys

# Database paths
DB_PATH = Path(__file__).parent.parent / "api" / "data" / "automation" / "queue.db"
BACKUP_DIR = Path(__file__).parent.parent / "api" / "data" / "automation" / "backups"
MIGRATIONS_DIR = Path(__file__).parent


def create_backup(db_path):
    """Create timestamped backup of database"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"queue_backup_{timestamp}.db"
    shutil.copy2(db_path, backup_path)
    print(f"✅ Created backup: {backup_path}")
    return backup_path


def table_exists(cursor, table_name):
    """Check if a table exists"""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None


def column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def run_migration(db_path, migration_file):
    """Run a single migration file with smart ALTER TABLE handling"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Read migration SQL
        with open(migration_file, 'r') as f:
            sql_content = f.read()

        # Split by sections to handle ALTER TABLE smartly
        sections = sql_content.split('-- ============================================================================')

        for section in sections:
            if not section.strip():
                continue

            # Handle ALTER TABLE statements separately
            if 'ALTER TABLE used_topics' in section:
                if table_exists(cursor, 'used_topics'):
                    # Add columns one by one, ignoring errors if they exist
                    alterations = [
                        ("theme", "ALTER TABLE used_topics ADD COLUMN theme TEXT"),
                        ("sub_theme", "ALTER TABLE used_topics ADD COLUMN sub_theme TEXT"),
                        ("tier", "ALTER TABLE used_topics ADD COLUMN tier INTEGER"),
                        ("source_type", "ALTER TABLE used_topics ADD COLUMN source_type TEXT")
                    ]
                    for col_name, alter_sql in alterations:
                        if not column_exists(cursor, 'used_topics', col_name):
                            cursor.execute(alter_sql)
                            print(f"  ✅ Added column used_topics.{col_name}")
                        else:
                            print(f"  ⚠️  Column used_topics.{col_name} already exists")
                else:
                    print(f"  ⚠️  Table used_topics doesn't exist yet (will be created on first run)")

            elif 'ALTER TABLE content_memory' in section:
                if table_exists(cursor, 'content_memory'):
                    alterations = [
                        ("theme", "ALTER TABLE content_memory ADD COLUMN theme TEXT"),
                        ("sub_theme", "ALTER TABLE content_memory ADD COLUMN sub_theme TEXT"),
                        ("trend_tier", "ALTER TABLE content_memory ADD COLUMN trend_tier INTEGER")
                    ]
                    for col_name, alter_sql in alterations:
                        if not column_exists(cursor, 'content_memory', col_name):
                            cursor.execute(alter_sql)
                            print(f"  ✅ Added column content_memory.{col_name}")
                        else:
                            print(f"  ⚠️  Column content_memory.{col_name} already exists")
                else:
                    print(f"  ⚠️  Table content_memory doesn't exist yet (will be created on first run)")

            # Execute CREATE TABLE and INSERT statements directly
            elif ('CREATE TABLE' in section or 'CREATE INDEX' in section or
                  'INSERT INTO' in section) and 'ALTER TABLE' not in section:
                try:
                    cursor.executescript(section)
                except sqlite3.Error as e:
                    # Ignore "already exists" errors
                    if 'already exists' not in str(e).lower():
                        print(f"  ⚠️  Warning: {e}")

        conn.commit()
        print(f"✅ Migration applied: {migration_file.name}")
        return True

    except sqlite3.Error as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()


def get_table_info(db_path, table_name):
    """Get column information for a table"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    conn.close()
    return columns


def verify_migration(db_path):
    """Verify that migration was successful"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\n🔍 Verifying migration...")

    # Check new tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]

    required_tables = ['trend_sources', 'trend_theme_mapping']
    for table in required_tables:
        if table in tables:
            print(f"  ✅ Table '{table}' created")
        else:
            print(f"  ❌ Table '{table}' missing")

    # Check new columns in used_topics
    used_topics_columns = get_table_info(db_path, 'used_topics')
    column_names = [col[1] for col in used_topics_columns]

    required_columns = ['theme', 'sub_theme', 'tier', 'source_type']
    for col in required_columns:
        if col in column_names:
            print(f"  ✅ Column 'used_topics.{col}' added")
        else:
            print(f"  ❌ Column 'used_topics.{col}' missing")

    # Check source data seeded
    cursor.execute("SELECT COUNT(*) FROM trend_sources")
    source_count = cursor.fetchone()[0]
    print(f"  ✅ Seeded {source_count} sources in trend_sources")

    conn.close()
    print("\n✅ Migration verification complete!\n")


def main():
    """Main migration runner"""
    print("\n" + "="*60)
    print("DATABASE MIGRATION RUNNER")
    print("="*60 + "\n")

    # Check for --yes flag
    auto_yes = '--yes' in sys.argv or '-y' in sys.argv

    if not DB_PATH.exists():
        print(f"❌ Database not found: {DB_PATH}")
        sys.exit(1)

    print(f"📁 Database: {DB_PATH}")
    print(f"📁 Migrations: {MIGRATIONS_DIR}\n")

    # Create backup
    backup_path = create_backup(DB_PATH)

    # Get migration files
    migrations = sorted(MIGRATIONS_DIR.glob("*.sql"))

    if not migrations:
        print("⚠️  No migration files found")
        return

    print(f"\n📋 Found {len(migrations)} migration(s):\n")
    for migration in migrations:
        print(f"  - {migration.name}")

    # Confirm
    if not auto_yes:
        response = input("\n❓ Apply these migrations? [y/N]: ")
        if response.lower() != 'y':
            print("❌ Migration cancelled")
            return
    else:
        print("\n✅ Auto-confirming (--yes flag provided)")

    # Run migrations
    print("\n🚀 Running migrations...\n")
    success = True
    for migration in migrations:
        if not run_migration(DB_PATH, migration):
            success = False
            break

    if success:
        verify_migration(DB_PATH)
        print(f"✅ All migrations applied successfully!")
        print(f"💾 Backup saved at: {backup_path}")
    else:
        print(f"\n❌ Migration failed. Restore backup if needed:")
        print(f"   cp {backup_path} {DB_PATH}")


if __name__ == "__main__":
    main()
