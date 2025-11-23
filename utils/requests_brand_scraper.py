"""
Brand scraper using requests + BeautifulSoup
Primary scraping method - no API limits, fast, reliable
"""

import requests
from bs4 import BeautifulSoup
import re
import time
import logging
from typing import Dict, List
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)


class RequestsBrandScraper:
    """
    Brand scraper using requests and BeautifulSoup
    """
    
    def __init__(self, delay: float = 1.0, fetch_descriptions: bool = True):
        """
        Initialize scraper
        
        Args:
            delay: Delay between requests in seconds (be polite)
            fetch_descriptions: If True, visits each product page to get full description
        """
        self.delay = delay
        self.fetch_descriptions = fetch_descriptions
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def scrape_brand_website(self, website: str, brand_name: str, limit: int = 100) -> Dict:
        """
        Scrape entire brand website
        
        Args:
            website: Brand website URL
            brand_name: Name of the brand
            limit: Maximum number of products per category
            
        Returns:
            Dictionary with scraped data
        """
        logger.info(f"Starting scrape for {brand_name} at {website}")
        
        try:
            # Get main page to find categories
            response = self.session.get(website, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find category links
            categories = self._find_categories(soup, website)
            logger.info(f"Found {len(categories)} categories")
            
            # Scrape each category
            all_products = {}
            category_tree = {}
            
            for category_name, category_url in categories.items():
                logger.info(f"Scraping category: {category_name}")
                
                # Get subcategories
                subcategories = self._find_subcategories(category_url, category_name)
                
                if subcategories:
                    # Has subcategories
                    category_tree[category_name] = {'subcategories': {}}
                    
                    for subcat_name, subcat_url in subcategories.items():
                        logger.info(f"  Scraping subcategory: {subcat_name}")
                        products = self._scrape_product_list(subcat_url, category_name, subcat_name, limit)
                        
                        if products:
                            category_tree[category_name]['subcategories'][subcat_name] = {
                                'products': products
                            }
                        
                        time.sleep(self.delay)
                else:
                    # No subcategories, scrape category directly
                    products = self._scrape_product_list(category_url, category_name, 'General', limit)
                    
                    if products:
                        category_tree[category_name] = {
                            'subcategories': {
                                'General': {'products': products}
                            }
                        }
                
                time.sleep(self.delay)
            
            return {
                'success': True,
                'brand': brand_name,
                'website': website,
                'category_tree': category_tree,
                'total_products': sum(
                    len(sub.get('products', []))
                    for cat in category_tree.values()
                    for sub in cat.get('subcategories', {}).values()
                )
            }
            
        except Exception as e:
            logger.error(f"Error scraping {brand_name}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _find_categories(self, soup: BeautifulSoup, base_url: str) -> Dict[str, str]:
        """Find main product categories from homepage"""
        categories = {}
        
        # Look for navigation menus with common patterns
        nav_patterns = [
            ('nav', {'class': lambda x: x and any(c in str(x).lower() for c in ['menu', 'nav', 'category'])}),
            ('ul', {'class': lambda x: x and any(c in str(x).lower() for c in ['menu', 'nav', 'category'])}),
            ('div', {'class': lambda x: x and 'menu' in str(x).lower()})
        ]
        
        for tag, attrs in nav_patterns:
            nav_elements = soup.find_all(tag, attrs)
            
            for nav in nav_elements:
                links = nav.find_all('a', href=True)
                
                for link in links:
                    href = link.get('href')
                    text = link.get_text(strip=True)
                    
                    # Look for product category URLs
                    if '/product-category/' in href and text:
                        # Skip nested subcategories, only get main categories
                        url_parts = href.split('/product-category/')[-1].split('/')
                        if len(url_parts) <= 2:  # Main category only
                            full_url = urljoin(base_url, href)
                            if text not in categories:
                                categories[text] = full_url
        
        return categories
    
    def _find_subcategories(self, category_url: str, category_name: str) -> Dict[str, str]:
        """Find subcategories within a category"""
        subcategories = {}
        
        try:
            response = self.session.get(category_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for subcategory links
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link.get('href')
                text = link.get_text(strip=True)
                
                # Check if it's a subcategory of current category
                if category_url in href and href != category_url:
                    # Extract subcategory name from URL
                    url_parts = href.split('/')
                    if text and text not in subcategories:
                        subcategories[text] = href
            
            return subcategories
            
        except Exception as e:
            logger.warning(f"Error finding subcategories for {category_name}: {e}")
            return {}
    
    def _scrape_product_list(self, url: str, category: str, subcategory: str, limit: int) -> List[Dict]:
        """Scrape products from a category/subcategory page with pagination support"""
        products = []
        page = 1
        seen_urls = set()
        
        while len(products) < limit:
            try:
                # Handle pagination - common patterns
                page_url = url
                if page > 1:
                    if '?' in url:
                        page_url = f"{url}&paged={page}"
                    else:
                        page_url = f"{url}?paged={page}" if not url.endswith('/') else f"{url}page/{page}/"
                
                logger.info(f"Scraping page {page}: {page_url}")
                response = self.session.get(page_url, timeout=15)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find product links - WooCommerce common patterns
                product_selectors = [
                    'a.woocommerce-LoopProduct-link',
                    'a.product-link',
                    'h2.woocommerce-loop-product__title a',
                    'a[href*="/product/"]'
                ]
                
                product_links = []
                for selector in product_selectors:
                    found = soup.select(selector)
                    if found:
                        product_links.extend(found)
                        break
                
                # Fallback: find all links to /product/
                if not product_links:
                    all_links = soup.find_all('a', href=True)
                    product_links = [link for link in all_links if '/product/' in link.get('href', '') and '/product-category/' not in link.get('href', '')]
                
                # If no products found, we've reached the end
                if not product_links:
                    logger.info(f"No more products found on page {page}")
                    break
                
                page_products_count = 0
                
                for link in product_links:
                    if len(products) >= limit:
                        break
                    
                    product_url = link.get('href')
                    if not product_url:
                        continue
                    
                    # Make absolute URL
                    if product_url.startswith('/'):
                        parsed = urlparse(url)
                        product_url = f"{parsed.scheme}://{parsed.netloc}{product_url}"
                    
                    # Skip if already seen
                    if product_url in seen_urls:
                        continue
                    
                    seen_urls.add(product_url)
                    
                    # Get product name
                    product_name = link.get_text(strip=True)
                    
                    if not product_name or len(product_name) < 3:
                        product_name = link.get('title', '')
                    
                    # Clean product name
                    product_name = re.sub(r'\s+', ' ', product_name).strip()
                    
                    # Skip navigation items
                    if any(skip in product_name.lower() for skip in ['add to', 'cart', 'wishlist', 'home', 'showing', 'filter', 'sort', 'categories']):
                        continue
                    
                    # Find associated image
                    img = link.find('img')
                    image_url = None
                    if img:
                        image_url = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                    
                    # Create product entry
                    product = {
                        'name': product_name,
                        'description': '',
                        'image_url': image_url,
                        'source_url': product_url,
                        'brand': category.split()[0] if category else 'Unknown',
                        'price': None,
                        'price_range': 'Contact for price',
                        'features': [],
                        'specifications': {},
                        'category_path': [category, subcategory]
                    }
                    
                    # Fetch detailed product info if enabled
                    if self.fetch_descriptions:
                        self._enrich_product_details(product)
                    
                    products.append(product)
                    page_products_count += 1
                
                logger.info(f"Page {page}: Found {page_products_count} products (Total: {len(products)})")
                
                # If no new products on this page, stop pagination
                if page_products_count == 0:
                    break
                
                page += 1
                time.sleep(self.delay)
                
            except Exception as e:
                logger.error(f"Error scraping page {page} from {url}: {e}")
                break
        
        return products
    
    def _enrich_product_details(self, product: Dict):
        """Visit individual product page to get full description and details"""
        try:
            response = self.session.get(product['source_url'], timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract description - common WooCommerce patterns
            description = ''
            
            # Method 1: Try WC tabs wrapper (OTTIMO uses this)
            tabs_wrapper = soup.find('div', class_='wc-tabs-wrapper')
            if tabs_wrapper:
                text = tabs_wrapper.get_text(strip=True)
                # Extract description between "Description" and "Additional"
                if 'Description' in text:
                    desc_start = text.find('Description') + len('Description')
                    desc_end = text.find('Additional', desc_start)
                    if desc_end > desc_start:
                        description = text[desc_start:desc_end].strip()
                    else:
                        description = text[desc_start:desc_start+500].strip()
            
            # Method 2: Try various description selectors
            if not description:
                desc_selectors = [
                    'div.woocommerce-product-details__short-description',
                    'div.product-short-description',
                    'div[itemprop="description"]',
                    'div.entry-summary p',
                    'div.summary p'
                ]
                
                for selector in desc_selectors:
                    desc_elem = soup.select_one(selector)
                    if desc_elem:
                        description = desc_elem.get_text(strip=True)
                        break
            
            # Method 3: Try full description tab
            if not description:
                full_desc_selectors = [
                    'div#tab-description',
                    'div.woocommerce-Tabs-panel--description',
                    'div.product-description'
                ]
                
                for selector in full_desc_selectors:
                    desc_elem = soup.select_one(selector)
                    if desc_elem:
                        # Get text from paragraphs
                        paragraphs = desc_elem.find_all('p')
                        if paragraphs:
                            description = ' '.join(p.get_text(strip=True) for p in paragraphs[:3])
                        else:
                            description = desc_elem.get_text(strip=True)[:500]
                        break
            
            # Clean up description
            if description:
                description = re.sub(r'\s+', ' ', description).strip()
                # Remove common unwanted text
                unwanted = ['add to cart', 'add to wishlist', 'share:', 'sku:', 'categories:', 'tags:']
                for unwanted_text in unwanted:
                    description = re.sub(unwanted_text, '', description, flags=re.IGNORECASE)
                description = description.strip()
            
            product['description'] = description
            
            # Try to extract price if available
            price_selectors = [
                'p.price span.amount',
                'span.woocommerce-Price-amount',
                'span.price-amount'
            ]
            
            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    product['price_range'] = price_text
                    break
            
            time.sleep(self.delay * 0.5)  # Half delay for product pages
            
        except Exception as e:
            logger.warning(f"Could not enrich product {product['name']}: {e}")
            # Continue without description if fetch fails

