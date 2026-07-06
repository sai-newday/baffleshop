#!/usr/bin/env python3
"""
Detect changes in dbt models and columns from PR diff
"""

import json
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Set
import re


def get_diff_files(base_ref: str, head_ref: str) -> Dict[str, str]:
    """Get diff between base and head refs"""
    try:
        result = subprocess.run(
            ["git", "diff", f"{base_ref}...{head_ref}", "--name-only"],
            capture_output=True,
            text=True,
            check=True
        )
        files = result.stdout.strip().split('\n')
        return {f: f for f in files if f and f.startswith('models/')}
    except subprocess.CalledProcessError as e:
        print(f"Error getting diff: {e}")
        return {}


def get_diff_content(base_ref: str, head_ref: str, file_path: str) -> str:
    """Get full diff content for a file"""
    try:
        result = subprocess.run(
            ["git", "diff", f"{base_ref}...{head_ref}", "--", file_path],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return ""


def parse_model_name(file_path: str) -> str:
    """Extract model name from file path"""
    # models/staging/stg_customers.sql -> stg_customers
    return Path(file_path).stem


def detect_column_changes(diff_content: str) -> Dict[str, str]:
    """Detect column additions/removals from SQL diff"""
    changes = {}
    
    # Find added columns (lines starting with +)
    added_lines = [line for line in diff_content.split('\n') if line.startswith('+') and not line.startswith('+++')]
    # Find removed columns (lines starting with -)
    removed_lines = [line for line in diff_content.split('\n') if line.startswith('-') and not line.startswith('---')]
    
    # Simple pattern matching for SQL column definitions
    # Pattern: column_name [type] [constraints]
    sql_column_pattern = re.compile(r'\b([a-z_][a-z0-9_]*)\s+(?:as\s+)?', re.IGNORECASE)
    
    for line in added_lines:
        if ',' in line or 'select' in line.lower():
            matches = sql_column_pattern.findall(line)
            for col in matches:
                if col.lower() not in ['as', 'from', 'where', 'with', 'select', 'cast']:
                    changes[col] = 'added'
    
    for line in removed_lines:
        if ',' in line or 'select' in line.lower():
            matches = sql_column_pattern.findall(line)
            for col in matches:
                if col.lower() not in ['as', 'from', 'where', 'with', 'select', 'cast']:
                    changes[col] = 'removed'
    
    return changes


def detect_model_changes(base_ref: str, head_ref: str, models_dir: str = 'models') -> Dict:
    """Detect all model and column changes"""
    changes = {
        'models': {},
        'timestamp': None
    }
    
    # Get changed files
    changed_files = get_diff_files(base_ref, head_ref)
    
    if not changed_files:
        return changes
    
    for file_path in changed_files.values():
        model_name = parse_model_name(file_path)
        diff_content = get_diff_content(base_ref, head_ref, file_path)
        
        # Determine if file was added, removed, or modified
        try:
            # Check if file exists in head
            head_exists = subprocess.run(
                ["git", "cat-file", "-e", f"{head_ref}:{file_path}"],
                capture_output=True,
                check=False
            ).returncode == 0
            
            # Check if file exists in base
            base_exists = subprocess.run(
                ["git", "cat-file", "-e", f"{base_ref}:{file_path}"],
                capture_output=True,
                check=False
            ).returncode == 0
            
            if head_exists and not base_exists:
                change_type = 'added'
            elif not head_exists and base_exists:
                change_type = 'removed'
            else:
                change_type = 'modified'
        except:
            change_type = 'modified'
        
        # Detect column changes
        column_changes = detect_column_changes(diff_content)
        
        changes['models'][model_name] = {
            'file_path': file_path,
            'change_type': change_type,
            'columns': column_changes if column_changes else None
        }
    
    return changes


def main():
    parser = argparse.ArgumentParser(description='Detect dbt model and column changes')
    parser.add_argument('--base-ref', required=True, help='Base git reference')
    parser.add_argument('--head-ref', required=True, help='Head git reference')
    parser.add_argument('--output', required=True, help='Output JSON file')
    
    args = parser.parse_args()
    
    changes = detect_model_changes(args.base_ref, args.head_ref)
    
    with open(args.output, 'w') as f:
        json.dump(changes, f, indent=2)
    
    print(f"Detected {len(changes['models'])} changed models")
    for model, details in changes['models'].items():
        print(f"  - {model}: {details['change_type']}")
        if details['columns']:
            for col, col_change in details['columns'].items():
                print(f"    - {col}: {col_change}")


if __name__ == '__main__':
    main()
