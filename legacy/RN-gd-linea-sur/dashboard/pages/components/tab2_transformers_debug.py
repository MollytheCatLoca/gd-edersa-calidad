"""
Tab 2 DEBUG: Raw Data Visualization for Transformers
This is a debug tab to see exactly what data we have before making it pretty
"""

from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc
import json
from pathlib import Path
from dashboard.pages.utils import get_data_manager, DataStatus

def render_transformers_tab():
    """Render the transformers debug tab - RAW DATA ONLY."""
    # Get data from data manager
    dm = get_data_manager()
    
    # Force reload to ensure we have latest data
    reload_result = dm.reload_data()
    print(f"DEBUG: Reload result: {reload_result}")
    
    # Get transformers data
    transformers_result = dm.get_transformers()
    print(f"DEBUG: Transformers result status: {transformers_result.status}")
    print(f"DEBUG: Transformers data type: {type(transformers_result.data)}")
    if transformers_result.data and isinstance(transformers_result.data, dict):
        print(f"DEBUG: Transformers data keys: {list(transformers_result.data.keys())[:5]}")
    transformers_data = transformers_result.data if transformers_result.data else {}
    
    # Get source from metadata
    data_source = transformers_result.meta.get("source", "UNKNOWN") if transformers_result.meta else "UNKNOWN"
    data_format = transformers_result.meta.get("format", "unknown") if transformers_result.meta else "unknown"
    
    # Get nodes data for reference
    nodes_result = dm.get_nodes()
    nodes_data = nodes_result.data if nodes_result.data else {}
    
    # Build sections
    sections = []
    
    # SECTION 1: Data Status
    status_section = html.Div([
        html.H4("1. DataManagerV2 Status", className="text-primary"),
        html.Pre(f"""
Transformers Data Status:
- Status: {transformers_result.status.value if transformers_result.status else 'Unknown'}
- Data Source: {data_source} {'⚠️ USING FALLBACK DATA - THIS SHOULD NOT HAPPEN!' if data_source == 'FALLBACK' else '✓ REAL DATA' if data_source == 'transformadores_detalle.json' else '❌ NO DATA' if data_source == 'none' else ''}
- Data Format: {data_format}
- Has Data: {bool(transformers_data)}
- Data Type: {type(transformers_data).__name__}
- Number of Transformers: {len(transformers_data) if transformers_data and isinstance(transformers_data, dict) else 0}
- Metadata: {json.dumps(transformers_result.meta, indent=2) if transformers_result.meta else 'None'}

Nodes Data Status:
- Status: {nodes_result.status.value if nodes_result.status else 'Unknown'}
- Has Data: {bool(nodes_data)}
- Number of Nodes: {len(nodes_data) if nodes_data else 0}
        """, className="bg-light p-3")
    ])
    sections.append(status_section)
    
    # SECTION 2: Raw Data Structure
    if transformers_data:
        # Show keys
        keys_list = list(transformers_data.keys()) if isinstance(transformers_data, dict) else []
        
        structure_section = html.Div([
            html.H4("2. Raw Data Structure", className="text-primary mt-4"),
            html.H5("Available Keys:"),
            html.Pre(json.dumps(keys_list, indent=2), className="bg-light p-3"),
            
            html.H5("Full Data Structure (limited to first 2 locations):"),
            html.Div([
                html.Pre(
                    json.dumps(
                        {k: transformers_data[k] for k in list(transformers_data.keys())[:2]},
                        indent=2,
                        ensure_ascii=False
                    )[:3000] + "...(truncated)",  # Limit display size
                    className="bg-light p-3",
                    style={"maxHeight": "400px", "overflowY": "scroll"}
                )
            ])
        ])
        sections.append(structure_section)
    else:
        sections.append(html.Div([
            html.H4("2. Raw Data Structure", className="text-primary mt-4"),
            html.Div("NO DATA AVAILABLE", className="alert alert-warning")
        ]))
    
    # SECTION 3: Parsed Data Analysis
    parsed_section = html.Div([
        html.H4("3. Parsed Data Analysis", className="text-primary mt-4")
    ])
    
    if transformers_data and isinstance(transformers_data, dict):
        # Count transformers
        count_summary = {
            "total_locations": len(transformers_data),
            "locations_with_single_transformer": 0,
            "locations_with_multiple_transformers": 0,
            "total_transformers": 0,
            "distribution_transformers": 0,
            "generation_transformers": 0,
            "power_transformers": 0,
            "small_transformers": 0
        }
        
        location_details = []
        
        for location_key, location_data in transformers_data.items():
            if not isinstance(location_data, dict):
                location_details.append(f"{location_key}: NOT A DICT - Type: {type(location_data).__name__}")
                continue
            
            location_info = {
                "key": location_key,
                "has_transformador_principal": "transformador_principal" in location_data,
                "has_transformadores": "transformadores" in location_data,
                "ubicacion": location_data.get("ubicacion", "N/A"),
                "tipo": location_data.get("tipo", "N/A")
            }
            
            # Count single transformer
            if "transformador_principal" in location_data:
                count_summary["locations_with_single_transformer"] += 1
                count_summary["total_transformers"] += 1
                
                t_data = location_data["transformador_principal"]
                tipo = t_data.get("tipo", "").lower()
                location_info["transformer_type"] = tipo
                location_info["power_mva"] = t_data.get("potencia_mva", "N/A")
                
                if "distribución" in tipo or "pequeño" in tipo:
                    count_summary["distribution_transformers"] += 1
                elif "potencia" in tipo:
                    count_summary["power_transformers"] += 1
                if "pequeño" in tipo:
                    count_summary["small_transformers"] += 1
            
            # Count multiple transformers
            if "transformadores" in location_data:
                count_summary["locations_with_multiple_transformers"] += 1
                tfmr_group = location_data["transformadores"]
                location_info["has_distribucion"] = "distribucion" in tfmr_group
                location_info["has_generacion"] = "generacion" in tfmr_group
                
                if "distribucion" in tfmr_group:
                    count_summary["total_transformers"] += 1
                    count_summary["distribution_transformers"] += 1
                
                if "generacion" in tfmr_group and isinstance(tfmr_group["generacion"], list):
                    gen_count = len(tfmr_group["generacion"])
                    count_summary["total_transformers"] += gen_count
                    count_summary["generation_transformers"] += gen_count
                    location_info["generation_count"] = gen_count
            
            location_details.append(location_info)
        
        parsed_section.children.extend([
            html.H5("Count Summary:"),
            html.Pre(json.dumps(count_summary, indent=2), className="bg-light p-3"),
            
            html.H5("Location Details:"),
            html.Div([
                html.Pre(
                    json.dumps(location_details, indent=2, ensure_ascii=False),
                    className="bg-light p-3",
                    style={"maxHeight": "400px", "overflowY": "scroll"}
                )
            ])
        ])
    else:
        parsed_section.children.append(
            html.Div("Cannot parse - no valid data", className="alert alert-warning")
        )
    
    sections.append(parsed_section)
    
    # SECTION 4: Debug Issues
    debug_section = html.Div([
        html.H4("4. Debug Information", className="text-primary mt-4")
    ])
    
    issues = []
    
    if not transformers_data:
        issues.append("No transformer data loaded")
    elif not isinstance(transformers_data, dict):
        issues.append(f"Transformer data is not a dict, it's: {type(transformers_data).__name__}")
    else:
        # Check for expected structure
        for location_key, location_data in transformers_data.items():
            if not isinstance(location_data, dict):
                issues.append(f"{location_key}: Expected dict, got {type(location_data).__name__}")
            else:
                if not ("transformador_principal" in location_data or "transformadores" in location_data):
                    if location_data.get("tipo") != "Seccionamiento":
                        issues.append(f"{location_key}: Missing both 'transformador_principal' and 'transformadores'")
    
    if not nodes_data:
        issues.append("No nodes data loaded (needed for location names)")
    
    if issues:
        debug_section.children.extend([
            html.H5("Issues Found:", className="text-danger"),
            html.Ul([html.Li(issue) for issue in issues])
        ])
    else:
        debug_section.children.append(
            html.Div("✓ No issues found - data structure looks good!", className="alert alert-success")
        )
    
    sections.append(debug_section)
    
    # SECTION 5: Sample Table Data
    if transformers_data and isinstance(transformers_data, dict) and len(transformers_data) > 0:
        table_section = html.Div([
            html.H4("5. Sample Table Data (First 3 Transformers)", className="text-primary mt-4"),
            html.P("This is how the data would look in a table:"),
        ])
        
        table_data = []
        count = 0
        
        for location_key, location_data in transformers_data.items():
            if not isinstance(location_data, dict):
                continue
                
            if "transformador_principal" in location_data:
                t_data = location_data["transformador_principal"]
                table_data.append({
                    "Location": location_data.get("ubicacion", location_key),
                    "Type": t_data.get("tipo", "N/A"),
                    "Power": f"{t_data.get('potencia_mva', 'N/A')} MVA",
                    "Voltage": t_data.get("relacion", "N/A"),
                    "Connection": t_data.get("conexion", "N/A")
                })
                count += 1
                if count >= 3:
                    break
        
        if table_data:
            table_section.children.append(
                html.Pre(json.dumps(table_data, indent=2, ensure_ascii=False), className="bg-light p-3")
            )
        else:
            table_section.children.append(
                html.Div("No table data could be extracted", className="alert alert-warning")
            )
        
        sections.append(table_section)
    
    # Main layout
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H3("🔍 DEBUG: Transformer Data Visualization", className="mb-3"),
                html.P("This debug view shows raw data from DataManagerV2", className="text-muted"),
                html.Hr()
            ])
        ]),
        
        # All sections
        html.Div(sections)
    ])


# Callbacks (if needed for interactivity)
# Currently no callbacks needed for debug view