import streamlit as st
import sqlite3
import folium
from streamlit_folium import st_folium
import json
from datetime import datetime
from utils.validators import validate_form_data




# Page namespace and state cleanup
PAGE_PREFIX = "register"
k = lambda name: f"{PAGE_PREFIX}:{name}"

def cleanup_foreign_keys(current_page):
    """Remove session state keys from other pages to prevent UI bleeding"""
    keys_to_delete = []
    for key in st.session_state.keys():
        if isinstance(key, str) and ":" in key:
            if not key.startswith(f"{current_page}:"):
                keys_to_delete.append(key)
    
    for key in keys_to_delete:
        del st.session_state[key]

# Clean up state from other pages
cleanup_foreign_keys(PAGE_PREFIX)

st.title("Register Crops 🌾")
st.markdown(
    "Complete agricultural registration for your crops. Select crops below to enter production data and draw field boundaries."
)

# Initialize session state for form data
if k('form_submitted') not in st.session_state:
    st.session_state[k('form_submitted')] = False


def save_form_data(data):
    """Save form data to database"""
    try:
        conn = sqlite3.connect('agricultural_data.db')
        cursor = conn.cursor()

        # Convert data to JSON string for flexible storage
        crops_str = ", ".join(
            data['selected_crops']) if data.get('selected_crops') else "None"
        cursor.execute(
            '''
            INSERT INTO form_responses 
            (farmer_id, district, village, season_year, crop_type, form_data, submission_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''',
            (data['farmer_id'], data['district'],
             data['village'], data['season_year'], crops_str, json.dumps(data),
             datetime.now().isoformat()))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error saving production data: {str(e)}")
        return False


def save_field_boundary(field_data):
    """Save field boundary data to database"""
    try:
        conn = sqlite3.connect('agricultural_data.db')
        cursor = conn.cursor()

        cursor.execute(
            '''
            INSERT INTO field_boundaries 
            (farmer_id, field_name, field_type, crop_type, coordinates, area_estimate, notes, creation_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (field_data['farmer_id'], field_data['field_name'],
              field_data['field_type'], field_data['crop_type'],
              json.dumps(
                  field_data['coordinates']), field_data['area_estimate'],
              field_data['notes'], datetime.now().isoformat()))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error saving field boundary: {str(e)}")
        return False


# Define crop options and field structures
CROP_OPTIONS = ["Coconut", "Cocoa", "Breadfruit", "Banana", "Kava", "Other"]
UNITS = ["Kg", "Tonnes", "Each", "Pile", "Basket", "Packet", "Bundle"]
GROWTH_MODES = ["Single crop", "Mixed crop", "Both single & mixed"]
PLANTING_SOURCES = [
    "Own saved seed/seedlings", "Another household", "Market/shop",
    "Govt/extension", "NGO/project", "Company/association", "Other (specify)"
]
BANANA_TYPES = ["Fa'i palagi", "Fa'i Samoa", "Other (specify)"]
FIELD_TYPES = ["Cropland", "Pasture", "Orchard", "Fallow Land", "Other"]

# Identification Information (outside form for immediate response)
st.subheader("Identification")

col1, col2 = st.columns(2)

with col1:
    farmer_id = st.text_input("1. Farmer ID *",
                              placeholder="EA10208-HH0012",
                              key=k("farmer_id"))
    district = st.selectbox("2. District *", [
        "Select...", "Vaimauga 1", "Vaimauga 2", "Vaimauga 3", "Vaimauga 4",
        "Faleata 1", "Faleata 2", "Faleata 3", "Faleata 4", "Sagaga 1",
        "Sagaga 2", "Sagaga 3", "Sagaga 4", "A'ana Alofi 1", "A'ana Alofi 2",
        "A'ana Alofi 3", "A'ana Alofi 4"
    ],
                            key=k("district"))

with col2:
    village = st.text_input("3. Village *",
                            placeholder="e.g., Moataa, Vaipuna...",
                            key=k("village"))
    season_year = st.text_input("4. Season/Year *",
                                placeholder="2024/25",
                                key=k("season_year"))

st.subheader("Crop Selection")
st.write("**(Check all that apply)**")

# Create checkboxes for each crop (outside form for immediate response)
selected_crops = []
col1, col2, col3 = st.columns(3)

with col1:
    if st.checkbox("Coconut", key=k("crop_coconut")):
        selected_crops.append("Coconut")
    if st.checkbox("Cocoa", key=k("crop_cocoa")):
        selected_crops.append("Cocoa")
with col2:
    if st.checkbox("Breadfruit", key=k("crop_breadfruit")):
        selected_crops.append("Breadfruit")
    if st.checkbox("Banana", key=k("crop_banana")):
        selected_crops.append("Banana")
with col3:
    if st.checkbox("Kava", key=k("crop_kava")):
        selected_crops.append("Kava")
    if st.checkbox("Other", key=k("crop_other")):
        selected_crops.append("Other")

# Store all crop data and boundary data
all_crop_data = {}
all_boundary_data = {}

# Dynamic crop-specific fields for each selected crop (immediate display)
if selected_crops:
    for crop_type in selected_crops:
        st.subheader(f"{crop_type} Production and Field Registration")

        # Initialize crop data for this specific crop
        crop_data = {}

        if crop_type == "Coconut":
            col1, col2 = st.columns(2)
            with col1:
                crop_data['growth_mode'] = st.selectbox(
                    f"How is Coconut grown? *", ["Select..."] + GROWTH_MODES,
                    key=k("coconut_growth_mode"))
                crop_data['pest_rhino_beetle'] = st.radio(
                    "Affected by rhinoceros beetle (last 12 months)?",
                    ["Yes", "No"],
                    key=k("coconut_beetle"))
                crop_data['planted_last_12m'] = st.radio(
                    "Planted coconut (last 12 months)?", ["Yes", "No"],
                    key=k("coconut_planted"))
                crop_data['trees_harvested'] = st.number_input(
                    "Trees harvested (last 12 months)",
                    min_value=0,
                    step=1,
                    key=k("coconut_trees_harvested"))
            with col2:
                crop_data['planting_sources'] = st.multiselect(
                    "Source(s) of planting material",
                    PLANTING_SOURCES,
                    key=k("coconut_sources"))
                st.write("**Trees by age group:**")
                crop_data['age_0_5'] = st.number_input("0–5 years (count)",
                                                       min_value=0,
                                                       step=1,
                                                       key=k("coconut_age_0_5"))
                crop_data['age_6_10'] = st.number_input(
                    "6–10 years (count)",
                    min_value=0,
                    step=1,
                    key=k("coconut_age_6_10"))
                crop_data['age_11_20'] = st.number_input(
                    "11–20 years (count)",
                    min_value=0,
                    step=1,
                    key=k("coconut_age_11_20"))
                crop_data['age_21_30'] = st.number_input(
                    "21–30 years (count)",
                    min_value=0,
                    step=1,
                    key=k("coconut_age_21_30"))
                crop_data['age_31_plus'] = st.number_input(
                    "31+ years (count)",
                    min_value=0,
                    step=1,
                    key=k("coconut_age_31_plus"))

        elif crop_type == "Cocoa":
            col1, col2 = st.columns(2)
            with col1:
                crop_data['growth_mode'] = st.selectbox(
                    "How is Cocoa grown? *", ["Select..."] + GROWTH_MODES,
                    key=k("cocoa_growth_mode"))
                crop_data['disease_mosaic'] = st.radio(
                    "Cocoa mosaic disease (last 12 months)?", ["Yes", "No"],
                    key=k("cocoa_disease"))
                crop_data['planted_last_12m'] = st.radio(
                    "Planted cocoa (last 12 months)?", ["Yes", "No"],
                    key=k("cocoa_planted"))
            with col2:
                crop_data['planting_sources'] = st.multiselect(
                    "Source(s) of planting material",
                    PLANTING_SOURCES,
                    key=k("cocoa_sources"))
                st.write("**Trees by age group:**")
                crop_data['age_0_2'] = st.number_input("0–2 years (count)",
                                                       min_value=0,
                                                       step=1,
                                                       key=k("cocoa_age_0_2"))
                crop_data['age_3_5'] = st.number_input("3–5 years (count)",
                                                       min_value=0,
                                                       step=1,
                                                       key=k("cocoa_age_3_5"))
                crop_data['age_6_10'] = st.number_input("6–10 years (count)",
                                                        min_value=0,
                                                        step=1,
                                                        key=k("cocoa_age_6_10"))
                crop_data['age_11_20'] = st.number_input(
                    "11–20 years (count)",
                    min_value=0,
                    step=1,
                    key=k("cocoa_age_11_20"))
                crop_data['age_21_30'] = st.number_input(
                    "21–30 years (count)",
                    min_value=0,
                    step=1,
                    key=k("cocoa_age_21_30"))
                crop_data['age_31_plus'] = st.number_input(
                    "31+ years (count)",
                    min_value=0,
                    step=1,
                    key=k("cocoa_age_31_plus"))

        elif crop_type == "Breadfruit":
            col1, col2 = st.columns(2)
            with col1:
                crop_data['growth_mode'] = st.selectbox(
                    "How is Breadfruit grown? *", ["Select..."] + GROWTH_MODES,
                    key=k("breadfruit_growth_mode"))
                crop_data['trees_single_crop'] = st.number_input(
                    "Breadfruit trees (single crop)",
                    min_value=0,
                    step=1,
                    key=k("breadfruit_trees_single"))
                crop_data['planted_last_12m'] = st.radio(
                    "Planted breadfruit (last 12 months)?", ["Yes", "No"],
                    key=k("breadfruit_planted"))
            with col2:
                crop_data['trees_harvested'] = st.number_input(
                    "Trees harvested (last 12 months)",
                    min_value=0,
                    step=1,
                    key=k("breadfruit_trees_harvested"))
                crop_data['planting_sources'] = st.multiselect(
                    "Source(s) of planting material",
                    PLANTING_SOURCES,
                    key=k("breadfruit_sources"))
                crop_data['area_acres'] = st.number_input(
                    "Area planted (acres)",
                    min_value=0.0,
                    step=0.01,
                    key=k("breadfruit_area"))

        elif crop_type == "Banana":
            col1, col2 = st.columns(2)
            with col1:
                crop_data['banana_type'] = st.selectbox(
                    "Banana type *", ["Select..."] + BANANA_TYPES,
                    key=k("banana_type"))
                crop_data['growth_mode'] = st.selectbox(
                    "How is Banana grown? *", ["Select..."] + GROWTH_MODES,
                    key=k("banana_growth_mode"))
                crop_data['plants_single_crop'] = st.number_input(
                    "Banana plants/suckers (single crop)",
                    min_value=0,
                    step=1,
                    key=k("banana_plants"))
            with col2:
                crop_data['area_acres'] = st.number_input(
                    "Area planted (acres)",
                    min_value=0.0,
                    step=0.01,
                    key=k("banana_area"))

        elif crop_type == "Kava":
            col1, col2 = st.columns(2)
            with col1:
                crop_data['planted_last_12m'] = st.radio(
                    "Planted kava (last 12 months)?", ["Yes", "No"],
                    key=k("kava_planted"))
                crop_data['plants_harvested'] = st.number_input(
                    "Plants harvested (last 12 months)",
                    min_value=0,
                    step=1,
                    key=k("kava_plants_harvested"))
            with col2:
                crop_data['planting_sources'] = st.multiselect(
                    "Source(s) of planting material",
                    PLANTING_SOURCES,
                    key=k("kava_sources"))

        elif crop_type == "Other":
            col1, col2 = st.columns(2)
            with col1:
                crop_data['other_crop_name'] = st.text_input(
                    "Crop name *",
                    placeholder="e.g., Mango, Citrus...",
                    key=k("other_crop_name"))
                crop_data['plants_growing'] = st.number_input(
                    "Plants growing (count)",
                    min_value=0,
                    step=1,
                    key=k("other_plants_growing"))
            with col2:
                crop_data['plants_harvested'] = st.number_input(
                    "Plants harvested (last 12 months)",
                    min_value=0,
                    step=1,
                    key=k("other_plants_harvested"))

        # Production fields for each crop
        st.write("**Production Information:**")
        col1, col2 = st.columns(2)
        with col1:
            crop_data['qty_harvested'] = st.number_input(
                "Quantity harvested (last 12 months) *",
                min_value=0.0,
                step=0.1,
                key=k(f"{crop_type.lower().replace(' ', '_')}_qty"))
            crop_data['unit'] = st.selectbox(
                "Unit of measure *", ["Select..."] + UNITS,
                key=k(f"{crop_type.lower().replace(' ', '_')}_unit"))
        with col2:
            crop_data['price_per_unit'] = st.number_input(
                "Average price per unit (last 12 months)",
                min_value=0.0,
                step=0.01,
                key=k(f"{crop_type.lower().replace(' ', '_')}_price"))

        # Store this crop's data
        all_crop_data[crop_type] = crop_data

        # Field boundary mapping section
        st.write(f"**Draw the boundaries of your {crop_type} fields**")
        st.info(
            "**Instructions:** Use the drawing tools on the map to draw a shape around each of your field boundaries for the given crop type. Click on the ⬟ icon in the toolbar to start drawing."
        )

        # Initialize the map for this crop
        map_key = f"map_center_{crop_type.lower()}"
        if map_key not in st.session_state:
            # Default to Upolu Island, Samoa - agricultural AOI
            st.session_state[map_key] = [-13.9167, -171.7500]
            st.session_state[f"map_zoom_{crop_type.lower()}"] = 12

        # Create the base map with satellite imagery
        m = folium.Map(
            location=st.session_state[map_key],
            zoom_start=st.session_state[f"map_zoom_{crop_type.lower()}"],
            tiles=None)

        # Add satellite tile layer
        folium.TileLayer(
            tiles=
            'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Satellite',
            overlay=False,
            control=True).add_to(m)

        # Add OpenStreetMap layer as backup
        folium.TileLayer(tiles='OpenStreetMap',
                         name='Street Map',
                         overlay=False,
                         control=True).add_to(m)

        # Add drawing tools
        from folium import plugins
        draw = plugins.Draw(
            export=True,
            draw_options={
                'polyline': False,
                'polygon': True,
                'circle': False,
                'rectangle': False,
                'marker': False,
                'circlemarker': False,
            },
            edit_options={'poly': {
                'allowIntersection': False
            }})
        draw.add_to(m)

        # Add layer control
        folium.LayerControl().add_to(m)

        # Display the map
        map_data = st_folium(m,
                             width=None,
                             height=500,
                             returned_objects=["all_drawings"],
                             key=k(f"map_{crop_type.lower()}"))

        # Process drawn polygons
        boundary_data = []
        total_area_hectares = 0
        num_fields = 0

        if map_data['all_drawings'] and len(map_data['all_drawings']) > 0:
            # Process all polygons for this crop
            polygons = [
                drawing for drawing in map_data['all_drawings']
                if drawing['geometry']['type'] == 'Polygon'
            ]
            num_fields = len(polygons)

            if num_fields > 0:

                # Calculate area for each polygon
                def calculate_polygon_area_hectares(coords):
                    """Calculate polygon area in hectares using shoelace formula with lat/lng conversion"""
                    n = len(coords)
                    if n < 3:
                        return 0

                    # Shoelace formula for area in square degrees
                    area_sq_degrees = 0
                    for i in range(n):
                        j = (i + 1) % n
                        area_sq_degrees += coords[i][0] * coords[j][1]
                        area_sq_degrees -= coords[j][0] * coords[i][1]
                    area_sq_degrees = abs(area_sq_degrees) / 2

                    # Convert to hectares (approximate for Samoa latitude ~-13.9°)
                    # 1 degree lat ≈ 111 km, 1 degree lng ≈ 111 km * cos(lat)
                    lat_avg = sum(coord[1] for coord in coords) / len(coords)
                    import math
                    meters_per_degree_lat = 111000  # meters per degree latitude
                    meters_per_degree_lng = 111000 * math.cos(
                        math.radians(lat_avg))  # meters per degree longitude

                    # Convert square degrees to square meters
                    area_sq_meters = area_sq_degrees * meters_per_degree_lat * meters_per_degree_lng

                    # Convert to hectares (1 hectare = 10,000 m²)
                    area_hectares = area_sq_meters / 10000
                    return area_hectares

                # Process each polygon
                for i, polygon in enumerate(polygons):
                    coordinates = polygon['geometry']['coordinates'][0]
                    area_ha = calculate_polygon_area_hectares(coordinates)
                    total_area_hectares += area_ha

                    # Store boundary data for this polygon
                    boundary_data.append({
                        'field_name': f"{crop_type} Field {i+1}",
                        'field_type': "Cropland",
                        'coordinates': coordinates,
                        'area_estimate': area_ha,
                        'notes': ""
                    })

                # Display summary metrics
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(f"Number of {crop_type} fields", num_fields)
                with col2:
                    st.metric("Total area (ha)", f"{total_area_hectares:.2f}")

                # Store all boundary data for this crop
                all_boundary_data[crop_type] = boundary_data
        else:
            st.info(
                "Draw a polygon on the map to define field boundaries for this crop."
            )

        st.divider()  # Visual separator between crops

# Submit button (only show if crops are selected)
if selected_crops:
    if st.button("Submit Production Data & Field Boundaries", type="primary"):
        submitted = True
    else:
        submitted = False
else:
    submitted = False

if submitted:
    # Collect form data
    form_data = {
        'farmer_id': farmer_id,
        'district': district,
        'village': village,
        'season_year': season_year,
        'selected_crops': selected_crops,
        'crop_data': all_crop_data  # Include all crop-specific data
    }

    # Validate form data
    is_valid, error_message = validate_form_data(form_data)

    if is_valid:
        # Save production data
        production_saved = save_form_data(form_data)

        # Save boundary data for each crop that has it
        boundaries_saved = []
        total_boundaries_saved = 0
        for crop_type, boundary_list in all_boundary_data.items():
            if boundary_list:  # Check if list is not empty
                crop_fields_saved = 0
                for boundary_info in boundary_list:
                    field_data = {
                        'farmer_id': farmer_id,
                        'field_name': boundary_info['field_name'],
                        'field_type': boundary_info['field_type'],
                        'crop_type': crop_type,
                        'coordinates': boundary_info['coordinates'],
                        'area_estimate': boundary_info['area_estimate'],
                        'notes': boundary_info['notes']
                    }
                    if save_field_boundary(field_data):
                        crop_fields_saved += 1
                        total_boundaries_saved += 1
                if crop_fields_saved > 0:
                    boundaries_saved.append(crop_type)

        if production_saved:
            st.success("✅ Data submitted successfully!")

            # Show balloons animation
            st.balloons()
            st.session_state[k('form_submitted')] = True
        else:
            st.error("❌ Failed to submit production data. Please try again.")
    else:
        st.error(f"❌ {error_message}")

# Post-submission options
if st.session_state[k('form_submitted')]:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Retract & Edit", type="secondary"):
            st.session_state[k('form_submitted')] = False
            st.rerun()
    with col2:
        if st.button("Submit Another Entry"):
            # Clear all namespaced form data for fresh entry
            keys_to_delete = []
            for key in st.session_state.keys():
                if isinstance(key, str) and key.startswith(f"{PAGE_PREFIX}:"):
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                del st.session_state[key]

            st.session_state[k('form_submitted')] = False
            st.rerun()

st.markdown("---")
