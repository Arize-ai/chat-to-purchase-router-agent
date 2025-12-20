#!/usr/bin/env python3
"""Populate database from cached seed data. Run: python database/populate_db.py"""

import psycopg2
from pathlib import Path
import json

DB_CONFIG = {'host': 'localhost', 'port': 5432, 'database': 'chat_to_purchase', 'user': 'postgres', 'password': 'postgres'}
CACHE_FILE = Path(__file__).parent / 'seed_cache.json'

def populate_database():
    # Load cache
    try:
        with open(CACHE_FILE, 'r') as f:
            cache = json.load(f)
        print(f"✓ Loaded {len(cache)} products")
    except FileNotFoundError:
        print(f"Error: Cache file not found: {CACHE_FILE}")
        return
    
    # Connect to database
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
    except Exception as e:
        print(f"Error: {e}\nMake sure database is running: docker-compose up -d")
        return
    
    # Check existing products
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] > 0:
        if input(f"Found existing products. Clear and repopulate? (y/n): ").lower() != 'y':
            conn.close()
            return
        cursor.execute("TRUNCATE TABLE products RESTART IDENTITY")
    
    # Insert products
    print(f"Inserting {len(cache)} products...")
    inserted = failed = 0
    for idx, (filename, p) in enumerate(cache.items(), 1):
        try:
            cursor.execute("INSERT INTO products (name, description, price, image_path, rating, category) VALUES (%s, %s, %s, %s, %s, %s)",
                         (p['name'], p['description'], p['price'], p['image_path'], p['rating'], p['category']))
            inserted += 1
            if idx % 50 == 0 or idx == len(cache):
                print(f"  {inserted}/{len(cache)} inserted...")
        except Exception as e:
            failed += 1
            print(f"  ✗ Failed {filename}: {e}")
    
    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM products")
    print(f"\n✓ Inserted {inserted} products | Total in DB: {cursor.fetchone()[0]}")
    if failed > 0:
        print(f"⚠️  Failed: {failed}")
    cursor.close()
    conn.close()

if __name__ == '__main__':
    populate_database()

