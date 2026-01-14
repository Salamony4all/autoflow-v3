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
    Get brand logo URL from brand-specific JSON files in brands_data directory.
    Each brand should have its own self-contained JSON file (e.g., NARBUTAS_mid_range.json, PEDRALI_seating.json).
    
    IMPORTANT: When a brand file is definitively matched, return that brand's logo or None.
    Do NOT fall back to other brand files' logos - this prevents showing wrong brand logos.
    
    Matching logic:
    1. Exact prefix match (brand_name matches start of filename) - DEFINITIVE
    2. Content match (brand field inside JSON matches brand_name) - DEFINITIVE
    3. Normalized fuzzy match (only if no definitive match found)
    
    Args:
        brand_name: Name of the brand to look up
    
    Returns:
        Logo URL string if found, None otherwise
    """
    if not brand_name:
        return None
    
    import json
    import re
    
    brand_name = brand_name.strip()
    brands_data_dir = 'brands_data'
    
    # Normalize brand name for matching (lowercase, remove special chars)
    def normalize_name(name):
        if not name:
            return ''
        return re.sub(r'[^a-z0-9]', '', name.lower())
    
    normalized_brand = normalize_name(brand_name)
    
    if not os.path.exists(brands_data_dir):
        logger.warning(f"Brands data directory not found: {brands_data_dir}")
        return None
    
    # Try to load from brand-specific JSON files ONLY (no brands_dynamic.json)
    try:
        json_files = [f for f in os.listdir(brands_data_dir) 
                      if f.endswith('.json') and f != 'brands_dynamic.json']
        
        # Priority 1: Exact prefix match (case-insensitive) - DEFINITIVE MATCH
        # If we find a file that starts with the brand name, that IS the brand file
        for filename in json_files:
            file_base = filename.rsplit('.', 1)[0]  # Remove .json extension
            # Check if file starts with brand name (handles B&T -> BT, etc.)
            if file_base.lower().startswith(brand_name.lower().replace('&', '')):
                brand_file_path = os.path.join(brands_data_dir, filename)
                logo = _extract_logo_from_file(brand_file_path)
                if logo:
                    logger.info(f"Found brand logo for '{brand_name}' via prefix match in {filename}")
                    return logo
                else:
                    # CRITICAL: This IS the correct brand file but has no logo
                    # Return None, do NOT continue searching other files
                    logger.warning(f"Brand file {filename} matched for '{brand_name}' but has no logo - returning None (not falling back)")
                    return None
        
        # Priority 2: Search within file content for brand field match - DEFINITIVE MATCH
        for filename in json_files:
            brand_file_path = os.path.join(brands_data_dir, filename)
            try:
                with open(brand_file_path, 'r', encoding='utf-8') as f:
                    brand_data = json.load(f)
                    file_brand = brand_data.get('brand', '')
                    # Exact normalized match on the brand field
                    if normalize_name(file_brand) == normalized_brand:
                        logo = brand_data.get('logo') or \
                               brand_data.get('brand_info', {}).get('logo') or \
                               brand_data.get('brand_logo')
                        if logo:
                            logger.info(f"Found brand logo for '{brand_name}' via content match in {filename}")
                            return logo
                        else:
                            # CRITICAL: This IS the correct brand file but has no logo
                            # Return None, do NOT continue searching other files
                            logger.warning(f"Brand file {filename} matched for '{brand_name}' but has no logo - returning None (not falling back)")
                            return None
            except Exception:
                continue
        
        # Priority 3: Normalized fuzzy match (only if no definitive match above)
        # This is a weaker match and should only be used as last resort
        for filename in json_files:
            file_base = filename.rsplit('.', 1)[0]
            normalized_file = normalize_name(file_base)
            # Only match if the normalized brand is a significant substring
            if len(normalized_brand) >= 3 and normalized_file.startswith(normalized_brand):
                brand_file_path = os.path.join(brands_data_dir, filename)
                # Verify by checking brand field inside
                try:
                    with open(brand_file_path, 'r', encoding='utf-8') as f:
                        brand_data = json.load(f)
                        file_brand = normalize_name(brand_data.get('brand', ''))
                        # Only use if brand field also matches
                        if file_brand == normalized_brand or normalized_brand in file_brand:
                            logo = brand_data.get('logo') or \
                                   brand_data.get('brand_info', {}).get('logo') or \
                                   brand_data.get('brand_logo')
                            if logo:
                                logger.info(f"Found brand logo for '{brand_name}' via fuzzy match in {filename}")
                                return logo
                except Exception:
                    continue
        
        logger.warning(f"No brand logo found for '{brand_name}' in {len(json_files)} brand files")
        
    except Exception as e:
        logger.error(f"Error searching brand files: {e}")
    
    return None


def _extract_logo_from_file(file_path):
    """
    Extract logo URL from a brand JSON file.
    
    Args:
        file_path: Path to the brand JSON file
    
    Returns:
        Logo URL string if found, None otherwise
    """
    import json
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            brand_data = json.load(f)
            # Check multiple possible keys for logo
            logo = brand_data.get('logo') or \
                   brand_data.get('brand_info', {}).get('logo') or \
                   brand_data.get('brand_logo')
            return logo
    except Exception as e:
        logger.error(f"Error reading brand file {file_path}: {e}")
        return None

