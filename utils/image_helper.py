"""Helper functions for downloading and caching product images"""
import os
import requests
import hashlib
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

def download_image(image_url, cache_dir='static/product_images'):
    """
    Download and cache an image from URL
    
    Args:
        image_url: URL of the image to download
        cache_dir: Directory to cache images in
    
    Returns:
        Local file path if successful, None otherwise
    """
    if not image_url:
        return None
    
    try:
        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)
        
        # Generate cache filename from URL
        url_hash = hashlib.md5(image_url.encode()).hexdigest()
        parsed_url = urlparse(image_url)
        ext = os.path.splitext(parsed_url.path)[1] or '.jpg'
        if not ext.startswith('.'):
            ext = '.' + ext
        
        cache_filename = f"{url_hash}{ext}"
        cache_path = os.path.join(cache_dir, cache_filename)
        
        # Return cached path if exists
        if os.path.exists(cache_path):
            return cache_path
        
        # Download image
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(image_url, headers=headers, timeout=10, stream=True)
        response.raise_for_status()
        
        # Save to cache
        with open(cache_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Cached image: {image_url} -> {cache_path}")
        return cache_path
        
    except Exception as e:
        logger.warning(f"Failed to download image {image_url}: {e}")
        return None

def get_product_image_url(brand_name, category, subcategory, model_name, tier='mid_range'):
    """
    Get product image URL from brand data
    
    Args:
        brand_name: Name of the brand
        category: Product category
        subcategory: Product subcategory
        model_name: Product model name
        tier: Budget tier
    
    Returns:
        Image URL if found, None otherwise
    """
    try:
        import json
        import re
        import os
        
        # Load brand data
        safe_brand_name = re.sub(r'[^\w\-_]', '', brand_name.replace(' ', '_'))
        filename = f"{safe_brand_name}_{tier}.json"
        filepath = os.path.join('brands_data', filename)
        
        if not os.path.exists(filepath):
            # Try case-insensitive search
            brands_data_dir = 'brands_data'
            if os.path.exists(brands_data_dir):
                for f in os.listdir(brands_data_dir):
                    if f.lower() == filename.lower():
                        filepath = os.path.join(brands_data_dir, f)
                        break
        
        if not os.path.exists(filepath):
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            brand_data = json.load(f)
        
        # Search in categories
        categories_data = brand_data.get('categories', {})
        if category in categories_data:
            subcategories = categories_data[category]
            if subcategory in subcategories:
                for product in subcategories[subcategory]:
                    if product.get('model', '').strip() == model_name.strip():
                        return product.get('image_url')
        
        # Search in collections
        collections = brand_data.get('collections', {})
        for collection_name, collection_data in collections.items():
            for product in collection_data.get('products', []):
                if product.get('name', '').strip() == model_name.strip() or \
                   product.get('model', '').strip() == model_name.strip():
                    return product.get('image_url')
        
        return None
        
    except Exception as e:
        logger.warning(f"Error getting product image URL: {e}")
        return None

def get_brand_logo_url(brand_name):
    """
    Get brand logo URL from brand JSON data in brands_data directory.
    Supports exact match and prefix match (e.g., 'NARBUTAS' matching 'NARBUTAS_mid_range.json').
    
    Args:
        brand_name: Name of the brand
    
    Returns:
        Logo URL string if found, None otherwise
    """
    if not brand_name:
        return None
    
    import json
    
    brand_name = brand_name.strip()
    brands_data_dir = 'brands_data'
    
    # Try to load from brand-specific JSON file
    # Check for direct match or prefix match (e.g., NARBUTAS_mid_range.json)
    try:
        if os.path.exists(brands_data_dir):
            for filename in os.listdir(brands_data_dir):
                if filename.lower().startswith(brand_name.lower()) and filename.endswith('.json'):
                    brand_file_path = os.path.join(brands_data_dir, filename)
                    try:
                        with open(brand_file_path, 'r', encoding='utf-8') as f:
                            brand_data = json.load(f)
                            # Check multiple possible keys for logo
                            logo = brand_data.get('logo') or \
                                   brand_data.get('brand_info', {}).get('logo') or \
                                   brand_data.get('brand_logo')
                            if logo:
                                return logo
                    except Exception as e:
                        logger.error(f"Error reading brand file {filename}: {e}")
    except Exception as e:
        logger.error(f"Error listing brands_data: {e}")
    
    # Try to load from brands_dynamic.json
    brands_dynamic_path = os.path.join(brands_data_dir, 'brands_dynamic.json')
    if os.path.exists(brands_dynamic_path):
        try:
            with open(brands_dynamic_path, 'r', encoding='utf-8') as f:
                brands_dynamic = json.load(f)
                for brand_entry in brands_dynamic.get('brands', []):
                    if brand_entry.get('name', '').lower() == brand_name.lower():
                        logo = brand_entry.get('logo')
                        if logo:
                            return logo
        except Exception as e:
            logger.error(f"Error reading brands_dynamic.json: {e}")
    
    return None

