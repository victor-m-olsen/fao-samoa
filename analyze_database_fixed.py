import sqlite3
import json

def analyze_database():
    """Analyze the current database structure and data"""
    conn = sqlite3.connect('agricultural_data.db')
    cursor = conn.cursor()
    
    print("=== DATABASE SCHEMA ANALYSIS ===\n")
    
    # Get table schemas
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
    schemas = cursor.fetchall()
    
    for schema in schemas:
        if schema[0] and 'sqlite_sequence' not in schema[0]:
            print(f"Table Schema:\n{schema[0]}\n")
    
    print("=== FORM_RESPONSES TABLE ANALYSIS ===\n")
    
    # Check form_responses table structure
    cursor.execute("PRAGMA table_info(form_responses)")
    form_columns = cursor.fetchall()
    print("Form_responses columns:")
    for col in form_columns:
        print(f"  - Column {col[0]}: {col[1]} ({col[2]}) {'NOT NULL' if col[3] else ''} {'PRIMARY KEY' if col[5] else ''}")
    
    # Get sample data from form_responses
    cursor.execute("SELECT * FROM form_responses")
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
            print(f"  Crop Type (field): {record[6]}")
            print(f"  Submission Date: {record[8]}")
            
            # Parse and display JSON form data
            try:
                json_data = json.loads(record[7])
                print(f"  JSON Form Data Keys: {list(json_data.keys())}")
                if 'selected_crops' in json_data:
                    print(f"  Selected Crops: {json_data['selected_crops']}")
                if 'crop_data' in json_data:
                    print(f"  Crop Data Keys: {list(json_data['crop_data'].keys())}")
                    # Show sample crop data structure
                    for crop, data in json_data['crop_data'].items():
                        print(f"    {crop} data keys: {list(data.keys())[:5]}...")  # Show first 5 keys
            except json.JSONDecodeError:
                print(f"  Form Data (raw): {record[7][:100]}...")
    
    print("\n=== FIELD_BOUNDARIES TABLE ANALYSIS ===\n")
    
    # Check field_boundaries table structure
    cursor.execute("PRAGMA table_info(field_boundaries)")
    boundary_columns = cursor.fetchall()
    print("Field_boundaries columns:")
    for col in boundary_columns:
        print(f"  - Column {col[0]}: {col[1]} ({col[2]}) {'NOT NULL' if col[3] else ''} {'PRIMARY KEY' if col[5] else ''}")
    
    # Get sample data from field_boundaries
    cursor.execute("SELECT * FROM field_boundaries")
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
            
            # Handle columns based on actual structure
            num_cols = len(record)
            print(f"  Total columns in record: {num_cols}")
            
            if num_cols >= 5:
                print(f"  Column 4 (coordinates?): {str(record[4])[:100]}...")
            if num_cols >= 6:
                print(f"  Column 5 (area?): {record[5]}")
            if num_cols >= 7:
                print(f"  Column 6 (notes?): {record[6]}")
            if num_cols >= 8:
                print(f"  Column 7 (date?): {record[7]}")
            if num_cols >= 9:
                print(f"  Column 8 (crop_type?): {record[8]}")
    
    print("\n=== RELATIONSHIP ANALYSIS ===\n")
    
    # Check potential relationships - farmer_id analysis
    cursor.execute("SELECT DISTINCT farmer_id FROM form_responses")
    form_farmers = {row[0] for row in cursor.fetchall()}
    
    cursor.execute("SELECT DISTINCT farmer_id FROM field_boundaries")
    boundary_farmers = {row[0] for row in cursor.fetchall()}
    
    print(f"Farmers in form_responses: {len(form_farmers)}")
    print(f"Form farmer IDs: {form_farmers}")
    print(f"Farmers in field_boundaries: {len(boundary_farmers)}")
    print(f"Boundary farmer IDs: {boundary_farmers}")
    print(f"Common farmers: {form_farmers.intersection(boundary_farmers)}")
    
    # Analyze form_responses crop storage pattern
    print(f"\n=== CROP DATA STORAGE ANALYSIS ===\n")
    
    if form_data:
        for i, record in enumerate(form_data):
            try:
                json_data = json.loads(record[7])
                selected_crops = json_data.get('selected_crops', [])
                crop_data = json_data.get('crop_data', {})
                
                print(f"Form record {i+1}:")
                print(f"  Farmer: {record[1]}")
                print(f"  Crops selected: {selected_crops}")
                print(f"  Crop data available for: {list(crop_data.keys())}")
                
                # Show production data for each crop
                for crop in crop_data:
                    crop_info = crop_data[crop]
                    qty = crop_info.get('qty_harvested', 'N/A')
                    unit = crop_info.get('unit', 'N/A')
                    print(f"    {crop}: {qty} {unit}")
                
                print()
            except json.JSONDecodeError:
                continue
    
    conn.close()
    
    print("\n=== DATABASE DESIGN RECOMMENDATIONS ===\n")
    print("Based on the analysis above, here are the key findings and recommendations:")
    print("1. Current structure allows one form_responses record to contain multiple crops")
    print("2. Field_boundaries table stores one boundary per record with one crop_type")
    print("3. Multiple boundaries can exist for the same farmer_id + crop_type combination")
    print("4. The farmer_id field provides the primary linking mechanism")
    print("5. JSON storage in form_responses provides flexibility but makes querying complex")

if __name__ == "__main__":
    analyze_database()