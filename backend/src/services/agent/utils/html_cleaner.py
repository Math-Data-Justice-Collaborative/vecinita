#!/usr/bin/env python3
"""
HTML Cleaner Module

Provides comprehensive HTML cleaning utilities using BeautifulSoup to extract
main content and remove boilerplate elements like headers, footers, navigation,
modals, and other non-content HTML structures.
"""

import logging
import re
from typing import Optional, List
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)


class HTMLCleaner:
    """
    Comprehensive HTML cleaner using BeautifulSoup to extract main content
    and remove boilerplate, navigation, and other non-content elements.
    """

    # CSS classes and IDs commonly associated with boilerplate content
    BOILERPLATE_CLASSES = [
        # Navigation and headers
        'navbar', 'navigation', 'nav', 'header', 'site-header',
        # Footers
        'footer', 'site-footer', 'usa-footer',
        # Sidebars and widgets
        'sidebar', 'aside', 'widget', 'widget-area',
        # Modals and popups
        'modal', 'popup', 'dialog', 'lightbox',
        # Ads and tracking
        'advertisement', 'ad', 'banner', 'advertisement-container',
        # Social and sharing
        'social', 'share', 'social-share', 'social-links',
        # Comments (usually not main content)
        'comments', 'comment-section',
        # Breadcrumbs
        'breadcrumb', 'breadcrumbs',
        # Related content
        'related', 'related-posts', 'similar-posts',
        # Cookie notices and alerts
        'cookie', 'cookie-banner', 'cookie-notice', 'consent',
        # Tracking and analytics
        'analytics', 'tracking', 'facebook-pixel',
        # Qualtrics and other survey tools
        'qualtrics', 'ntas',
        # Skip links
        'skip-to-content', 'skip-link',
    ]

    BOILERPLATE_IDS = [
        'navbar', 'navigation', 'header', 'footer', 'sidebar', 'aside',
        'modal', 'modal-content', 'popup', 'ads', 'comments', 'social',
        'cookie-banner', 'cookie-notice', 'ntas-frame', 'qualtrics',
    ]

    BOILERPLATE_TAGS = [
        'header', 'footer', 'nav', 'aside', 'script', 'style',
        'noscript', 'meta', 'link', 'iframe'
    ]

    # Tags that are good sources of main content
    CONTENT_CONTAINERS = [
        'main', 'article', 'section', 'div[role="main"]', 'div.main-content',
        'div.content', 'div.article', 'div.post', 'div.entry'
    ]

    @staticmethod
    def is_boilerplate_element(element) -> bool:
        """Check if an element is likely boilerplate content."""
        # Skip non-tag elements
        if not hasattr(element, 'name') or element.name is None:
            return False

        if element.name in HTMLCleaner.BOILERPLATE_TAGS:
            return True

        # Check classes
        element_classes = element.get(
            'class', []) if hasattr(element, 'get') else []
        for class_name in element_classes:
            for boilerplate_class in HTMLCleaner.BOILERPLATE_CLASSES:
                if boilerplate_class.lower() in class_name.lower():
                    return True

        # Check IDs
        element_id = element.get('id', '') if hasattr(element, 'get') else ''
        for boilerplate_id in HTMLCleaner.BOILERPLATE_IDS:
            if boilerplate_id.lower() in element_id.lower():
                return True

        # Check role attribute
        role = element.get('role', '').lower(
        ) if hasattr(element, 'get') else ''
        if role in ['navigation', 'complementary', 'doc-pagelist']:
            return True

        return False

    @staticmethod
    def is_likely_main_content_container(element) -> bool:
        """Check if an element is likely to contain main content."""
        if not hasattr(element, 'get') or not hasattr(element, 'name'):
            return False

        element_classes = element.get('class', [])

        element_id = element.get('id', '')
        element_name = element.name

        # Check for explicit main content indicators
        main_indicators = ['main', 'content',
                           'article', 'post', 'entry', 'body']

        for indicator in main_indicators:
            if indicator in element_id.lower():
                return True
            for class_name in element_classes:
                if indicator in class_name.lower():
                    return True

        return element_name == 'main' or element_name == 'article'

    @staticmethod
    def should_remove_element(element) -> bool:
        """Determine if an element should be completely removed."""
        # Skip non-tag elements
        if not hasattr(element, 'name') or element.name is None:
            return False

        # Remove if it's clearly boilerplate
        if HTMLCleaner.is_boilerplate_element(element):
            return True

        # Remove very short text nodes that look like UI elements
        text_content = element.get_text(strip=True)
        if len(text_content) < 5 and element.name in ['li', 'span', 'div', 'a']:
            # But keep if it's part of a larger structure
            if element.parent and element.parent.name not in ['p', 'article', 'section']:
                return False

        # Remove elements with certain data attributes
        if hasattr(element, 'attrs'):
            data_attrs = element.attrs
            for attr, value in data_attrs.items():
                if 'track' in attr.lower() or 'analytics' in str(value).lower():
                    return True

        return False

    @staticmethod
    def clean_html(html_content: str, extract_main: bool = True) -> str:
        """
        Clean HTML content by removing boilerplate and extracting main content.

        Args:
            html_content: Raw HTML string
            extract_main: If True, try to extract main content container

        Returns:
            Cleaned text content
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove script and style tags completely
            for tag in soup(['script', 'style', 'noscript', 'meta', 'link']):
                tag.decompose()

            # Try to find and extract main content first
            if extract_main:
                main_content = HTMLCleaner._extract_main_content(soup)
                if main_content:
                    soup = main_content

            # Remove boilerplate elements
            removed_count = 0
            for element in list(soup.find_all()):
                if HTMLCleaner.should_remove_element(element):
                    element.decompose()
                    removed_count += 1

            # Remove elements with boilerplate patterns in class/id
            for element in list(soup.find_all()):
                if HTMLCleaner.is_boilerplate_element(element):
                    # For tags like footer and nav, remove completely
                    if element.name in ['footer', 'nav', 'header']:
                        element.decompose()
                        removed_count += 1
                    # For divs and sections, check if they have substantial content
                    else:
                        text_length = len(element.get_text(strip=True))
                        if text_length < 100:  # Small boilerplate elements
                            element.decompose()
                            removed_count += 1

            # Get text and clean it
            text = soup.get_text(separator='\n', strip=True)
            text = HTMLCleaner._clean_text(text)

            log.debug(
                f"Removed {removed_count} boilerplate elements during HTML cleaning")
            return text

        except Exception as e:
            log.error(f"Error during HTML cleaning: {e}")
            return html_content

    @staticmethod
    def _extract_main_content(soup) -> Optional[BeautifulSoup]:
        """
        Try to extract the main content container from the document.

        Returns:
            BeautifulSoup object containing main content, or None
        """
        # Priority: Look for these tags/classes in order
        selectors = [
            ('main', None),
            ('article', None),
            ('div', {'class': lambda x: x and 'main' in ' '.join(x).lower()}),
            ('div', {'id': lambda x: x and 'main' in x.lower()}),
            ('div', {'role': 'main'}),
            ('section', {
             'class': lambda x: x and 'content' in ' '.join(x).lower()}),
        ]

        for tag, attrs in selectors:
            if attrs is None:
                element = soup.find(tag)
            else:
                element = soup.find(tag, attrs)

            if element:
                text_content = element.get_text(strip=True)
                # Make sure it has substantial content
                if len(text_content) > 200:
                    log.debug(f"Found main content in <{tag}> element")
                    # Create new soup from this element to continue processing
                    return BeautifulSoup(str(element), 'html.parser')

        return None

    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean extracted text content."""
        # Remove excessive whitespace
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n+', '\n\n', text)

        # Remove common boilerplate text patterns
        boilerplate_patterns = [
            r'cookie\s+policy', r'privacy\s+policy', r'terms\s+of\s+service',
            r'terms\s+&\s+conditions', r'terms\s+and\s+conditions',
            r'©\s*(\d{4})?.*all\s+rights\s+reserved',
            r'all\s+rights\s+reserved', r'site\s+map', r'contact\s+us',
            r'log\s*in|sign\s*up|register', r'search(\s+site)?',
            r'skip\s+to\s+(main\s+)?content', r'return\s+to\s+top',
            r'social\s+media\s+links?', r'follow\s+us',
            # Dates like "Last Reviewed/Updated: 2025-04-10"
            r'last\s+(reviewed|updated).*\d{4}',
        ]

        for pattern in boilerplate_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)

        # Remove lines that are too short (likely UI elements)
        lines = text.split('\n')
        cleaned_lines = [line.strip()
                         for line in lines if len(line.strip().split()) > 2]
        text = '\n'.join(cleaned_lines)

        # Remove any remaining excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text.strip()

    @staticmethod
    def clean_html_to_text(html_content: str) -> str:
        """
        Convenience method: Clean HTML and return plain text.

        Args:
            html_content: Raw HTML string

        Returns:
            Cleaned plain text
        """
        return HTMLCleaner.clean_html(html_content, extract_main=True)
