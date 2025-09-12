import sqlite3
import json
import pandas as pd

def analyze_database():
    """Analyze the current database structure and data"""
    conn = sqlite3.connect('agricultural_data.db')
    cursor = conn.cursor()
    
    print("=== DATABASE SCHEMA ANALYSIS ===\n")
    
    # Get table schemas
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
    schemas = cursor.fetchall()
    
    for schema in schemas:
        print(f"Table Schema:\n{schema[0]}\n")
    
    print("=== FORM_RESPONSES TABLE ANALYSIS ===\n")
    
    # Check form_responses table structure
    cursor.execute("PRAGMA table_info(form_responses)")
    columns = cursor.fetchall()
    print("Form_responses columns:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]}) {'NOT NULL' if col[3] else ''} {'PRIMARY KEY' if col[5] else ''}")
    
    # Get sample data from form_responses
    cursor.execute("SELECT * FROM form_responses LIMIT 3")
    form_data = cursor.fetchall()
    
    print(f"\nTotal form_responses records: {len(form_data)}")
    if form_data:
        print("\nSample form_responses records:")
        for i, record in enumerate(form_data):
            print(f"\nRecord {i+1}:")
            print(f"  ID: {record[0]}")
            print(f"  Farmer ID: {record[1]}")
            print(f"  District: {record[2]}")
            print(f"  Village: {record[3]}")
            print(f"  EA Code: {record[4]}")
            print(f"  Season/Year: {record[5]}")
            print(f"  Crop Type: {record[6]}")
            print(f"  Submission Date: {record[8]}")
            
            # Parse and display JSON form data
            try:
                json_data = json.loads(record[7])
                print(f"  JSON Form Data Keys: {list(json_data.keys())}")
                if 'selected_crops' in json_data:
                    print(f"  Selected Crops: {json_data['selected_crops']}")
                if 'crop_data' in json_data:
                    print(f"  Crop Data Keys: {list(json_data['crop_data'].keys())}")
            except json.JSONDecodeError:
                print(f"  Form Data (raw): {record[7][:100]}...")
    
    print("\n=== FIELD_BOUNDARIES TABLE ANALYSIS ===\n")
    
    # Check field_boundaries table structure
    cursor.execute("PRAGMA table_info(field_boundaries)")
    columns = cursor.fetchall()
    print("Field_boundaries columns:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]}) {'NOT NULL' if col[3] else ''} {'PRIMARY KEY' if col[5] else ''}")
    
    # Get sample data from field_boundaries
    cursor.execute("SELECT * FROM field_boundaries LIMIT 3")
    boundary_data = cursor.fetchall()
    
    print(f"\nTotal field_boundaries records: {len(boundary_data)}")
    if boundary_data:
        print("\nSample field_boundaries records:")
        for i, record in enumerate(boundary_data):
            print(f"\nBoundary {i+1}:")
            print(f"  ID: {record[0]}")
            print(f"  Farmer ID: {record[1]}")
            print(f"  Field Name: {record[2]}")
            print(f"  Field Type: {record[3]}")
            print(f"  Crop Type: {record[4]}")
            print(f"  Area Estimate: {record[6]}")
            print(f"  Creation Date: {record[8]}")
            print(f"  Coordinates Length: {len(record[5]) if record[5] else 0}")
    
    print("\n=== RELATIONSHIP ANALYSIS ===\n")
    
    # Check potential relationships
    cursor.execute("SELECT DISTINCT farmer_id FROM form_responses")
    form_farmers = {row[0] for row in cursor.fetchall()}
    
    cursor.execute("SELECT DISTINCT farmer_id FROM field_boundaries")
    boundary_farmers = {row[0] for row in cursor.fetchall()}
    
    print(f"Farmers in form_responses: {len(form_farmers)}")
    print(f"Farmers in field_boundaries: {len(boundary_farmers)}")
    print(f"Common farmers: {len(form_farmers.intersection(boundary_farmers))}")
    
    # Check crop type overlap
    cursor.execute("SELECT DISTINCT crop_type FROM form_responses")
    form_crops = {row[0] for row in cursor.fetchall()}
    
    cursor.execute("SELECT DISTINCT crop_type FROM field_boundaries")
    boundary_crops = {row[0] for row in cursor.fetchall()}
    
    print(f"\nCrop types in form_responses: {form_crops}")
    print(f"Crop types in field_boundaries: {boundary_crops}")
    print(f"Common crop types: {form_crops.intersection(boundary_crops)}")
    
    # Check for potential farmer_id + crop_type combinations
    cursor.execute("""
        SELECT f.farmer_id, f.crop_type, COUNT(*) as form_count
        FROM form_responses f
        GROUP BY f.farmer_id, f.crop_type
    """)
    form_combinations = cursor.fetchall()
    
    cursor.execute("""
        SELECT b.farmer_id, b.crop_type, COUNT(*) as boundary_count
        FROM field_boundaries b
        GROUP BY b.farmer_id, b.crop_type
    """)
    boundary_combinations = cursor.fetchall()
    
    print(f"\nFarmer+Crop combinations in forms: {len(form_combinations)}")
    print(f"Farmer+Crop combinations in boundaries: {len(boundary_combinations)}")
    
    if form_combinations:
        print("\nSample form combinations:")
        for combo in form_combinations[:3]:
            print(f"  {combo[0]} + {combo[1]}: {combo[2]} records")
    
    if boundary_combinations:
        print("\nSample boundary combinations:")
        for combo in boundary_combinations[:3]:
            print(f"  {combo[0]} + {combo[1]}: {combo[2]} records")
    
    conn.close()

if __name__ == "__main__":
    analyze_database()