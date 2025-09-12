import re

def validate_form_data(data):
    """Validate form data before saving to database"""
    errors = []
    
    # Required field validation
    required_fields = {
        'farmer_id': 'Farmer ID',
        'district': 'District',
        'village': 'Village',
        'season_year': 'Season/Year'
    }
    
    for field, label in required_fields.items():
        if not data.get(field) or data[field] == "Select..." or data[field] == "":
            errors.append(f"{label} is required")
    
    # Check if at least one crop is selected
    selected_crops = data.get('selected_crops', [])
    if not selected_crops:
        errors.append("At least one crop must be selected")
    
    # Specific validation rules
    if data.get('farmer_id'):
        if len(data['farmer_id'].strip()) < 3:
            errors.append("Farmer ID must be at least 3 characters long")
        if not re.match(r'^[a-zA-Z0-9\-_]+$', data['farmer_id']):
            errors.append("Farmer ID can only contain letters, numbers, hyphens, and underscores")
    
    if data.get('ea_code'):
        if not re.match(r'^[0-9]+$', data['ea_code']):
            errors.append("EA Code must contain only numbers")
    
    if data.get('season_year'):
        if not re.match(r'^\d{4}/\d{2,4}$', data['season_year']):
            errors.append("Season/Year must be in format YYYY/YY or YYYY/YYYY (e.g., 2024/25)")
    
    # Crop-specific validation for each selected crop
    crop_data = data.get('crop_data', {})
    selected_crops = data.get('selected_crops', [])
    
    for crop_type in selected_crops:
        crop_info = crop_data.get(crop_type, {})
        
        # Validate crop-specific required fields
        if crop_type == "Coconut":
            if crop_info.get('growth_mode') == "Select...":
                errors.append(f"Growth mode is required for {crop_type}")
        elif crop_type == "Cocoa":
            if crop_info.get('growth_mode') == "Select...":
                errors.append(f"Growth mode is required for {crop_type}")
        elif crop_type == "Breadfruit":
            if crop_info.get('growth_mode') == "Select...":
                errors.append(f"Growth mode is required for {crop_type}")
        elif crop_type == "Banana":
            if crop_info.get('banana_type') == "Select...":
                errors.append(f"Banana type is required for {crop_type}")
            if crop_info.get('growth_mode') == "Select...":
                errors.append(f"Growth mode is required for {crop_type}")
        elif crop_type == "Other":
            if not crop_info.get('other_crop_name'):
                errors.append(f"Crop name is required for {crop_type}")
        
        # Validate production fields for each crop
        if crop_info.get('qty_harvested') is not None:
            if crop_info['qty_harvested'] < 0:
                errors.append(f"Quantity harvested cannot be negative for {crop_type}")
            if crop_info['qty_harvested'] > 1000000:
                errors.append(f"Quantity harvested seems unrealistic for {crop_type} (max 1,000,000)")
        
        if crop_info.get('price_per_unit') is not None:
            if crop_info['price_per_unit'] < 0:
                errors.append(f"Price per unit cannot be negative for {crop_type}")
            if crop_info['price_per_unit'] > 10000:
                errors.append(f"Price per unit seems unrealistic for {crop_type} (max $10,000)")
        
        if crop_info.get('area_acres') is not None and crop_info['area_acres'] > 0:
            if crop_info['area_acres'] > 10000:
                errors.append(f"Area in acres seems unrealistic for {crop_type} (max 10,000 acres)")
        
        # Check production fields have units if quantity is provided
        if crop_info.get('qty_harvested') and crop_info.get('qty_harvested') > 0:
            if crop_info.get('unit') == "Select..." or not crop_info.get('unit'):
                errors.append(f"Unit is required when quantity harvested is provided for {crop_type}")
    
    # Return validation result
    if errors:
        return False, "; ".join(errors)
    else:
        return True, "Validation successful"

def validate_field_boundary(data):
    """Validate field boundary data before saving"""
    errors = []
    
    # Required fields
    if not data.get('field_name') or len(data['field_name'].strip()) < 1:
        errors.append("Field name is required")
    
    if not data.get('field_type') or data['field_type'] == "Select...":
        errors.append("Field type is required")
    
    if not data.get('coordinates') or len(data['coordinates']) < 3:
        errors.append("Field boundary must have at least 3 points")
    
    # Field name validation
    if data.get('field_name'):
        if len(data['field_name']) > 100:
            errors.append("Field name must be less than 100 characters")
        if not re.match(r'^[a-zA-Z0-9\s\-_\.]+$', data['field_name']):
            errors.append("Field name contains invalid characters")
    
    # Area validation
    if data.get('area_estimate'):
        if data['area_estimate'] <= 0:
            errors.append("Area estimate must be greater than 0")
        if data['area_estimate'] > 10000:
            errors.append("Area estimate seems unrealistic (max 10,000 acres)")
    
    # Notes length check
    if data.get('notes') and len(data['notes']) > 500:
        errors.append("Notes must be less than 500 characters")
    
    # Return validation result
    if errors:
        return False, "; ".join(errors)
    else:
        return True, "Validation successful"

def sanitize_input(text):
    """Sanitize text input to prevent basic security issues"""
    if not text:
        return ""
    
    # Remove potentially harmful characters
    sanitized = str(text).strip()
    
    # Remove HTML tags
    sanitized = re.sub(r'<[^>]+>', '', sanitized)
    
    # Remove SQL injection patterns (basic)
    dangerous_patterns = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)',
        r'(--|#|\/\*|\*\/)',
        r'(\bOR\b.*=.*\bOR\b)',
        r'(\bAND\b.*=.*\bAND\b)'
    ]
    
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
    
    return sanitized

def validate_coordinates(coordinates):
    """Validate coordinate data for field boundaries"""
    if not coordinates or not isinstance(coordinates, list):
        return False, "Invalid coordinates format"
    
    if len(coordinates) < 3:
        return False, "Minimum 3 coordinate points required"
    
    if len(coordinates) > 1000:
        return False, "Too many coordinate points (max 1000)"
    
    for coord in coordinates:
        if not isinstance(coord, list) or len(coord) != 2:
            return False, "Each coordinate must have latitude and longitude"
        
        try:
            lat, lng = float(coord[0]), float(coord[1])
            if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                return False, "Coordinates out of valid range"
        except (ValueError, TypeError):
            return False, "Coordinates must be valid numbers"
    
    return True, "Coordinates are valid"
