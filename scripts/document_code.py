#!/usr/bin/env python3
"""
Script to identify and add documentation to Python code files.

This script helps identify classes and methods without proper docstrings
and can generate documentation templates for them.
"""

import os
import ast
import sys
import argparse
from typing import List, Tuple, Dict, Any, Optional

class DocStringVisitor(ast.NodeVisitor):
    """AST visitor that identifies missing or incomplete docstrings."""
    
    def __init__(self):
        """Initialize the visitor."""
        self.missing_docs = []
        self.current_path = []
        
    def visit_ClassDef(self, node):
        """Visit class definitions and check for docstrings."""
        self.current_path.append(node.name)
        has_docstring = ast.get_docstring(node) is not None
        
        if not has_docstring:
            self.missing_docs.append({
                'type': 'class',
                'name': node.name,
                'path': '.'.join(self.current_path),
                'lineno': node.lineno,
                'node': node
            })
        
        # Continue visiting the class body
        self.generic_visit(node)
        self.current_path.pop()
        
    def visit_FunctionDef(self, node):
        """Visit function definitions and check for docstrings."""
        # Skip special methods like __init__, __str__, etc.
        is_special = node.name.startswith('__') and node.name.endswith('__')
        
        # Check for decorator that might indicate property or abstract method
        decorators = [d.id for d in node.decorator_list 
                     if isinstance(d, ast.Name)]
        is_property = 'property' in decorators
        
        self.current_path.append(node.name)
        has_docstring = ast.get_docstring(node) is not None
        
        if not has_docstring and not (is_special and is_property):
            # Get argument info
            args = []
            for arg in node.args.args:
                if arg.arg != 'self' and arg.arg != 'cls':
                    args.append(arg.arg)
                    
            # Get return info
            returns = None
            if node.returns:
                if isinstance(node.returns, ast.Name):
                    returns = node.returns.id
                elif isinstance(node.returns, ast.Subscript):
                    # Handle typing annotations like List[str]
                    if isinstance(node.returns.value, ast.Name):
                        returns = node.returns.value.id
                    
            self.missing_docs.append({
                'type': 'function',
                'name': node.name,
                'path': '.'.join(self.current_path),
                'lineno': node.lineno,
                'args': args,
                'returns': returns,
                'node': node
            })
            
        # Continue visiting the function body
        self.generic_visit(node)
        self.current_path.pop()

def generate_docstring_template(item: Dict[str, Any]) -> str:
    """
    Generate a docstring template for a class or function.
    
    Args:
        item: Information about the class or function
    
    Returns:
        str: Docstring template
    """
    if item['type'] == 'class':
        return '    """\n    Class for handling {}.\n    """\n'.format(item['name'].lower())
    
    elif item['type'] == 'function':
        template = [
            '    """',
            '    {}.\n'.format(item['name'].replace('_', ' ').capitalize())
        ]
        
        # Add Args section if there are arguments
        if item['args']:
            template.append('    Args:')
            for arg in item['args']:
                template.append('        {}: Description of {}'.format(arg, arg))
            template.append('')
        
        # Add Returns section if the function doesn't return None
        if item['returns'] and item['returns'] != 'None':
            template.append('    Returns:')
            template.append('        {}: Description of return value'.format(item['returns']))
            template.append('')
        
        # Add Raises section as a placeholder
        template.append('    Raises:')
        template.append('        Exception: Description of when the exception is raised')
        
        template.append('    """')
        return '\n'.join(template)
    
    return ""

def analyze_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Analyze a Python file for missing documentation.
    
    Args:
        file_path: Path to the Python file
        
    Returns:
        List of items with missing documentation
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
        visitor = DocStringVisitor()
        visitor.visit(tree)
        return visitor.missing_docs
    except SyntaxError as e:
        print(f"Syntax error in {file_path}: {e}")
        return []

def analyze_directory(directory: str, extensions: List[str] = ['.py']) -> Dict[str, List[Dict[str, Any]]]:
    """
    Recursively analyze a directory for Python files with missing documentation.
    
    Args:
        directory: Directory path to analyze
        extensions: File extensions to include
        
    Returns:
        Dictionary mapping file paths to missing documentation items
    """
    results = {}
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                missing_docs = analyze_file(file_path)
                if missing_docs:
                    results[file_path] = missing_docs
    
    return results

def print_report(results: Dict[str, List[Dict[str, Any]]]):
    """
    Print a report of missing documentation.
    
    Args:
        results: Dictionary mapping file paths to missing documentation items
    """
    total_files = len(results)
    total_items = sum(len(items) for items in results.values())
    
    print(f"\nFound {total_items} missing docstrings in {total_files} files:\n")
    
    for file_path, items in sorted(results.items()):
        print(f"{os.path.relpath(file_path)}:")
        for item in sorted(items, key=lambda x: x['lineno']):
            print(f"  Line {item['lineno']}: {item['type']} {item['path']}")
        print()

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Identify and add documentation to Python code files.')
    parser.add_argument('path', help='Path to file or directory to analyze')
    parser.add_argument('--generate', action='store_true', help='Generate documentation templates')
    parser.add_argument('--extensions', default='.py', help='File extensions to analyze (comma-separated)')
    
    args = parser.parse_args()
    
    path = args.path
    extensions = args.extensions.split(',')
    
    if os.path.isfile(path):
        results = {path: analyze_file(path)}
    elif os.path.isdir(path):
        results = analyze_directory(path, extensions)
    else:
        print(f"Error: Path {path} does not exist")
        return 1
    
    print_report(results)
    
    if args.generate:
        for file_path, items in results.items():
            print(f"\nTemplate docstrings for {os.path.relpath(file_path)}:\n")
            for item in sorted(items, key=lambda x: x['lineno']):
                print(f"Line {item['lineno']}: {item['type']} {item['path']}")
                print(generate_docstring_template(item))
                print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 