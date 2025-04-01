#!/usr/bin/env python3

from prompits.pools.SQLitePool import SQLitePool
import json

def main():
    # Create a SQLitePool
    pool = SQLitePool("test_pool", "Test SQLite Pool", "test.db")
    
    # Get the JSON representation
    json_data = pool.ToJson()
    
    # Check if practices are included
    print("SQLitePool ToJson output:")
    print(json.dumps(json_data, indent=2))
    
    if "practices" in json_data:
        print(f"\nPractices found: {len(json_data['practices'])} practices")
        print(f"Practice keys: {list(json_data['practices'].keys())}")
    else:
        print("\nNo practices found in ToJson output!")

if __name__ == "__main__":
    main() 