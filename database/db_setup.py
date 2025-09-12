import sqlite3
import os


def init_database():
    """Initialize the SQLite database with required tables"""
    conn = sqlite3.connect('agricultural_data.db')
    cursor = conn.cursor()

    # Create form_responses table with flexible JSON structure
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS form_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_id TEXT NOT NULL,
            district TEXT NOT NULL,
            village TEXT NOT NULL,
            ea_code TEXT,
            season_year TEXT NOT NULL,
            crop_type TEXT NOT NULL,
            form_data TEXT NOT NULL,
            submission_date TEXT NOT NULL
        )
    ''')

    # Create field_boundaries table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS field_boundaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_id TEXT NOT NULL,
            field_name TEXT NOT NULL,
            field_type TEXT NOT NULL,
            crop_type TEXT NOT NULL,
            coordinates TEXT NOT NULL,
            area_estimate REAL,
            notes TEXT,
            creation_date TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()


def get_database_stats():
    """Get basic statistics about the database"""
    try:
        conn = sqlite3.connect('agricultural_data.db')
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM form_responses")
        form_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM field_boundaries")
        field_count = cursor.fetchone()[0]

        conn.close()

        return {
            'form_responses': form_count,
            'field_boundaries': field_count,
            'total_records': form_count + field_count
        }
    except Exception as e:
        return {
            'error': str(e),
            'form_responses': 0,
            'field_boundaries': 0,
            'total_records': 0
        }


def clear_all_data():
    """Clear all data from the database (use with caution)"""
    try:
        conn = sqlite3.connect('agricultural_data.db')
        cursor = conn.cursor()

        cursor.execute("DELETE FROM form_responses")
        cursor.execute("DELETE FROM field_boundaries")

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error clearing database: {str(e)}")
        return False


if __name__ == "__main__":
    # Initialize database when run directly
    init_database()
    print("Database initialized successfully!")

    stats = get_database_stats()
    print(f"Database stats: {stats}")
