#!/usr/bin/env python3
"""
Analyze dbt lineage to determine blast radius using colibri lineage from manifest
"""

import json
import argparse
import sys
from typing import Dict, List, Set, Tuple


def load_manifest(manifest_file: str) -> Dict:
    """Load dbt manifest"""
    with open(manifest_file, 'r') as f:
        return json.load(f)


def load_catalog(catalog_file: str) -> Dict:
    """Load dbt catalog"""
    with open(catalog_file, 'r') as f:
        return json.load(f)


def load_colibri_lineage(manifest: Dict) -> Dict:
    """Extract column lineage from dbt manifest (colibri-generated)"""
    lineage = manifest.get('lineage', {})
    return {
        'edges': lineage.get('edges', []),
        'parents': lineage.get('parents', {}),
        'children': lineage.get('children', {})
    }


def get_affected_columns_from_colibri(
    source_model: str,
    changed_columns: List[str],
    target_model: str,
    colibri_lineage: Dict
) -> List[str]:
    """
    Get affected columns in target model using colibri lineage edges.
    Returns list of target columns that depend on changed source columns.
    """
    affected = set()
    
    if not colibri_lineage.get('edges'):
        return []
    
    # Find all edges from source model to target model
    for edge in colibri_lineage['edges']:
        # Check if this edge goes from changed source to target
        edge_source = edge.get('source', '')
        edge_target = edge.get('target', '')
        source_col = edge.get('sourceColumn', '')
        target_col = edge.get('targetColumn', '')
        
        # Match by model name (strip prefix if needed)
        source_model_match = source_model in edge_source or edge_source.endswith(source_model)
        target_model_match = target_model in edge_target or edge_target.endswith(target_model)
        
        if source_model_match and target_model_match and source_col in changed_columns:
            affected.add(target_col)
    
    return sorted(list(affected)) if affected else []


def get_model_name_from_id(node_id: str) -> str:
    """Extract model name from dbt node ID"""
    # e.g., "model.jaffleshop.stg_customers" -> "stg_customers"
    parts = node_id.split('.')
    return parts[-1] if parts else node_id


def get_downstream_nodes(manifest: Dict, node_id: str) -> Set[str]:
    """Get all downstream dependent nodes"""
    downstream = set()
    
    # Find all nodes that reference this node
    for other_id, node in manifest.get('nodes', {}).items():
        depends_on = node.get('depends_on', {})
        
        if node_id in depends_on.get('nodes', []):
            downstream.add(other_id)
            # Recursively get downstream
            downstream.update(get_downstream_nodes(manifest, other_id))
    
    return downstream


def get_model_columns(manifest: Dict, node_id: str) -> List[str]:
    """Get columns for a model from manifest"""
    node = manifest.get('nodes', {}).get(node_id, {})
    columns = node.get('columns', {})
    return sorted(list(columns.keys())) if columns else []


def analyze_impact(
    manifest: Dict,
    changes: Dict,
    catalog: Dict,
    colibri_lineage: Dict
) -> Dict:
    """Analyze impact of model/column changes using colibri column lineage"""
    
    impact_results = {
        'changed_assets': [],
        'direct_impacts': [],
        'recursive_impacts': [],
        'impacted_models': {},
        'summary': {
            'changed_models': 0,
            'changed_columns': 0,
            'directly_impacted_models': 0,
            'recursively_impacted_models': 0,
            'impacted_columns': 0
        }
    }
    
    changed_models = changes.get('models', {})
    
    if not changed_models:
        return impact_results
    
    # Track all impacted models and columns
    all_directly_impacted = set()
    all_recursively_impacted = set()
    all_impacted_columns = set()
    
    for model_name, model_info in changed_models.items():
        # Find matching node in manifest
        node_id = None
        for node_key, node in manifest.get('nodes', {}).items():
            if node.get('name') == model_name:
                node_id = node_key
                break
        
        if not node_id:
            continue
        
        # Record changed asset
        changed_cols = model_info.get('columns')
        impact_results['changed_assets'].append({
            'model': model_name,
            'change_type': model_info.get('change_type', 'modified'),
            'columns': changed_cols
        })
        
        impact_results['summary']['changed_models'] += 1
        if changed_cols:
            impact_results['summary']['changed_columns'] += len(changed_cols)
        
        # Get direct downstream
        downstream = get_downstream_nodes(manifest, node_id)
        
        # Separate direct from recursive
        direct_downstream = set()
        recursive_downstream = set()
        
        # Direct: nodes that directly depend on this
        for dep_id in manifest.get('nodes', {}).get(node_id, {}).get('dependents', []):
            direct_downstream.add(dep_id)
        
        # Recursive: everything else downstream
        recursive_downstream = downstream - direct_downstream
        
        # Get changed column names
        changed_column_list = list(changed_cols.keys()) if changed_cols else []
        
        # Record impacts - use colibri lineage for column accuracy
        for dep_id in direct_downstream:
            dep_node = manifest.get('nodes', {}).get(dep_id, {})
            dep_name = dep_node.get('name')
            if dep_name:
                all_directly_impacted.add(dep_name)
                
                # Get affected columns using colibri lineage
                affected_cols = get_affected_columns_from_colibri(
                    model_name, changed_column_list, dep_name, colibri_lineage
                )
                
                # If no specific columns found via lineage, use all columns as fallback
                if not affected_cols:
                    affected_cols = get_model_columns(manifest, dep_id)
                
                all_impacted_columns.update(affected_cols)
                
                impact_results['direct_impacts'].append({
                    'source_model': model_name,
                    'source_column': None,
                    'impacted_model': dep_name,
                    'impacted_columns': affected_cols
                })
        
        for dep_id in recursive_downstream:
            dep_node = manifest.get('nodes', {}).get(dep_id, {})
            dep_name = dep_node.get('name')
            if dep_name:
                all_recursively_impacted.add(dep_name)
                
                # Get affected columns using colibri lineage
                affected_cols = get_affected_columns_from_colibri(
                    model_name, changed_column_list, dep_name, colibri_lineage
                )
                
                # If no specific columns found via lineage, use all columns as fallback
                if not affected_cols:
                    affected_cols = get_model_columns(manifest, dep_id)
                
                all_impacted_columns.update(affected_cols)
                
                impact_results['recursive_impacts'].append({
                    'source_model': model_name,
                    'source_column': None,
                    'impacted_model': dep_name,
                    'impacted_columns': affected_cols
                })
    
    # Build aggregated impact by model
    for impact in impact_results['direct_impacts'] + impact_results['recursive_impacts']:
        model = impact['impacted_model']
        if model not in impact_results['impacted_models']:
            impact_results['impacted_models'][model] = {
                'columns': set(),
                'source_changes': []
            }
        
        impact_results['impacted_models'][model]['columns'].update(
            impact.get('impacted_columns', [])
        )
        impact_results['impacted_models'][model]['source_changes'].append({
            'model': impact['source_model'],
            'column': impact.get('source_column')
        })
    
    # Convert sets to lists and remove duplicates
    for model, info in impact_results['impacted_models'].items():
        info['columns'] = sorted(list(info['columns']))
    
    impact_results['summary']['directly_impacted_models'] = len(all_directly_impacted)
    impact_results['summary']['recursively_impacted_models'] = len(all_recursively_impacted)
    impact_results['summary']['impacted_columns'] = len(all_impacted_columns)
    
    return impact_results


def main():
    parser = argparse.ArgumentParser(description='Analyze dbt lineage impact')
    parser.add_argument('--changes-file', required=True, help='Changes JSON file')
    parser.add_argument('--manifest-file', required=True, help='Manifest JSON file')
    parser.add_argument('--catalog-file', required=True, help='Catalog JSON file')
    parser.add_argument('--output', required=True, help='Output JSON file')
    
    args = parser.parse_args()
    
    try:
        # Load files
        with open(args.changes_file, 'r') as f:
            changes = json.load(f)
        
        manifest = load_manifest(args.manifest_file)
        catalog = load_catalog(args.catalog_file)
        
        # Extract column lineage from colibri (in manifest)
        print("Extracting column-level lineage from dbt manifest (colibri)...")
        colibri_lineage = load_colibri_lineage(manifest)
        
        if colibri_lineage.get('edges'):
            print(f"  ✓ Column lineage extracted successfully")
            print(f"    - Lineage edges: {len(colibri_lineage['edges'])}")
            print(f"    - Models with parents: {len(colibri_lineage.get('parents', {}))}")
            print(f"    - Models with children: {len(colibri_lineage.get('children', {}))}")
        else:
            print("  ℹ No column lineage found (using model-level analysis)")
        
        # Analyze impact
        print("\nAnalyzing impact...")
        results = analyze_impact(manifest, changes, catalog, colibri_lineage)
        
        # Save results
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✓ Impact analysis complete")
        print(f"  - Changed models: {results['summary']['changed_models']}")
        print(f"  - Changed columns: {results['summary']['changed_columns']}")
        print(f"  - Directly impacted models: {results['summary']['directly_impacted_models']}")
        print(f"  - Recursively impacted models: {results['summary']['recursively_impacted_models']}")
        print(f"  - Total impacted columns: {results['summary']['impacted_columns']}")
        
    except Exception as e:
        print(f"Error during impact analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
