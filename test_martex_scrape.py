#!/usr/bin/env python3
"""
Test script to verify Martex scraping from Architonic
"""
import logging
from utils.architonic_scraper import ArchitonicScraper

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_martex_scrape():
    """Test scraping Martex collections from Architonic"""
    
    # Martex collections URL
    url = "https://www.architonic.com/en/b/martex/collections/3101472/"
    brand_name = "MARTEX"
    
    print("=" * 80)
    print("🏛️  TESTING ARCHITONIC SCRAPER - MARTEX")
    print("=" * 80)
    print(f"\n📍 URL: {url}")
    print(f"🏷️  Brand: {brand_name}\n")
    
    # Initialize scraper
    scraper = ArchitonicScraper(use_selenium=True)
    
    # Verify it's an Architonic URL
    if not scraper.is_architonic_url(url):
        print("❌ ERROR: Not detected as Architonic URL")
        return False
    
    print("✅ URL detected as Architonic\n")
    
    # Verify it's a collections page
    if not scraper.is_collections_page(url):
        print("⚠️  WARNING: Not detected as collections page (will try anyway)")
    else:
        print("✅ Detected as collections page\n")
    
    print("🚀 Starting scrape...\n")
    print("-" * 80)
    
    # Scrape the collection
    result = scraper.scrape_collection(url, brand_name)
    
    print("-" * 80)
    print("\n📊 SCRAPING RESULTS:\n")
    
    if 'error' in result:
        print(f"❌ ERROR: {result['error']}")
        return False
    
    # Display statistics
    total_products = result.get('total_products', 0)
    total_collections = result.get('total_collections', 0)
    collections = result.get('collections', {})
    category_tree = result.get('category_tree', {})
    
    print(f"✅ Total Products: {total_products}")
    print(f"✅ Total Collections: {total_collections}")
    print(f"✅ Category Tree Categories: {len(category_tree)}")
    
    print("\n📦 COLLECTIONS FOUND:\n")
    for collection_name, collection_data in collections.items():
        product_count = collection_data.get('product_count', 0)
        clean_name = collection_name.split('\n')[0]
        print(f"   • {clean_name}: {product_count} products")
    
    print("\n🗂️  CATEGORY TREE STRUCTURE:\n")
    for category_name, category_data in category_tree.items():
        subcats = category_data.get('subcategories', {})
        total_prods = sum(len(sub.get('products', [])) for sub in subcats.values())
        print(f"   • {category_name}: {total_prods} products")
        for subcat_name, subcat_data in subcats.items():
            prod_count = len(subcat_data.get('products', []))
            print(f"      └─ {subcat_name}: {prod_count} products")
    
    # Sample some products
    print("\n🖼️  SAMPLE PRODUCTS (first 3):\n")
    sample_count = 0
    for collection_name, collection_data in collections.items():
        if sample_count >= 3:
            break
        for product in collection_data.get('products', [])[:3-sample_count]:
            print(f"   • {product.get('name', 'Unknown')}")
            print(f"     URL: {product.get('url', 'N/A')}")
            print(f"     Image: {'✅' if product.get('image_url') else '❌'}")
            print(f"     ID: {product.get('product_id', 'N/A')}")
            print()
            sample_count += 1
            if sample_count >= 3:
                break
    
    # Verify expected collections (from the website)
    expected_collections = [
        'ACOUSTIC SOLUTIONS',
        'EXECUTIVE',
        'MEETING',
        'SEATING',
        'STORAGES',
        'WORKSPACES'
    ]
    
    found_collections = [name.split('\n')[0].upper() for name in collections.keys()]
    
    print("\n✅ EXPECTED COLLECTIONS CHECK:\n")
    for expected in expected_collections:
        if expected.upper() in [fc.upper() for fc in found_collections]:
            print(f"   ✅ {expected}")
        else:
            print(f"   ❌ {expected} - NOT FOUND")
    
    # Success criteria
    success = (
        total_products >= 100 and  # Should have at least 100 products (expected ~159)
        total_collections >= 5 and  # Should have at least 5 collections
        len(category_tree) >= 5  # Should have at least 5 categories
    )
    
    print("\n" + "=" * 80)
    if success:
        print("✅ TEST PASSED - Scraper working correctly!")
        print(f"   • Products: {total_products} (expected ~159)")
        print(f"   • Collections: {total_collections} (expected 6)")
    else:
        print("⚠️  TEST INCOMPLETE - Results below expected")
        print(f"   • Products: {total_products} (expected ~159)")
        print(f"   • Collections: {total_collections} (expected 6)")
        print("\n   This might be normal if:")
        print("   - The website has fewer products than expected")
        print("   - The scraping was interrupted")
        print("   - Network issues occurred")
    print("=" * 80)
    
    return success

if __name__ == '__main__':
    try:
        success = test_martex_scrape()
        exit(0 if success else 1)
    except Exception as e:
        logger.exception("Test failed with exception")
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)

