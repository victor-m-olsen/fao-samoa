#!/usr/bin/env python3
"""
Database viewer and editor for agricultural_data.db
Provides functions to view, query, and modify the SQLite database
"""

import sqlite3
import json
import pandas as pd
from datetime import datetime

def view_tables():
    """Show all tables in the database"""
    conn = sqlite3.connect('agricultural_data.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("Available tables:")
    for table in tables:
        print(f"- {table[0]}")
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"  Rows: {count}")
        
        # Show column structure
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        print(f"  Columns: {[col[1] for col in columns]}")
        print()
    
    conn.close()

def view_form_responses(limit=5):
    """View recent form responses"""
    conn = sqlite3.connect('agricultural_data.db')
    
    query = f"""
    SELECT id, farmer_id, district, village, crop_type, submission_date 
    FROM form_responses 
    ORDER BY submission_date DESC 
    LIMIT {limit}
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print(f"Recent {limit} form responses:")
    print(df.to_string(index=False))
    return df

def view_field_boundaries(limit=5):
    """View recent field boundaries"""
    conn = sqlite3.connect('agricultural_data.db')
    
    query = f"""
    SELECT id, farmer_id, field_name, field_type, crop_type, area_estimate, creation_date
    FROM field_boundaries 
    ORDER BY creation_date DESC 
    LIMIT {limit}
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print(f"Recent {limit} field boundaries:")
    print(df.to_string(index=False))
    return df

def search_by_farmer_id(farmer_id):
    """Find all records for a specific farmer"""
    conn = sqlite3.connect('agricultural_data.db')
    
    # Form responses
    print(f"Form responses for farmer {farmer_id}:")
    form_query = "SELECT * FROM form_responses WHERE farmer_id = ?"
    form_df = pd.read_sql_query(form_query, conn, params=(farmer_id,))
    print(form_df.to_string(index=False))
    print()
    
    # Field boundaries
    print(f"Field boundaries for farmer {farmer_id}:")
    field_query = "SELECT * FROM field_boundaries WHERE farmer_id = ?"
    field_df = pd.read_sql_query(field_query, conn, params=(farmer_id,))
    print(field_df.to_string(index=False))
    
    conn.close()
    return form_df, field_df

def execute_custom_query(query):
    """Execute a custom SQL query"""
    conn = sqlite3.connect('agricultural_data.db')
    
    try:
        if query.strip().upper().startswith('SELECT'):
            df = pd.read_sql_query(query, conn)
            print("Query results:")
            print(df.to_string(index=False))
            return df
        else:
            cursor = conn.cursor()
            cursor.execute(query)
            conn.commit()
            print(f"Query executed successfully. Rows affected: {cursor.rowcount}")
    except Exception as e:
        print(f"Error executing query: {e}")
    finally:
        conn.close()

def delete_record(table, record_id):
    """Delete a record by ID"""
    conn = sqlite3.connect('agricultural_data.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"DELETE FROM {table} WHERE id = ?", (record_id,))
        conn.commit()
        print(f"Deleted record {record_id} from {table} table. Rows affected: {cursor.rowcount}")
    except Exception as e:
        print(f"Error deleting record: {e}")
    finally:
        conn.close()

def backup_database():
    """Create a backup of the database"""
    import shutil
    backup_name = f"agricultural_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2('agricultural_data.db', backup_name)
    print(f"Database backed up to: {backup_name}")
    return backup_name

def main():
    print("=== Agricultural Database Viewer ===")
    print("Database file: agricultural_data.db")
    print()
    
    while True:
        print("\nOptions:")
        print("1. View all tables")
        print("2. View recent form responses")
        print("3. View recent field boundaries") 
        print("4. Search by farmer ID")
        print("5. Execute custom SQL query")
        print("6. Delete record")
        print("7. Backup database")
        print("8. Exit")
        
        choice = input("\nSelect option (1-8): ").strip()
        
        if choice == '1':
            view_tables()
        elif choice == '2':
            limit = input("How many records to show? (default 5): ").strip()
            limit = int(limit) if limit.isdigit() else 5
            view_form_responses(limit)
        elif choice == '3':
            limit = input("How many records to show? (default 5): ").strip()
            limit = int(limit) if limit.isdigit() else 5
            view_field_boundaries(limit)
        elif choice == '4':
            farmer_id = input("Enter farmer ID: ").strip()
            if farmer_id:
                search_by_farmer_id(farmer_id)
        elif choice == '5':
            query = input("Enter SQL query: ").strip()
            if query:
                execute_custom_query(query)
        elif choice == '6':
            table = input("Enter table name (form_responses/field_boundaries): ").strip()
            record_id = input("Enter record ID to delete: ").strip()
            if table and record_id.isdigit():
                confirm = input(f"Really delete record {record_id} from {table}? (y/N): ")
                if confirm.lower() == 'y':
                    delete_record(table, int(record_id))
        elif choice == '7':
            backup_database()
        elif choice == '8':
            break
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()