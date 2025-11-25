"""
Content analysis and detection for blocked or skeleton content.
"""

import logging
import json
import re
from bs4 import BeautifulSoup
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class ContentAnalyzer:
    """Analyzes HTML content to detect if it's blocked or skeleton content."""
    
    def __init__(
        self,
        min_content_length: int = 1000,
        min_text_length: int = 200,
        min_meaningful_elements: int = 5,
        text_to_markup_ratio: float = 0.001
    ):
        """
        Initialize the content analyzer.
        
        Args:
            min_content_length: Minimum total content length in bytes
            min_text_length: Minimum text content length in characters
            min_meaningful_elements: Minimum number of meaningful elements (text, images, links)
            text_to_markup_ratio: Minimum ratio of text to HTML markup
        """
        self.min_content_length = min_content_length
        self.min_text_length = min_text_length
        self.min_meaningful_elements = min_meaningful_elements
        self.text_to_markup_ratio = text_to_markup_ratio
    
    def is_blocked(self, status_code: int) -> bool:
        """
        Check if response is blocked based on status code.
        
        Args:
            status_code: HTTP status code
            
        Returns:
            True if status code indicates blocking
        """
        # 4xx and 5xx indicate blocking or errors
        if 400 <= status_code < 600:
            logger.debug(f"Status code {status_code} indicates blocking")
            return True
        return False
    
    def is_skeleton_content(
        self,
        html_content: str,
        status_code: int = 200
    ) -> Tuple[bool, str]:
        """
        Analyze HTML content to determine if it's skeleton/placeholder content.
        
        Args:
            html_content: HTML content to analyze
            status_code: HTTP status code (default: 200)
            
        Returns:
            Tuple of (is_skeleton: bool, reason: str)
        """
        if not html_content:
            return True, "Empty content"
        
        # Check content length
        content_length = len(html_content)
        if content_length < self.min_content_length:
            logger.debug(f"Content length {content_length} below threshold {self.min_content_length}")
            return True, f"Content too short ({content_length} bytes)"
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
        except Exception as e:
            logger.warning(f"Failed to parse HTML: {e}")
            # If we can't parse, but content is long enough, assume it's valid
            if content_length >= self.min_content_length:
                return False, "Valid content (unparseable but sufficient length)"
            return True, f"Unparseable content: {e}"
        
        # Extract text content
        text_content = soup.get_text(separator=' ', strip=True)
        text_length = len(text_content)
        
        # Check text length
        if text_length < self.min_text_length:
            logger.debug(f"Text length {text_length} below threshold {self.min_text_length}")
            return True, f"Text content too short ({text_length} chars)"
        
        # Count meaningful elements
        meaningful_elements = (
            len(soup.find_all(['p', 'article', 'section', 'div'], string=True)) +
            len(soup.find_all('img', src=True)) +
            len(soup.find_all('a', href=True))
        )
        
        if meaningful_elements < self.min_meaningful_elements:
            logger.debug(f"Meaningful elements {meaningful_elements} below threshold {self.min_meaningful_elements}")
            return True, f"Too few meaningful elements ({meaningful_elements})"
        
        # Check text-to-markup ratio (be more lenient for large pages)
        markup_length = len(html_content) - text_length
        if markup_length > 0:
            ratio = text_length / markup_length
            
            # For large pages (>100KB), use a more lenient threshold
            # Modern web pages (especially e-commerce) have lots of markup
            effective_threshold = self.text_to_markup_ratio
            if content_length > 100000:  # 100KB
                effective_threshold = self.text_to_markup_ratio * 0.5  # Half the threshold for large pages
            
            if ratio < effective_threshold:
                # Only fail if ratio is very low AND content is small
                # Large pages with low ratio are often valid (e.g., Amazon, modern SPAs)
                if content_length < 50000:  # Only strict check for smaller pages
                    logger.debug(f"Text-to-markup ratio {ratio:.4f} below threshold {effective_threshold}")
                    return True, f"Low text-to-markup ratio ({ratio:.4f})"
                else:
                    # Large page with low ratio - likely valid, just log it
                    logger.debug(f"Large page with low text-to-markup ratio {ratio:.4f}, but content size suggests it's valid")
        
        # Check for common skeleton indicators
        skeleton_indicators = [
            'loading',
            'skeleton',
            'placeholder',
            'spinner',
            'shimmer',
            'pulse'
        ]
        
        html_lower = html_content.lower()
        skeleton_count = sum(1 for indicator in skeleton_indicators if indicator in html_lower)
        
        # If many skeleton indicators and low content, likely skeleton
        if skeleton_count >= 3 and text_length < self.min_text_length * 2:
            logger.debug(f"Found {skeleton_count} skeleton indicators with low content")
            return True, f"Multiple skeleton indicators ({skeleton_count})"
        
        # Check for minimal content patterns (lots of divs, little text)
        divs = soup.find_all('div')
        if len(divs) > 20 and text_length < self.min_text_length * 3:
            logger.debug(f"Many divs ({len(divs)}) but little text ({text_length})")
            return True, f"Layout-heavy, content-light ({len(divs)} divs, {text_length} chars)"
        
        return False, "Valid content"
    
    def is_custom_js_skeleton(
        self,
        html_content: str,
        url: str = "",
        min_products: int = 1
    ) -> Tuple[bool, str]:
        """
        Analyze HTML content from custom JS rendering to detect skeleton/empty results.
        This is specifically designed for JS-rendered pages that may have structure
        but no actual content (e.g., search pages with no results).
        
        This method does NOT affect the existing is_skeleton_content() method used
        for static/XHR analysis.
        
        Args:
            html_content: HTML content from custom JS rendering
            url: URL of the page (used to skip skeleton detection for specific domains)
            min_products: Minimum number of products/items expected (default: 1)
            
        Returns:
            Tuple of (is_skeleton: bool, reason: str)
        """
        if not html_content:
            return True, "Empty content"
        
        # Skip skeleton detection for whitelisted domains - accept whatever custom JS returns
        whitelisted_domains = [
            'myntra.com',
            'sangeethamobiles.com',
            'paiinternational.in',
            'myg.in',
            'darlingretail.com',
            'ajio.com',
            'xtepindia.com',
            'lakhanifootwear.com',
            'skechers.in',
            'somethingsbrewing.in',
            'shop.ttkprestige.com',
            'reliancedigital.in',
            'wonderchef.com',
            'domesticappliances.philips.co.in',
            'agarolifestyle.com',
            'naaptol.com',
            'rbzone.com'
        ]
        if url:
            url_lower = url.lower()
            for domain in whitelisted_domains:
                if domain in url_lower:
                    logger.debug(f"Skipping skeleton detection for whitelisted domain ({domain}): {url}")
                    return False, f"{domain} - accepting custom JS result"
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
        except Exception as e:
            logger.warning(f"Failed to parse HTML for custom JS skeleton check: {e}")
            return False, "Unparseable content, assuming valid"
        
        html_lower = html_content.lower()
        
        # 1. Check for "no results" messages (case-insensitive)
        no_results_patterns = [
            r'oops!?\s*no\s+results?\s+found',
            r'no\s+results?\s+found',
            r'nothing\s+found',
            r'no\s+products?\s+found',
            r'no\s+items?\s+found',
            r'try\s+searching\s+for\s+something\s+else',
            r'don\'?t\s+worry,\s+try\s+searching',
            r'no\s+results?\s+available',
            r'we\s+couldn\'?t\s+find',
            r'no\s+matches?\s+found'
        ]
        
        for pattern in no_results_patterns:
            if re.search(pattern, html_lower):
                logger.debug(f"Found 'no results' pattern: {pattern}")
                return True, f"Found 'no results' message"
        
        # 2. Extract and check JSON data from script tags
        script_tags = soup.find_all('script', type='application/json')
        script_tags.extend(soup.find_all('script', id=re.compile(r'__NEXT_DATA__|__INITIAL_STATE__|__APP_DATA__', re.I)))
        
        # Also check for inline JSON in script tags
        all_scripts = soup.find_all('script')
        for script in all_scripts:
            script_content = script.string or ""
            if not script_content:
                continue
            
            # Look for JSON data patterns
            json_patterns = [
                r'"products"\s*:\s*\[\s*\]',  # products: []
                r'"items"\s*:\s*\[\s*\]',     # items: []
                r'"results"\s*:\s*\[\s*\]',   # results: []
                r'"productsCount"\s*:\s*0',    # productsCount: 0
                r'"totalProductsCount"\s*:\s*0',  # totalProductsCount: 0
                r'"itemCount"\s*:\s*0',        # itemCount: 0
                r'"count"\s*:\s*0\s*,',       # count: 0
            ]
            
            for pattern in json_patterns:
                if re.search(pattern, script_content):
                    logger.debug(f"Found empty product listing pattern: {pattern}")
                    return True, f"Empty product listing detected"
            
            # Try to parse as JSON and check for empty arrays
            try:
                # Look for JSON objects in script content
                json_match = re.search(r'\{[^{}]*"products"[^{}]*\}', script_content)
                if json_match:
                    json_str = json_match.group(0)
                    data = json.loads(json_str)
                    if isinstance(data, dict):
                        # Check various product-related keys
                        for key in ['products', 'items', 'results', 'data']:
                            if key in data:
                                value = data[key]
                                if isinstance(value, list) and len(value) == 0:
                                    return True, f"Empty {key} array in JSON data"
                                if isinstance(value, dict):
                                    # Check for count fields
                                    for count_key in ['count', 'total', 'productsCount', 'itemCount', 'totalProductsCount']:
                                        if count_key in value and value[count_key] == 0:
                                            return True, f"Zero {count_key} in JSON data"
            except (json.JSONDecodeError, AttributeError):
                # Not valid JSON, continue checking
                pass
        
        # 3. Check for pages with navigation/header but no product cards or listings
        # Look for common e-commerce/product listing indicators
        product_indicators = [
            soup.find_all(class_=re.compile(r'product|item|listing|card', re.I)),
            soup.find_all(id=re.compile(r'product|item|listing', re.I)),
            soup.find_all('article'),
            soup.find_all(attrs={'data-product-id': True}),
            soup.find_all(attrs={'data-item-id': True}),
        ]
        
        # Flatten and count unique product indicators
        product_elements = set()
        for indicator_list in product_indicators:
            product_elements.update(indicator_list)
        
        # Check if we have navigation/header structure
        has_navigation = (
            len(soup.find_all(['nav', 'header'])) > 0 or
            len(soup.find_all(class_=re.compile(r'nav|header|menu', re.I))) > 0
        )
        
        # If we have navigation but no products, likely skeleton
        if has_navigation and len(product_elements) < min_products:
            # But check if there's substantial text content (might be a content page, not product listing)
            text_content = soup.get_text(separator=' ', strip=True)
            text_length = len(text_content)
            
            # If text is very short, it's likely skeleton
            if text_length < 500:
                logger.debug(f"Has navigation but no products and minimal text ({text_length} chars)")
                return True, f"Navigation present but no products and minimal content"
            
            # Check for error/empty state messages in visible text
            visible_text_lower = text_content.lower()
            if any(phrase in visible_text_lower for phrase in ['no results', 'nothing found', 'try searching', 'oops']):
                return True, f"Navigation present but empty state message detected"
        
        # 4. Check for structure-heavy, content-light pages
        # Count structural elements vs content elements
        structural_elements = len(soup.find_all(['div', 'nav', 'header', 'footer', 'aside']))
        content_elements = len(soup.find_all(['article', 'section', 'main', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']))
        
        text_content = soup.get_text(separator=' ', strip=True)
        text_length = len(text_content)
        
        # If lots of structure but little content, might be skeleton
        if structural_elements > 50 and content_elements < 5 and text_length < 1000:
            logger.debug(f"Structure-heavy ({structural_elements} divs) but content-light ({content_elements} content elements, {text_length} chars)")
            return True, f"Structure-heavy but content-light page"
        
        # 5. Check for loading/error states in class names or IDs
        loading_indicators = soup.find_all(class_=re.compile(r'loading|error|empty|no-results|no-results-found', re.I))
        loading_indicators.extend(soup.find_all(id=re.compile(r'loading|error|empty|no-results', re.I)))
        
        if len(loading_indicators) > 0:
            # Check if these are visible/active
            for indicator in loading_indicators:
                # Check if element is likely visible (not hidden)
                style = indicator.get('style', '')
                classes = ' '.join(indicator.get('class', []))
                if 'display: none' not in style.lower() and 'hidden' not in classes.lower():
                    logger.debug(f"Found visible loading/error indicator")
                    return True, f"Visible loading/error state detected"
        
        return False, "Valid content"
    
    def should_fallback(
        self,
        html_content: Optional[str],
        status_code: int
    ) -> Tuple[bool, str]:
        """
        Determine if we should fallback to next method.
        
        Args:
            html_content: HTML content (None if request failed)
            status_code: HTTP status code
            
        Returns:
            Tuple of (should_fallback: bool, reason: str)
        """
        # Check if blocked
        if self.is_blocked(status_code):
            return True, f"Request blocked (status {status_code})"
        
        # If no content, fallback
        if html_content is None:
            return True, "No content received"
        
        # Check if skeleton
        is_skeleton, reason = self.is_skeleton_content(html_content, status_code)
        if is_skeleton:
            return True, f"Skeleton content: {reason}"
        
        return False, "Content is valid"

