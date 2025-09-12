#!/usr/bin/env python3
"""
Quick database commands for common operations
"""

import sqlite3
import pandas as pd

# Quick examples for common database operations:

def show_all_farmers():
    """Show unique farmer IDs"""
    conn = sqlite3.connect('agricultural_data.db')
    df = pd.read_sql_query("SELECT DISTINCT farmer_id FROM form_responses ORDER BY farmer_id", conn)
    conn.close()
    print("All farmer IDs:")
    print(df['farmer_id'].tolist())

def count_records():
    """Show record counts"""
    conn = sqlite3.connect('agricultural_data.db')
    
    # Count form responses
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM form_responses")
    form_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM field_boundaries")
    field_count = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"Form responses: {form_count}")
    print(f"Field boundaries: {field_count}")

def show_recent_data():
    """Show 3 most recent records from each table"""
    conn = sqlite3.connect('agricultural_data.db')
    
    print("=== Recent Form Responses ===")
    form_df = pd.read_sql_query("""
        SELECT id, farmer_id, district, village, crop_type, submission_date 
        FROM form_responses 
        ORDER BY submission_date DESC LIMIT 3
    """, conn)
    print(form_df.to_string(index=False))
    
    print("\n=== Recent Field Boundaries ===")
    field_df = pd.read_sql_query("""
        SELECT id, farmer_id, field_name, crop_type, area_estimate, creation_date
        FROM field_boundaries 
        ORDER BY creation_date DESC LIMIT 3
    """, conn)
    print(field_df.to_string(index=False))
    
    conn.close()

if __name__ == "__main__":
    print("=== Database Quick View ===")
    count_records()
    print()
    show_recent_data()
    print()
    show_all_farmers()