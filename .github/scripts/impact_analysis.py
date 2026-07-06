#!/usr/bin/env python3
"""
Analyze dbt lineage to determine blast radius
"""

import json
import argparse
import subprocess
import sys
from typing import Dict, List, Set
from pathlib import Path


def load_manifest(manifest_file: str) -> Dict:
    """Load dbt manifest"""
    with open(manifest_file, 'r') as f:
        return json.load(f)


def load_catalog(catalog_file: str) -> Dict:
    """Load dbt catalog"""
    with open(catalog_file, 'r') as f:
        return json.load(f)


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
    return list(columns.keys()) if columns else []


def analyze_impact(
    manifest: Dict,
    changes: Dict,
    catalog: Dict
) -> Dict:
    """Analyze impact of model/column changes"""
    
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
    all_impacted_columns = {}
    
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
        impact_results['changed_assets'].append({
            'model': model_name,
            'change_type': model_info.get('change_type', 'modified'),
            'columns': model_info.get('columns')
        })
        
        impact_results['summary']['changed_models'] += 1
        if model_info.get('columns'):
            impact_results['summary']['changed_columns'] += len(model_info['columns'])
        
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
        
        # Record impacts
        for dep_id in direct_downstream:
            dep_node = manifest.get('nodes', {}).get(dep_id, {})
            dep_name = dep_node.get('name')
            if dep_name:
                all_directly_impacted.add(dep_name)
                impact_results['direct_impacts'].append({
                    'source_model': model_name,
                    'source_column': None,
                    'impacted_model': dep_name,
                    'impacted_columns': get_model_columns(manifest, dep_id)
                })
        
        for dep_id in recursive_downstream:
            dep_node = manifest.get('nodes', {}).get(dep_id, {})
            dep_name = dep_node.get('name')
            if dep_name:
                all_recursively_impacted.add(dep_name)
                impact_results['recursive_impacts'].append({
                    'source_model': model_name,
                    'source_column': None,
                    'impacted_model': dep_name,
                    'impacted_columns': get_model_columns(manifest, dep_id)
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
    impact_results['summary']['impacted_columns'] = len(set(
        col for cols in all_impacted_columns.values() for col in cols
    ))
    
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
        
        # Analyze impact
        results = analyze_impact(manifest, changes, catalog)
        
        # Save results
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Impact analysis complete")
        print(f"  Changed models: {results['summary']['changed_models']}")
        print(f"  Changed columns: {results['summary']['changed_columns']}")
        print(f"  Directly impacted models: {results['summary']['directly_impacted_models']}")
        print(f"  Recursively impacted models: {results['summary']['recursively_impacted_models']}")
        
    except Exception as e:
        print(f"Error during impact analysis: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
