import streamlit as st

# Page configuration and widget key namespacing
PAGE_PREFIX = "view_data"

# Helper function for namespaced widget keys
def k(key_name):
    """Create a namespaced key for widgets to prevent state bleeding between pages."""
    return f"{PAGE_PREFIX}:{key_name}"

# Add cleanup function for any foreign state
def cleanup_foreign_keys():
    """Remove session state keys from other pages to prevent bleeding."""
    keys_to_remove = []
    for key in st.session_state.keys():
        if isinstance(key, str):
            # Remove namespaced keys from other pages
            if ":" in key and not key.startswith(f"{PAGE_PREFIX}:"):
                keys_to_remove.append(key)
            # Remove common component state patterns that can bleed (but not our own)
            elif not key.startswith(f"{PAGE_PREFIX}:") and any(pattern in key.lower() for pattern in [
                'folium', 'map_data', 'plotly', 'chart_', 'download_', 
                'dataframe_', 'table_', '_selection', '_zoom', '_center'
            ]):
                keys_to_remove.append(key)
    
    for key in keys_to_remove:
        del st.session_state[key]

# Cleanup any foreign state on page load
cleanup_foreign_keys()
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import folium
from streamlit_folium import st_folium




st.title("Agricultural Data Dashboard 📊")
st.markdown("Comprehensive view of collected agricultural data and insights")


def load_form_data():
    """Load form response data from database"""
    try:
        conn = sqlite3.connect('agricultural_data.db')
        df = pd.read_sql_query(
            """
            SELECT * FROM form_responses 
            ORDER BY submission_date DESC
        """, conn)
        conn.close()

        # Parse JSON form_data if it exists
        if not df.empty and 'form_data' in df.columns:
            # Expand JSON data into columns
            expanded_data = []
            for _, row in df.iterrows():
                try:
                    form_json = json.loads(row['form_data'])
                    # Combine basic fields with JSON data
                    combined_row = {
                        'id': row['id'],
                        'farmer_id': row['farmer_id'],
                        'district': row['district'],
                        'village': row['village'],
                        'ea_code': row['ea_code'],
                        'season_year': row['season_year'],
                        'crop_type': row['crop_type'],
                        'submission_date': row['submission_date'],
                        **form_json  # Expand all JSON fields
                    }
                    expanded_data.append(combined_row)
                except json.JSONDecodeError:
                    # If JSON parsing fails, use basic row data
                    expanded_data.append(row.to_dict())

            df = pd.DataFrame(expanded_data)

        return df
    except Exception as e:
        st.error(f"Error loading form data: {str(e)}")
        return pd.DataFrame()


def load_field_data():
    """Load field boundary data from database"""
    try:
        conn = sqlite3.connect('agricultural_data.db')
        df = pd.read_sql_query(
            """
            SELECT * FROM field_boundaries 
            WHERE coordinates IS NOT NULL AND coordinates != ''
            ORDER BY creation_date DESC
        """, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error loading field boundaries: {str(e)}")
        return pd.DataFrame()


# Load data
form_df = load_form_data()
field_df = load_field_data()

# Overview metrics
st.subheader("Data Overview")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Form Responses", len(form_df))
with col2:
    st.metric("Field Boundaries", len(field_df))
with col3:
    if not field_df.empty:
        total_mapped_area = field_df['area_estimate'].sum()
        st.metric("Total Mapped Area (ha)", f"{total_mapped_area:.1f}")
    else:
        st.metric("Total Mapped Area", "No data")
with col4:
    total_records = len(form_df) + len(field_df)
    st.metric("Total Records", total_records)
with col5:
    if not form_df.empty and not field_df.empty:
        st.metric("Data Status", "✅ Active")
    else:
        st.metric("Data Status", "⚠️ Limited")

# Form Data Analysis
if not form_df.empty:
    col1, col2 = st.columns(2)

    with col1:
        # Quantity harvested distribution
        if 'qty_harvested' in form_df.columns:
            fig2 = px.histogram(form_df,
                                x='qty_harvested',
                                title="Quantity Harvested Distribution",
                                nbins=10,
                                labels={
                                    'qty_harvested': 'Quantity Harvested',
                                    'count': 'Number of Records'
                                })
            st.plotly_chart(fig2, use_container_width=True, key=k("quantity_histogram_chart"))

    with col2:
        # Price vs Quantity relationship
        if 'price_per_unit' in form_df.columns and 'qty_harvested' in form_df.columns:
            fig4 = px.scatter(
                form_df,
                x='qty_harvested',
                y='price_per_unit',
                color='crop_type' if 'crop_type' in form_df.columns else None,
                title="Price vs Quantity Harvested",
                labels={
                    'qty_harvested': 'Quantity Harvested',
                    'price_per_unit': 'Price per Unit'
                })
            st.plotly_chart(fig4, use_container_width=True, key=k("price_quantity_scatter_chart"))

    # Recent submissions table
    st.subheader("Recent Form Submissions")
    if len(form_df) > 0:
        # Show last 10 submissions
        recent_forms = form_df.head(10)
        display_cols = [
            'farmer_id', 'district', 'village', 'crop_type', 'season_year',
            'submission_date'
        ]
        available_cols = [
            col for col in display_cols if col in recent_forms.columns
        ]

        if available_cols:
            st.dataframe(recent_forms[available_cols],
                         use_container_width=True,
                         hide_index=True,
                         key=k("recent_form_submissions_table"))
    else:
        st.info("No form submissions yet.")

else:
    st.info(
        "📝 No form responses available. Visit the Form Collection page to add data."
    )

# Field Data Analysis
if not field_df.empty:

    # Field boundaries table
    st.subheader("Recent Field Boundaries")
    display_cols = [
        'field_name', 'field_type', 'area_estimate', 'creation_date'
    ]
    available_cols = [col for col in display_cols if col in field_df.columns]

    if available_cols:
        recent_fields = field_df.head(10)
        st.dataframe(recent_fields[available_cols],
                     use_container_width=True,
                     hide_index=True,
                     key=k("recent_field_boundaries_table"))

else:
    st.info(
        "🗺️ No field boundaries mapped yet. Visit the Field Mapping page to add boundaries."
    )

# Field Boundaries Map
st.subheader("Field Boundaries Map")

# Create map centered on Upolu Island, Samoa
map_center = [-13.9167, -171.7500]  # Upolu Island coordinates
m = folium.Map(location=map_center, zoom_start=12, tiles=None)

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

# Define colors for field boundaries
colors = [
    'red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige',
    'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 'white', 'pink',
    'lightblue', 'lightgreen', 'gray', 'black', 'lightgray'
]

# Add all field boundaries to the map
if not field_df.empty:
    for idx, (_, row) in enumerate(field_df.iterrows()):
        try:
            # Check if coordinates exist and are not empty
            if pd.isna(row['coordinates']) or str(
                    row['coordinates']).strip() == '':
                continue

            coordinates = json.loads(str(row['coordinates']))

            # Validate coordinates structure
            if not coordinates or len(coordinates) < 3:
                continue

            # Convert coordinates to folium format [lat, lng]
            folium_coords = [[coord[1], coord[0]] for coord in coordinates]

            # Choose color based on field type or cycle through available colors
            color = colors[idx % len(colors)]

            # Safely get field attributes with defaults
            field_name = row.get('field_name', 'Unknown Field')
            field_type = row.get('field_type', 'Unknown')
            crop_type = row.get('crop_type', 'Unknown')
            area_estimate = row.get('area_estimate', 0)
            creation_date = str(row.get('creation_date', ''))[:10]

            # Add polygon to map
            folium.Polygon(locations=folium_coords,
                           popup=f"""
                <b>{field_name}</b><br>
                Type: {field_type}<br>
                Crop: {crop_type}<br>
                Area: {area_estimate} acres<br>
                Created: {creation_date}
                """,
                           tooltip=f"{field_name} ({field_type})",
                           color=color,
                           weight=2,
                           opacity=0.8,
                           fillColor=color,
                           fillOpacity=0.3).add_to(m)

        except (json.JSONDecodeError, KeyError, TypeError, IndexError) as e:
            # Silently skip invalid boundaries instead of showing warnings
            continue

# Add layer control
folium.LayerControl().add_to(m)

# Display the map
if not field_df.empty:
    st_folium(m, width=None, height=700, key=k("field_boundaries_map"))
else:
    st.info(
        "No field boundaries to display on map. Add boundaries from the Field Mapping page."
    )

# Export functionality
st.subheader("📤 Data Export")
col1, col2, col3 = st.columns(3)

with col1:
    if not form_df.empty:
        csv_form = form_df.to_csv(index=False)
        st.download_button(
            label="📄 Download Form Data (CSV)",
            data=csv_form,
            file_name=f"form_responses_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            key=k("download_form_data"))

with col2:
    if not field_df.empty:
        csv_field = field_df.to_csv(index=False)
        st.download_button(
            label="🗺️ Download Field Data (CSV)",
            data=csv_field,
            file_name=
            f"field_boundaries_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            key=k("download_field_data"))

with col3:
    if not form_df.empty or not field_df.empty:
        # Combined summary report
        summary_data = {
            'metric': [
                'Total Form Responses', 'Total Field Boundaries',
                'Data Collection Date'
            ],
            'value':
            [len(form_df),
             len(field_df),
             datetime.now().strftime('%Y-%m-%d')]
        }
        summary_df = pd.DataFrame(summary_data)
        csv_summary = summary_df.to_csv(index=False)
        st.download_button(
            label="📊 Download Summary Report",
            data=csv_summary,
            file_name=f"summary_report_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            key=k("download_summary_report"))

st.markdown("---")
