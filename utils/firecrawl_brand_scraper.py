"""
Firecrawl-based Brand Scraper
Uses Firecrawl API to crawl brand websites and extract product information
"""

import re
import logging
from typing import Dict, List, Optional
from datetime import datetime
from urllib.parse import urlparse, urljoin
from firecrawl import Firecrawl

logger = logging.getLogger(__name__)


class FirecrawlBrandScraper:
    """
    Brand scraper using Firecrawl API for robust web crawling and data extraction
    """
    
    def __init__(self, api_key: str = "fc-05e4171926164a569eaded40652cac1a"):
        """
        Initialize Firecrawl scraper
        
        Args:
            api_key: Firecrawl API key
        """
        self.api_key = api_key
        self.firecrawl = Firecrawl(api_key=api_key)
        
    def scrape_brand_website(
        self, 
        website: str, 
        brand_name: str,
        limit: int = 50
    ) -> Dict:
        """
        Scrape a brand website using Firecrawl API
        
        Args:
            website: Brand website URL
            brand_name: Brand name
            limit: Maximum number of pages to crawl
            
        Returns:
            Dictionary with brand data and products
        """
        
        logger.info(f"Starting Firecrawl crawl for {brand_name} at {website}")
        
        try:
            # Use Firecrawl Python SDK - crawl() method handles polling automatically
            logger.info(f"Initiating Firecrawl crawl job for {website} (limit: {limit} pages)...")
            
            # The crawl() method returns results directly after polling completes
            crawl_result = self.firecrawl.crawl(
                url=website,
                limit=limit
            )
            
            logger.info(f"Crawl completed! Result type: {type(crawl_result)}")
            
            # Check if we got a valid response
            if not crawl_result:
                logger.warning(f"No response from Firecrawl for {brand_name}")
                return self._empty_result(brand_name)
            
            # Extract pages data - SDK returns list of documents directly
            pages_data = []
            
            if isinstance(crawl_result, list):
                # Direct list of pages
                pages_data = crawl_result
                logger.info(f"Got list with {len(pages_data)} pages")
            elif isinstance(crawl_result, dict):
                # Check for data key
                if 'data' in crawl_result:
                    pages_data = crawl_result['data']
                    logger.info(f"Extracted {len(pages_data)} pages from dict['data']")
                else:
                    logger.warning(f"Dict response but no 'data' key. Keys: {crawl_result.keys()}")
                    # Maybe the dict itself is a single page
                    pages_data = [crawl_result]
            else:
                logger.error(f"Unexpected result type: {type(crawl_result)}")
                logger.error(f"Result: {crawl_result}")
                return self._empty_result(brand_name)
            
            if not pages_data:
                logger.warning(f"No pages data found in crawl response")
                return self._empty_result(brand_name)
            
            logger.info(f"Successfully retrieved {len(pages_data)} pages, now processing...")
            
            # Parse crawl results - wrap in expected dict format
            result = self._parse_crawl_results({'data': pages_data}, brand_name, website)
            
            logger.info(f"✅ Extraction complete: {result['total_products']} products found in {result['total_collections']} collections")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error during Firecrawl scraping: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return self._empty_result(brand_name)
    
    def _parse_crawl_results(self, crawl_result: Dict, brand_name: str, base_url: str) -> Dict:
        """
        Parse Firecrawl crawl results and extract products
        
        Args:
            crawl_result: Firecrawl crawl response
            brand_name: Brand name
            base_url: Base website URL
            
        Returns:
            Structured brand data with products
        """
        result = {
            'brand': brand_name,
            'source': 'Brand Website (Firecrawl)',
            'scraped_at': datetime.now().isoformat(),
            'total_products': 0,
            'total_collections': 0,
            'collections': {},
            'all_products': []
        }
        
        pages = crawl_result.get('data', [])
        
        # Extract products from each page
        for page in pages:
            url = page.get('metadata', {}).get('sourceURL', '')
            markdown = page.get('markdown', '')
            html = page.get('html', '')
            metadata = page.get('metadata', {})
            
            # Check if this is a product page
            if self._is_product_page(url, markdown, metadata):
                product = self._extract_product_from_page(
                    url, markdown, html, metadata, brand_name
                )
                
                if product:
                    # Determine category and collection
                    category, subcategory = self._detect_category_from_url(url, metadata)
                    
                    product['category'] = category
                    product['subcategory'] = subcategory
                    
                    # Add to collection
                    if subcategory:
                        coll_key = f"{category} > {subcategory}"
                    else:
                        coll_key = category
                    
                    if coll_key not in result['collections']:
                        result['collections'][coll_key] = {
                            'url': url,
                            'category': category,
                            'subcategory': subcategory,
                            'product_count': 0,
                            'products': []
                        }
                    
                    result['collections'][coll_key]['products'].append(product)
                    result['all_products'].append(product)
            
            # Also check if this is a category/listing page with multiple products
            elif self._is_category_page(url, markdown):
                products = self._extract_products_from_listing(url, markdown, brand_name)
                if products:
                    logger.info(f"Extracted {len(products)} products from listing page: {url}")
                    for product in products:
                        # Determine category and collection
                        category, subcategory = self._detect_category_from_url(url, metadata)
                        
                        product['category'] = category
                        product['subcategory'] = subcategory if subcategory else 'general'
                        
                        # Add to collection
                        if subcategory:
                            coll_key = f"{category} > {subcategory}"
                        else:
                            coll_key = f"{category} > general"
                        
                        if coll_key not in result['collections']:
                            result['collections'][coll_key] = {
                                'url': url,
                                'category': category,
                                'subcategory': subcategory if subcategory else 'general',
                                'product_count': 0,
                                'products': []
                            }
                        
                        result['collections'][coll_key]['products'].append(product)
                        result['all_products'].append(product)
        
        # Update counts
        for coll_key in result['collections']:
            result['collections'][coll_key]['product_count'] = len(
                result['collections'][coll_key]['products']
            )
        
        result['total_products'] = len(result['all_products'])
        result['total_collections'] = len(result['collections'])
        
        return result
    
    def _is_product_page(self, url: str, markdown: str, metadata: Dict) -> bool:
        """
        Determine if a page is a product page
        
        Args:
            url: Page URL
            markdown: Page markdown content
            metadata: Page metadata
            
        Returns:
            True if product page, False otherwise
        """
        # Exclude category/listing pages first
        if re.search(r'/product-category/|/category/|/archive|/page/\d+', url, re.IGNORECASE):
            return False
            
        # Check URL patterns for individual products
        product_patterns = [
            r'/product/[^/]+/?$',  # /product/chair-name/
            r'/item/[^/]+/?$',
            r'/p/[^/]+/?$',
            r'-\d+\.html$'
        ]
        
        for pattern in product_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        
        # Check metadata
        og_type = metadata.get('ogType', '')
        if og_type == 'product':
            return True
        
        return False
    
    def _is_category_page(self, url: str, markdown: str) -> bool:
        """
        Determine if a page is a category/listing page
        
        Args:
            url: Page URL
            markdown: Page markdown content
            
        Returns:
            True if category page, False otherwise
        """
        # Check URL patterns
        category_patterns = [
            r'/product-category/',
            r'/category/',
            r'/product-tag/',
            r'/collection/',
            r'/shop/?$',
            r'/products/?$'
        ]
        
        for pattern in category_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        
        # Check for multiple product listings in markdown
        # Look for repeated product patterns
        product_link_count = len(re.findall(r'\[.*?\]\(.*?/product/.*?\)', markdown))
        if product_link_count >= 3:  # If 3 or more product links, it's likely a listing
            return True
        
        return False
    
    def _extract_products_from_listing(
        self, 
        url: str, 
        markdown: str,
        brand_name: str
    ) -> List[Dict]:
        """
        Extract multiple products from a category/listing page
        
        Args:
            url: Page URL
            markdown: Page markdown content
            brand_name: Brand name
            
        Returns:
            List of product dictionaries
        """
        products = []
        
        # Try to find product blocks in markdown
        # Pattern: Product title followed by link
        product_pattern = r'\[([^\]]+)\]\((https?://[^)]+/product/[^)]+)\)'
        matches = re.findall(product_pattern, markdown, re.IGNORECASE)
        
        for title, product_url in matches:
            # Clean title
            title = title.strip()
            if not title or len(title) < 3:
                continue
            
            # Skip navigation/UI elements and category links
            skip_terms = [
                'add to', 'select option', 'wishlist', 'cart', 'home', 'archives',
                'open submenu', 'contact for price', 'showing', 'filter', 'sort by',
                'page', 'next', 'previous', 'view:', 'categories', 'tags',
                'coffee table', 'accessories', 'new arrivals', 'desks', 'chairs', 
                'storage', 'sofa'  # Common category names
            ]
            if any(skip in title.lower() for skip in skip_terms):
                continue
            
            # Skip if URL is a category page, not a product page
            if re.search(r'/product-category/|/category/|/tag/', product_url, re.IGNORECASE):
                continue
            
            # Create product
            product = {
                'name': title,
                'description': '',
                'image_url': '',
                'source_url': product_url,
                'brand': brand_name,
                'price': None,
                'price_range': 'Contact for price',
                'features': [],
                'specifications': {}
            }
            
            products.append(product)
        
        # Also try to extract product info from structured markdown sections
        # Look for patterns like "### Product Name" followed by content
        section_pattern = r'###\s+\[?([^\]\n]+)\]?[^\n]*\n+((?:.*?\n)*?)(?=###|\Z)'
        sections = re.findall(section_pattern, markdown, re.MULTILINE)
        
        for section_title, section_content in sections:
            section_title = section_title.strip()
            
            # Skip non-product sections
            if any(skip in section_title.lower() for skip in ['filter', 'sort', 'view', 'showing', 'page']):
                continue
            
            # Look for product URL in section
            url_match = re.search(r'\((https?://[^)]+/product/[^)]+)\)', section_content)
            if url_match:
                product_url = url_match.group(1)
                
                # Check if we already have this product
                if any(p['source_url'] == product_url for p in products):
                    continue
                
                product = {
                    'name': section_title,
                    'description': section_content[:200].strip() if section_content else '',
                    'image_url': '',
                    'source_url': product_url,
                    'brand': brand_name,
                    'price': None,
                    'price_range': 'Contact for price',
                    'features': [],
                    'specifications': {}
                }
                
                # Try to extract image
                img_match = re.search(r'!\[.*?\]\((https?://[^)]+)\)', section_content)
                if img_match:
                    product['image_url'] = img_match.group(1)
                
                products.append(product)
        
        logger.info(f"Found {len(products)} products in listing page")
        return products
    
    def _extract_product_from_page(
        self, 
        url: str, 
        markdown: str, 
        html: str, 
        metadata: Dict,
        brand_name: str
    ) -> Optional[Dict]:
        """
        Extract product information from a page
        
        Args:
            url: Page URL
            markdown: Page markdown
            html: Page HTML
            metadata: Page metadata
            brand_name: Brand name
            
        Returns:
            Product dictionary or None
        """
        try:
            # Extract title
            title = metadata.get('title', '')
            if not title:
                # Try to extract from markdown (first H1)
                h1_match = re.search(r'^#\s+(.+)$', markdown, re.MULTILINE)
                if h1_match:
                    title = h1_match.group(1).strip()
            
            # Clean title (remove brand name, "buy", etc.)
            title = self._clean_product_title(title, brand_name)
            
            if not title or len(title) < 3:
                return None
            
            # Extract image
            image_url = metadata.get('ogImage', '')
            if not image_url:
                # Try to find first image in markdown
                img_match = re.search(r'!\[.*?\]\((https?://[^\)]+)\)', markdown)
                if img_match:
                    image_url = img_match.group(1)
            
            # Extract price
            price = self._extract_price(markdown, html)
            
            # Extract description
            description = metadata.get('description', '')
            if not description:
                # Get first paragraph from markdown
                para_match = re.search(r'\n\n(.+?)\n\n', markdown, re.DOTALL)
                if para_match:
                    description = para_match.group(1).strip()[:200]
            
            product = {
                'brand': brand_name,
                'model': title,
                'image_url': image_url,
                'price': price,
                'source_url': url,
                'description': description,
                'collection': 'General'
            }
            
            return product
            
        except Exception as e:
            logger.error(f"Error extracting product from {url}: {e}")
            return None
    
    def _clean_product_title(self, title: str, brand_name: str) -> str:
        """Clean product title by removing brand name and common suffixes"""
        if not title:
            return ""
        
        # Remove brand name
        title = re.sub(rf'\b{re.escape(brand_name)}\b', '', title, flags=re.IGNORECASE)
        
        # Remove common suffixes
        title = re.sub(r'\s*[-|]\s*.+$', '', title)  # Remove everything after - or |
        title = re.sub(r'\s*\(.*?\)', '', title)  # Remove parentheses
        title = re.sub(r'\b(buy|shop|price|online)\b', '', title, flags=re.IGNORECASE)
        
        return title.strip()
    
    def _extract_price(self, markdown: str, html: str) -> Optional[str]:
        """Extract price from markdown or HTML"""
        # Price patterns
        patterns = [
            r'(?:Price|Cost|AED|USD|\$|€|£)\s*:?\s*(\d+(?:[.,]\d{2})?)',
            r'(\d+(?:[.,]\d{2})?)\s*(?:AED|USD|\$|€|£)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, markdown)
            if match:
                return match.group(1)
        
        return None
    
    def _detect_category_from_url(self, url: str, metadata: Dict) -> tuple:
        """
        Detect category and subcategory from URL path
        
        Args:
            url: Page URL
            metadata: Page metadata
            
        Returns:
            Tuple of (category, subcategory)
        """
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p and p != 'product']
        
        # Try to extract from breadcrumbs in metadata
        # For now, use URL path
        
        category = "Products"
        subcategory = None
        
        if len(path_parts) >= 2:
            # e.g., /chairs/executive/product-name
            category = path_parts[0].replace('-', ' ').title()
            subcategory = path_parts[1].replace('-', ' ').title()
        elif len(path_parts) >= 1:
            # e.g., /chairs/product-name
            category = path_parts[0].replace('-', ' ').title()
        
        return category, subcategory
    
    def _empty_result(self, brand_name: str) -> Dict:
        """Return empty result structure"""
        return {
            'brand': brand_name,
            'source': 'Brand Website (Firecrawl)',
            'scraped_at': datetime.now().isoformat(),
            'total_products': 0,
            'total_collections': 0,
            'collections': {},
            'all_products': []
        }
