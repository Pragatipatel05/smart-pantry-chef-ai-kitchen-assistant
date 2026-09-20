#!/usr/bin/env python3
import sys
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-02-7b95af39ea22"  # Hardcoded GCP Project ID

def seed_pantry():
    print(f"Connecting to Firestore for project: {PROJECT_ID}...")
    db = firestore.Client(project=PROJECT_ID)
    collection_ref = db.collection("pantry_inventory")

    seeded_items = [
        {
            "item_id": "eggs",
            "name": "Organic Eggs",
            "quantity": 12.0,
            "unit": "count",
            "category": "Dairy & Eggs",
            "expiration_date": "2026-10-15",
            "notes": "Pasture-raised grade A large brown eggs"
        },
        {
            "item_id": "tomatoes",
            "name": "Roma Tomatoes",
            "quantity": 6.0,
            "unit": "count",
            "category": "Produce",
            "expiration_date": "2026-10-05",
            "notes": "Ripe vine-ripened tomatoes"
        },
        {
            "item_id": "spinach",
            "name": "Baby Spinach",
            "quantity": 1.0,
            "unit": "bag",
            "category": "Produce",
            "expiration_date": "2026-09-30",
            "notes": "Fresh organic baby spinach greens"
        },
        {
            "item_id": "chickpeas",
            "name": "Garbanzo Beans",
            "quantity": 3.0,
            "unit": "cans",
            "category": "Canned Goods",
            "expiration_date": "2027-05-01",
            "notes": "Low-sodium organic chickpeas"
        },
        {
            "item_id": "olive_oil",
            "name": "Extra Virgin Olive Oil",
            "quantity": 1.0,
            "unit": "bottle",
            "category": "Pantry Staples",
            "expiration_date": "2027-12-31",
            "notes": "Cold pressed Italian olive oil"
        },
        {
            "item_id": "curry_powder",
            "name": "Madras Curry Powder",
            "quantity": 1.0,
            "unit": "jar",
            "category": "Spices",
            "expiration_date": "2027-08-15",
            "notes": "Spicy gluten-free yellow curry blend"
        }
    ]

    print("Seeding pantry items into Firestore 'pantry_inventory' collection...")
    for item in seeded_items:
        doc_ref = collection_ref.document(item["item_id"])
        doc_ref.set(item)
        print(f"  - Seeded: {item['name']} ({item['quantity']} {item['unit']})")

    print("Firestore seeding complete!")

if __name__ == "__main__":
    seed_pantry()
