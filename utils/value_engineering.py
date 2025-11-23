import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime
from .brand_database import BrandDatabase

class ValueEngineer:
    """Generate value-engineered alternatives using AI product search"""
    
    def __init__(self):
        self.brand_db = BrandDatabase()
        self.architonic_base_url = "https://www.architonic.com"
        self.budget_multipliers = {
            'budgetary': 0.7,
            'mid_range': 1.0,
            'high_end': 1.5
        }
    
    def generate_alternatives(self, file_id, budget_option, session):
        """
        Generate value-engineered alternatives for items
        Returns: list of alternatives with pricing
        """
        # Get file info and extracted data
        uploaded_files = session.get('uploaded_files', [])
        file_info = None
        
        for f in uploaded_files:
            if f['id'] == file_id:
                file_info = f
                break
        
        if not file_info:
            raise Exception('File not found. Please upload and extract tables first.')
        
        # Check if stitched table exists (preferred)
        if 'stitched_table' in file_info:
            items = self.parse_stitched_table(file_info['stitched_table'])
        elif 'extraction_result' in file_info:
            # Fallback to extraction result
            extraction_result = file_info['extraction_result']
            costed_data = file_info.get('costed_data', None)
            items = self.parse_items(extraction_result, costed_data)
        else:
            raise Exception('No table data found. Please extract and stitch tables first.')
        
        if not items:
            raise Exception('No items found in the table. Please check the extraction.')
        
        # Generate alternatives for each item
        alternatives = []
        for item in items:
            item_alternatives = self.find_alternatives(item, budget_option)
            alternatives.append({
                'original_item': item,
                'alternatives': item_alternatives,
                'budget_option': budget_option
            })
        
        # Store alternatives in session
        file_info['value_engineering'] = {
            'budget_option': budget_option,
            'alternatives': alternatives,
            'generated_at': datetime.now().isoformat()
        }
        session.modified = True
        
        return alternatives
    
    def parse_stitched_table(self, stitched_table_data):
        """Parse items from stitched table HTML"""
        from bs4 import BeautifulSoup
        import logging
        
        logger = logging.getLogger(__name__)
        items = []
        html_content = stitched_table_data.get('html', '')
        
        if not html_content:
            logger.warning("No HTML content in stitched table")
            return items
        
        soup = BeautifulSoup(html_content, 'html.parser')
        table = soup.find('table')
        
        if not table:
            logger.warning("No table found in HTML content")
            return items
        
        rows = table.find_all('tr')
        headers = []
        
        logger.info(f"Processing {len(rows)} rows from stitched table")
        
        for row in rows:
            cells = row.find_all(['th', 'td'])
            if not cells:
                continue
            
            cell_texts = [cell.get_text(strip=True) for cell in cells]
            
            # First row with meaningful content is headers
            if not headers and any(cell_texts):
                # Check if this looks like a header row
                header_keywords = ['si.no', 'item', 'description', 'qty', 'unit', 'rate', 'amount', 'price', 'total']
                if any(keyword in ' '.join(cell_texts).lower() for keyword in header_keywords):
                    headers = [h.lower() for h in cell_texts]
                    logger.info(f"Found headers: {headers}")
                    continue
            
            # Skip if no headers yet or if row is empty
            if not headers or not any(cell_texts):
                continue
            
            # Skip header rows that appear again
            if any(keyword in ' '.join(cell_texts).lower() for keyword in ['si.no', 'item description', 'qty', 'unit rate']):
                continue
            
            # Parse row data
            if len(cell_texts) >= len(headers):
                row_dict = {}
                for i, header in enumerate(headers):
                    if i < len(cell_texts):
                        row_dict[header] = cell_texts[i]
                
                # Extract item information
                description = self.get_value_from_row(row_dict, ['description', 'item', 'item description', 'particulars'])
                qty = self.get_value_from_row(row_dict, ['qty', 'quantity', 'qnty'])
                unit = self.get_value_from_row(row_dict, ['unit', 'uom'])
                unit_rate = self.get_value_from_row(row_dict, ['unit rate', 'rate', 'unit price', 'price'])
                total = self.get_value_from_row(row_dict, ['total', 'amount', 'total amount'])
                
                # Skip if description is empty or looks like a section header
                if not description or len(description) < 5:
                    continue
                
                # Categorize the item
                categorization = self.categorize_item(description)
                
                item = {
                    'description': description,
                    'qty': self.parse_number(qty),
                    'unit': unit,
                    'unit_rate': self.parse_number(unit_rate),
                    'total': self.parse_number(total),
                    'category': categorization['category'],
                    'subcategory': categorization['subcategory']
                }
                
                # Only add items with meaningful data
                if item['qty'] > 0 or item['unit_rate'] > 0:
                    items.append(item)
                    logger.info(f"Added item: {description[:50]}... (Category: {item['category']}/{item['subcategory']})")
        
        logger.info(f"Parsed {len(items)} items from stitched table")
        return items
    
    def get_value_from_row(self, row_dict, possible_keys):
        """Get value from row dict trying multiple possible keys"""
        for key in possible_keys:
            for row_key in row_dict.keys():
                if key in row_key.lower():
                    return row_dict[row_key]
        return ''
    
    def parse_items(self, extraction_result, costed_data=None):
        """Parse items from extraction result"""
        items = []
        
        for layout_result in extraction_result.get('layoutParsingResults', []):
            markdown_text = layout_result.get('markdown', {}).get('text', '')
            
            # Parse tables
            rows = self.extract_table_rows(markdown_text)
            
            for row in rows:
                item_desc = row.get('description', row.get('item', ''))
                categorization = self.categorize_item(item_desc)
                
                item = {
                    'description': item_desc,
                    'qty': self.parse_number(row.get('qty', row.get('quantity', '0'))),
                    'unit': row.get('unit', ''),
                    'unit_rate': self.parse_number(row.get('unit rate', row.get('unit price', row.get('rate', '0')))),
                    'total': self.parse_number(row.get('total', row.get('amount', '0'))),
                    'category': categorization['category'],
                    'subcategory': categorization['subcategory']
                }
                items.append(item)
        
        return items
    
    def extract_table_rows(self, markdown_text):
        """Extract table rows from markdown"""
        lines = markdown_text.split('\n')
        rows = []
        headers = []
        
        for line in lines:
            if '|' in line:
                cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                
                if not headers and cells:
                    headers = [h.lower() for h in cells]
                elif headers and cells and not all(c in '-: ' for c in ''.join(cells)):
                    if len(cells) == len(headers):
                        row = dict(zip(headers, cells))
                        rows.append(row)
        
        return rows
    
    def parse_number(self, value):
        """Parse numeric value from string"""
        if isinstance(value, (int, float)):
            return float(value)
        
        # Remove currency symbols and commas
        cleaned = re.sub(r'[^\d.-]', '', str(value))
        
        try:
            return float(cleaned)
        except:
            return 0.0
    
    def categorize_item(self, description):
        """Categorize item based on description"""
        description_lower = description.lower()
        
        # Detailed categorization matching brand database
        seating_keywords = {
            'executive_chairs': ['executive chair', 'director chair', 'manager chair', 'executive seating'],
            'task_chairs': ['task chair', 'office chair', 'work chair', 'operator chair', 'ergonomic chair'],
            'visitor_chairs': ['visitor chair', 'guest chair', 'side chair', 'reception chair'],
            'conference_chairs': ['conference chair', 'meeting chair', 'boardroom chair'],
            'sofas': ['sofa', 'couch', 'settee', '2-seater', '3-seater'],
            'lounge_seating': ['lounge', 'armchair', 'easy chair', 'lounge chair', 'breakout seating']
        }
        
        desking_keywords = {
            'executive_desks': ['executive desk', 'director desk', 'manager desk', 'executive table'],
            'workstations': ['workstation', 'work desk', 'office desk', 'workspace', 'desk system'],
            'meeting_tables': ['meeting table', 'conference table', 'boardroom table', 'discussion table'],
            'pedestals': ['pedestal', 'drawer unit', 'mobile pedestal', 'under desk drawer'],
            'cabinets': ['cabinet', 'cupboard', 'storage cabinet', 'filing cabinet'],
            'lockers': ['locker', 'personal storage', 'staff locker'],
            'partitions': ['partition', 'screen', 'divider', 'panel', 'privacy screen']
        }
        
        # Check seating categories
        for subcategory, keywords in seating_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                return {'category': 'seating', 'subcategory': subcategory}
        
        # Check desking categories
        for subcategory, keywords in desking_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                return {'category': 'desking', 'subcategory': subcategory}
        
        # Default fallback
        if any(word in description_lower for word in ['chair', 'seat', 'stool', 'bench']):
            return {'category': 'seating', 'subcategory': 'task_chairs'}
        elif any(word in description_lower for word in ['table', 'desk']):
            return {'category': 'desking', 'subcategory': 'workstations'}
        
        return {'category': 'general', 'subcategory': 'general'}
    
    def find_alternatives(self, item, budget_option):
        """
        Find alternative products based on budget option using brand database
        """
        alternatives = []
        
        category = item['category']
        subcategory = item['subcategory']
        
        if category in ['seating', 'desking']:
            # Use brand database to find real alternatives
            products = self.brand_db.search_product(budget_option, category, subcategory)
            
            for product in products[:5]:  # Limit to top 5 alternatives
                # Parse price range
                price_range = product['price_range'].split('-')
                avg_price = (float(price_range[0]) + float(price_range[1])) / 2
                
                alt = {
                    'brand': product['brand'],
                    'model': product['model'],
                    'country': product['country'],
                    'description': f"{product['brand']} {product['model']} - {subcategory.replace('_', ' ').title()}",
                    'unit_rate': round(avg_price, 2),
                    'total': round(avg_price * item['qty'], 2),
                    'specs': product['features'],
                    'category': category,
                    'subcategory': subcategory,
                    'source': f"Brand Database - {budget_option}",
                    'website': product['website'],
                    'price_range': product['price_range'],
                    'lead_time': self.estimate_lead_time(budget_option, product['country'])
                }
                alternatives.append(alt)
        
        # If no alternatives found, generate simulated ones
        if not alternatives:
            alternatives = self.generate_simulated_alternatives(item, budget_option)
        
        return alternatives
    
    def estimate_lead_time(self, budget_option, country):
        """Estimate lead time based on budget tier and country"""
        base_lead_times = {
            'budgetary': '2-3 weeks',
            'mid_range': '4-6 weeks',
            'high_end': '6-10 weeks'
        }
        
        # Adjust for country
        if country in ['China', 'Taiwan', 'Malaysia']:
            return base_lead_times.get(budget_option, '4-6 weeks')
        elif country in ['Turkey']:
            return '3-5 weeks' if budget_option == 'budgetary' else '5-7 weeks'
        else:  # European brands
            return base_lead_times.get(budget_option, '6-8 weeks')
    
    def generate_simulated_alternatives(self, item, budget_option):
        """Generate simulated alternatives when brand database doesn't have matches"""
        # Get budget multiplier
        multiplier = self.budget_multipliers.get(budget_option, 1.0)
        original_price = item['unit_rate']
        target_price = original_price * multiplier
        
        if budget_option == 'budgetary':
            return self.generate_budget_alternatives(item, target_price)
        elif budget_option == 'mid_range':
            return self.generate_medium_alternatives(item, target_price)
        else:  # high_end
            return self.generate_premium_alternatives(item, target_price)
    
    def generate_budget_alternatives(self, item, target_price):
        """Generate budget-friendly alternatives"""
        category = item['category']
        
        # Simulated budget brands
        budget_brands = {
            'seating': ['Ikea Business', 'Office Depot', 'Staples'],
            'tables': ['Ikea Business', 'Office Depot', 'HON'],
            'storage': ['Bisley', 'Ikea Business', 'Office Depot'],
            'lighting': ['Philips', 'Osram', 'Generic LED'],
        }
        
        brands = budget_brands.get(category, ['Budget Brand'])
        
        alternatives = []
        for idx, brand in enumerate(brands[:3]):
            alt = {
                'brand': brand,
                'model': f'{category.title()} Model B{idx+1}',
                'description': f'Budget-friendly {item["description"][:50]} alternative',
                'unit_rate': round(target_price * (0.9 + idx * 0.1), 2),
                'total': round(target_price * item['qty'] * (0.9 + idx * 0.1), 2),
                'specs': [
                    'Basic functionality',
                    'Standard warranty (1 year)',
                    'Limited color options',
                    'Good value for money'
                ],
                'source': 'Simulated - Budget Option',
                'lead_time': '2-3 weeks'
            }
            alternatives.append(alt)
        
        return alternatives
    
    def generate_medium_alternatives(self, item, target_price):
        """Generate medium-range alternatives"""
        category = item['category']
        
        # Simulated medium brands
        medium_brands = {
            'seating': ['Sedus', 'Narbutas', 'Sokoa'],
            'tables': ['Narbutas', 'Sedus', 'Vitra'],
            'storage': ['Bisley', 'Sedus', 'Steelcase'],
            'lighting': ['Artemide', 'Flos', 'Louis Poulsen'],
        }
        
        brands = medium_brands.get(category, ['Medium Brand'])
        
        alternatives = []
        for idx, brand in enumerate(brands[:3]):
            alt = {
                'brand': brand,
                'model': f'{category.title()} Model M{idx+1}',
                'description': f'Mid-range {item["description"][:50]} alternative',
                'unit_rate': round(target_price * (0.95 + idx * 0.05), 2),
                'total': round(target_price * item['qty'] * (0.95 + idx * 0.05), 2),
                'specs': [
                    'Excellent build quality',
                    'Extended warranty (3-5 years)',
                    'Multiple finish options',
                    'Ergonomic design',
                    'Sustainable materials'
                ],
                'source': 'Simulated - Medium Range',
                'lead_time': '4-6 weeks'
            }
            alternatives.append(alt)
        
        return alternatives
    
    def generate_premium_alternatives(self, item, target_price):
        """Generate high-end premium alternatives"""
        category = item['category']
        
        # Simulated premium brands
        premium_brands = {
            'seating': ['Herman Miller', 'Knoll', 'Vitra'],
            'tables': ['Vitra', 'Knoll', 'USM'],
            'storage': ['USM', 'Vitra', 'Walter Knoll'],
            'lighting': ['Flos', 'Artemide', 'Louis Poulsen'],
        }
        
        brands = premium_brands.get(category, ['Premium Brand'])
        
        alternatives = []
        for idx, brand in enumerate(brands[:3]):
            alt = {
                'brand': brand,
                'model': f'{category.title()} Model P{idx+1}',
                'description': f'Premium {item["description"][:50]} alternative',
                'unit_rate': round(target_price * (1.0 + idx * 0.1), 2),
                'total': round(target_price * item['qty'] * (1.0 + idx * 0.1), 2),
                'specs': [
                    'Exceptional craftsmanship',
                    'Lifetime warranty',
                    'Fully customizable',
                    'Award-winning design',
                    'Sustainable & certified',
                    'Premium materials'
                ],
                'source': 'Simulated - Premium Option',
                'lead_time': '6-8 weeks'
            }
            alternatives.append(alt)
        
        return alternatives
    
    def search_architonic(self, query, budget_option):
        """
        Search architonic.com for products (placeholder for future implementation)
        Note: Actual scraping should respect robots.txt and terms of service
        """
        # This is a placeholder - in production, implement proper API or scraping
        # with rate limiting and respect for website policies
        
        try:
            # Simulated search results
            results = {
                'query': query,
                'budget': budget_option,
                'results': [],
                'note': 'This is a simulated search. Implement actual API integration.'
            }
            
            return results
        except Exception as e:
            print(f"Search error: {e}")
            return {'results': [], 'error': str(e)}
    
    def get_available_brands(self, tier, category):
        """Get list of available brands for a tier and category"""
        brands = self.brand_db.get_brands_by_tier_and_category(tier, category)
        return [{'name': b['name'], 'country': b['country'], 'website': b['website']} for b in brands]
    
    def get_brand_models(self, tier, category, brand_name, subcategory):
        """Get models for a specific brand and subcategory"""
        models_dict = self.brand_db.get_brand_models(tier, category, brand_name)
        
        if subcategory in models_dict:
            return models_dict[subcategory]
        return []
    
    def get_tiers(self):
        """Get all available budget tiers"""
        return self.brand_db.get_all_tiers()
    
    def get_categories(self):
        """Get all available categories"""
        return self.brand_db.get_all_categories()
    
    def get_subcategories(self, category):
        """Get subcategories for a category"""
        return self.brand_db.get_subcategories(category)
