#!/usr/bin/env python3
"""
Check if any changes were detected
"""

import json
import sys
import argparse


def main():
    parser = argparse.ArgumentParser(description='Check if changes were detected')
    parser.add_argument('changes_file', help='Changes JSON file')
    
    args = parser.parse_args()
    
    with open(args.changes_file, 'r') as f:
        changes = json.load(f)
    
    has_changes = len(changes.get('models', {})) > 0
    
    if has_changes:
        print(f"Changes detected: {len(changes['models'])} models")
        sys.exit(0)
    else:
        print("No changes detected")
        sys.exit(1)


if __name__ == '__main__':
    main()
