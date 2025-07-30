#!/usr/bin/env python3
"""
Update all database imports to use sparkjar_shared
"""
import os
import re
from pathlib import Path

def update_imports_in_file(file_path):
    """Update database imports in a single file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace database imports
    replacements = [
        (r'from database\.connection import', 'from sparkjar_shared.database.connection import'),
        (r'from database\.models import', 'from sparkjar_shared.database.models import'),
        (r'from sparkjar_shared.database import', 'from sparkjar_shared.database import'),
        (r'import database\.', 'import sparkjar_shared.database.'),
    ]
    
    modified = False
    for pattern, replacement in replacements:
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            modified = True
            content = new_content
    
    if modified:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Updated: {file_path}")
        return True
    return False

def main():
    """Update all Python files."""
    root_dir = Path('.')
    updated_count = 0
    
    # Skip virtual environments
    skip_dirs = {'.venv', '.venv_test', 'venv', '__pycache__'}
    
    for py_file in root_dir.rglob('*.py'):
        # Skip if in virtual environment
        if any(skip_dir in py_file.parts for skip_dir in skip_dirs):
            continue
            
        if update_imports_in_file(py_file):
            updated_count += 1
    
    print(f"\nTotal files updated: {updated_count}")

if __name__ == "__main__":
    main()