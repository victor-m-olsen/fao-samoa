import sqlite3
import json
import pandas as pd
from typing import Dict, List, Any, Optional

class ProductionBoundaryLinker:
    """
    Class to demonstrate linking production data with plot boundaries
    using the existing database schema.
    """
    
    def __init__(self, db_path: str = 'agricultural_data.db'):
        self.db_path = db_path
    
    def get_crop_production_data(self, farmer_id: str, crop_type: str) -> Optional[Dict]:
        """Extract specific crop production data from JSON structure"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT form_data, season_year, submission_date 
                FROM form_responses 
                WHERE farmer_id = ?
            """, (farmer_id,))
            
            result = cursor.fetchone()
            if not result:
                return None
            
            form_data = json.loads(result[0])
            crop_data = form_data.get('crop_data', {})
            
            if crop_type not in crop_data:
                return None
            
            production_data = crop_data[crop_type].copy()
            production_data.update({
                'season_year': result[1],
                'submission_date': result[2],
                'farmer_id': farmer_id,
                'crop_type': crop_type
            })
            
            return production_data
            
        except (json.JSONDecodeError, Exception) as e:
            print(f"Error extracting crop data: {e}")
            return None
        finally:
            conn.close()
    
    def get_field_boundaries_for_crop(self, farmer_id: str, crop_type: str) -> List[Dict]:
        """Get all field boundaries for a specific farmer+crop combination"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, field_name, field_type, coordinates, 
                       area_estimate, notes, creation_date, crop_type
                FROM field_boundaries 
                WHERE farmer_id = ? AND crop_type = ?
                ORDER BY creation_date
            """, (farmer_id, crop_type))
            
            boundaries = []
            for row in cursor.fetchall():
                boundary = {
                    'id': row[0],
                    'field_name': row[1],
                    'field_type': row[2],
                    'coordinates': json.loads(row[3]) if row[3] else [],
                    'area_estimate': row[4],
                    'notes': row[5],
                    'creation_date': row[6],
                    'crop_type': row[7]
                }
                boundaries.append(boundary)
            
            return boundaries
            
        except Exception as e:
            print(f"Error retrieving boundaries: {e}")
            return []
        finally:
            conn.close()
    
    def link_production_to_boundaries(self, farmer_id: str, crop_type: str) -> Dict[str, Any]:
        """
        Link production data with field boundaries for a specific farmer+crop combination
        """
        production_data = self.get_crop_production_data(farmer_id, crop_type)
        boundaries = self.get_field_boundaries_for_crop(farmer_id, crop_type)
        
        if not production_data:
            return {
                'status': 'no_production_data',
                'farmer_id': farmer_id,
                'crop_type': crop_type,
                'boundaries': boundaries
            }
        
        # Calculate aggregated metrics
        total_area = sum([b['area_estimate'] for b in boundaries if b['area_estimate']])
        total_fields = len(boundaries)
        
        # Calculate yield per acre if possible
        yield_per_acre = None
        if total_area > 0 and production_data.get('qty_harvested'):
            yield_per_acre = production_data['qty_harvested'] / total_area
        
        return {
            'status': 'linked',
            'farmer_id': farmer_id,
            'crop_type': crop_type,
            'production_data': production_data,
            'field_boundaries': boundaries,
            'summary_metrics': {
                'total_fields': total_fields,
                'total_area_acres': total_area,
                'quantity_harvested': production_data.get('qty_harvested', 0),
                'harvest_unit': production_data.get('unit', 'N/A'),
                'yield_per_acre': yield_per_acre,
                'price_per_unit': production_data.get('price_per_unit', 0),
                'total_value': (production_data.get('qty_harvested', 0) * 
                              production_data.get('price_per_unit', 0))
            }
        }
    
    def get_all_farmer_crop_links(self) -> List[Dict[str, Any]]:
        """Get all possible farmer+crop combinations and their linking status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all farmer+crop combinations from production data
        cursor.execute("SELECT farmer_id, form_data FROM form_responses")
        production_combinations = set()
        
        for row in cursor.fetchall():
            farmer_id = row[0]
            try:
                form_data = json.loads(row[1])
                selected_crops = form_data.get('selected_crops', [])
                for crop in selected_crops:
                    production_combinations.add((farmer_id, crop))
            except json.JSONDecodeError:
                continue
        
        # Get all farmer+crop combinations from boundary data
        cursor.execute("SELECT DISTINCT farmer_id, crop_type FROM field_boundaries")
        boundary_combinations = set(cursor.fetchall())
        
        conn.close()
        
        # Create comprehensive linking analysis
        all_combinations = production_combinations.union(boundary_combinations)
        results = []
        
        for farmer_id, crop_type in all_combinations:
            has_production = (farmer_id, crop_type) in production_combinations
            has_boundaries = (farmer_id, crop_type) in boundary_combinations
            
            if has_production and has_boundaries:
                # Full linking possible
                link_result = self.link_production_to_boundaries(farmer_id, crop_type)
                results.append(link_result)
            elif has_production:
                # Production only
                production_data = self.get_crop_production_data(farmer_id, crop_type)
                results.append({
                    'status': 'production_only',
                    'farmer_id': farmer_id,
                    'crop_type': crop_type,
                    'production_data': production_data,
                    'field_boundaries': []
                })
            else:
                # Boundaries only
                boundaries = self.get_field_boundaries_for_crop(farmer_id, crop_type)
                results.append({
                    'status': 'boundaries_only',
                    'farmer_id': farmer_id,
                    'crop_type': crop_type,
                    'production_data': None,
                    'field_boundaries': boundaries
                })
        
        return results
    
    def generate_dashboard_data(self) -> Dict[str, Any]:
        """Generate comprehensive dashboard data showing all linkages"""
        all_links = self.get_all_farmer_crop_links()
        
        # Categorize results
        fully_linked = [r for r in all_links if r['status'] == 'linked']
        production_only = [r for r in all_links if r['status'] == 'production_only']
        boundaries_only = [r for r in all_links if r['status'] == 'boundaries_only']
        
        # Calculate summary statistics
        total_production_records = len([r for r in all_links if r.get('production_data')])
        total_boundary_records = sum([len(r['field_boundaries']) for r in all_links])
        
        # Crop-wise analysis
        crop_analysis = {}
        for result in fully_linked:
            crop = result['crop_type']
            if crop not in crop_analysis:
                crop_analysis[crop] = {
                    'farmers': set(),
                    'total_area': 0,
                    'total_production': 0,
                    'total_value': 0,
                    'fields': 0
                }
            
            metrics = result['summary_metrics']
            crop_analysis[crop]['farmers'].add(result['farmer_id'])
            crop_analysis[crop]['total_area'] += metrics.get('total_area_acres', 0)
            crop_analysis[crop]['total_production'] += metrics.get('quantity_harvested', 0)
            crop_analysis[crop]['total_value'] += metrics.get('total_value', 0)
            crop_analysis[crop]['fields'] += metrics.get('total_fields', 0)
        
        # Convert sets to counts
        for crop in crop_analysis:
            crop_analysis[crop]['farmers'] = len(crop_analysis[crop]['farmers'])
        
        return {
            'summary': {
                'total_combinations': len(all_links),
                'fully_linked': len(fully_linked),
                'production_only': len(production_only),
                'boundaries_only': len(boundaries_only),
                'total_production_records': total_production_records,
                'total_boundary_records': total_boundary_records,
                'linking_success_rate': len(fully_linked) / len(all_links) if all_links else 0
            },
            'fully_linked_data': fully_linked,
            'production_only_data': production_only,
            'boundaries_only_data': boundaries_only,
            'crop_analysis': crop_analysis
        }

def demonstrate_linking():
    """Demonstrate the linking functionality with current data"""
    linker = ProductionBoundaryLinker()
    
    print("=== PRODUCTION-BOUNDARY LINKING DEMONSTRATION ===\n")
    
    # Generate dashboard data
    dashboard_data = linker.generate_dashboard_data()
    
    print("SUMMARY STATISTICS:")
    summary = dashboard_data['summary']
    for key, value in summary.items():
        if key == 'linking_success_rate':
            print(f"  {key}: {value:.1%}")
        else:
            print(f"  {key}: {value}")
    
    print(f"\nFULLY LINKED FARMER+CROP COMBINATIONS ({len(dashboard_data['fully_linked_data'])}):")
    for result in dashboard_data['fully_linked_data']:
        metrics = result['summary_metrics']
        print(f"\n  {result['farmer_id']} - {result['crop_type']}:")
        print(f"    Fields: {metrics['total_fields']}")
        print(f"    Total Area: {metrics['total_area_acres']} acres")
        print(f"    Production: {metrics['quantity_harvested']} {metrics['harvest_unit']}")
        if metrics['yield_per_acre']:
            print(f"    Yield per Acre: {metrics['yield_per_acre']:.2f} {metrics['harvest_unit']}/acre")
        print(f"    Total Value: ${metrics['total_value']:.2f}")
    
    print(f"\nPRODUCTION-ONLY DATA ({len(dashboard_data['production_only_data'])}):")
    for result in dashboard_data['production_only_data']:
        if result['production_data']:
            prod = result['production_data']
            qty = prod.get('qty_harvested', 'N/A')
            unit = prod.get('unit', 'N/A')
            print(f"  {result['farmer_id']} - {result['crop_type']}: {qty} {unit} (NO BOUNDARIES)")
    
    print(f"\nBOUNDARY-ONLY DATA ({len(dashboard_data['boundaries_only_data'])}):")
    for result in dashboard_data['boundaries_only_data']:
        boundary_count = len(result['field_boundaries'])
        total_area = sum([b['area_estimate'] for b in result['field_boundaries'] if b['area_estimate']])
        print(f"  {result['farmer_id']} - {result['crop_type']}: {boundary_count} fields, {total_area} acres (NO PRODUCTION)")
    
    print(f"\nCROP ANALYSIS:")
    for crop, analysis in dashboard_data['crop_analysis'].items():
        print(f"\n  {crop}:")
        print(f"    Farmers: {analysis['farmers']}")
        print(f"    Total Fields: {analysis['fields']}")
        print(f"    Total Area: {analysis['total_area']:.1f} acres")
        print(f"    Total Production: {analysis['total_production']:.1f}")
        print(f"    Total Value: ${analysis['total_value']:.2f}")
        if analysis['total_area'] > 0:
            avg_yield = analysis['total_production'] / analysis['total_area']
            print(f"    Average Yield per Acre: {avg_yield:.2f}")

if __name__ == "__main__":
    demonstrate_linking()