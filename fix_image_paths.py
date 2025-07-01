#!/usr/bin/env python3
"""
Fix image paths in the database that have the wrong format.
This script updates any image_url entries that start with '/static/uploads/'
to just start with 'uploads/' instead.
"""

from shared import app, db, Product

def fix_image_paths():
    """Fix image paths in the database"""
    with app.app_context():
        # Find all products with image URLs that start with '/static/uploads/'
        products_to_fix = Product.query.filter(
            Product.image_url.like('/static/uploads/%')
        ).all()
        
        if not products_to_fix:
            print("✅ No products found with incorrect image paths.")
            return
        
        print(f"🔧 Found {len(products_to_fix)} products with incorrect image paths:")
        
        for product in products_to_fix:
            old_path = product.image_url
            # Remove the '/static/uploads/' prefix, keeping just 'filename'
            new_path = product.image_url.replace('/static/uploads/', '', 1)
            product.image_url = new_path
            
            print(f"   - Product '{product.name}': {old_path} → {new_path}")
        
        # Save changes
        db.session.commit()
        print(f"✅ Fixed {len(products_to_fix)} image paths successfully!")

if __name__ == "__main__":
    fix_image_paths()
