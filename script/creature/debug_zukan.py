#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug script to analyze scuba-monsters.com/zukan/ page structure
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin

def debug_zukan_page():
    """Debug the zukan page to understand its structure"""
    base_url = "https://scuba-monsters.com/zukan/"
    
    try:
        print("Fetching and analyzing zukan page...")
        response = requests.get(base_url, timeout=30)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print("=== PAGE TITLE ===")
        title = soup.find('title')
        if title:
            print(f"Title: {title.get_text()}")
        
        print("\n=== ALL LINKS ===")
        links = soup.find_all('a', href=True)
        print(f"Total links found: {len(links)}")
        
        zukan_links = []
        for i, link in enumerate(links):
            href = link['href']
            text = link.get_text(strip=True)
            if '/zukan/' in href or 'group' in href:
                full_url = urljoin(base_url, href)
                zukan_links.append((text, full_url))
                print(f"  {i+1}: '{text}' -> {full_url}")
        
        print(f"\nZukan-related links: {len(zukan_links)}")
        
        print("\n=== JAVASCRIPT/DYNAMIC CONTENT CHECK ===")
        scripts = soup.find_all('script')
        print(f"Found {len(scripts)} script tags")
        
        # Look for potential AJAX endpoints or data
        for script in scripts:
            if script.string:
                content = script.string
                if 'api' in content.lower() or 'ajax' in content.lower() or 'fetch' in content.lower():
                    print("Found potential API/AJAX content in script")
                    # Show first 200 chars
                    print(f"  Content preview: {content[:200]}...")
        
        print("\n=== MAIN CONTENT STRUCTURE ===")
        # Look for main content areas
        main_content = soup.find('main') or soup.find('div', class_=re.compile(r'main|content|container'))
        if main_content:
            print("Found main content area")
            # Look for creature-related elements
            creature_elements = main_content.find_all(['div', 'ul', 'li'], class_=re.compile(r'creature|fish|zukan|card|item|list'))
            print(f"Found {len(creature_elements)} potential creature elements")
            
            for elem in creature_elements[:5]:  # Show first 5
                print(f"  Element: {elem.name}, classes: {elem.get('class', [])}")
                text = elem.get_text(strip=True)[:100]
                print(f"    Text: {text}...")
        
        print("\n=== FORM AND INPUT ELEMENTS ===")
        forms = soup.find_all('form')
        inputs = soup.find_all(['input', 'select', 'textarea'])
        print(f"Forms: {len(forms)}, Inputs: {len(inputs)}")
        
        print("\n=== META AND DATA ATTRIBUTES ===")
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            if meta.get('name') or meta.get('property'):
                print(f"  Meta: {meta.get('name') or meta.get('property')} = {meta.get('content', '')[:100]}")
        
        # Check for data attributes
        data_elements = soup.find_all(attrs=lambda x: x and any(k.startswith('data-') for k in x.keys()))
        print(f"\nElements with data attributes: {len(data_elements)}")
        for elem in data_elements[:5]:
            data_attrs = {k: v for k, v in elem.attrs.items() if k.startswith('data-')}
            print(f"  {elem.name}: {data_attrs}")
        
        return zukan_links
        
    except Exception as e:
        print(f"Error analyzing page: {e}")
        return []

def test_group_page(group_url):
    """Test fetching a specific group page"""
    print(f"\n=== TESTING GROUP PAGE: {group_url} ===")
    
    try:
        response = requests.get(group_url, timeout=20)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print("=== PAGE TITLE ===")
        title = soup.find('title')
        if title:
            print(f"Title: {title.get_text()}")
        
        print("\n=== CREATURE NAMES ===")
        # Look for creature names in various elements
        potential_creatures = []
        
        # Method 1: Look in list items
        list_items = soup.find_all('li')
        for li in list_items:
            text = li.get_text(strip=True)
            if text and 2 <= len(text) <= 20 and re.match(r'^[ひらがなカタカナ漢字ー・（）]+$', text):
                potential_creatures.append(text)
        
        # Method 2: Look in divs with creature-like classes
        creature_divs = soup.find_all('div', class_=re.compile(r'name|title|creature|fish'))
        for div in creature_divs:
            text = div.get_text(strip=True)
            if text and 2 <= len(text) <= 20 and re.match(r'^[ひらがなカタカナ漢字ー・（）]+$', text):
                potential_creatures.append(text)
        
        # Method 3: Look in headers
        headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        for header in headers:
            text = header.get_text(strip=True)
            if text and 2 <= len(text) <= 20 and re.match(r'^[ひらがなカタカナ漢字ー・（）]+$', text):
                potential_creatures.append(text)
        
        # Remove duplicates and filter
        unique_creatures = list(set(potential_creatures))
        # Filter out common navigation words
        filtered_creatures = [name for name in unique_creatures 
                            if not any(word in name for word in ['ホーム', 'メニュー', 'ナビ', '検索', '図鑑', 'サイト'])]
        
        print(f"Found {len(filtered_creatures)} potential creature names:")
        for name in filtered_creatures[:10]:  # Show first 10
            print(f"  - {name}")
        
        return filtered_creatures
        
    except Exception as e:
        print(f"Error testing group page: {e}")
        return []

def main():
    """Main debug function"""
    print("Starting zukan page structure analysis...")
    
    # Analyze main page
    zukan_links = debug_zukan_page()
    
    # Test a few group pages
    if zukan_links:
        print(f"\n=== TESTING FIRST FEW GROUP PAGES ===")
        all_creatures = []
        
        for i, (name, url) in enumerate(zukan_links[:3]):  # Test first 3
            if 'group' in url:
                creatures = test_group_page(url)
                all_creatures.extend(creatures)
                print(f"\nGroup '{name}': {len(creatures)} creatures found")
                
        print(f"\nTotal unique creatures from tested pages: {len(set(all_creatures))}")
        
        # Save sample data
        if all_creatures:
            sample_data = [{"id": i+1, "name": name, "category": "unknown"} 
                          for i, name in enumerate(set(all_creatures))]
            
            with open("../../data/processed/creature/zukan_debug_sample.json", 'w', encoding='utf-8') as f:
                json.dump(sample_data, f, ensure_ascii=False, indent=2)
            print(f"Saved sample data to zukan_debug_sample.json")

if __name__ == "__main__":
    main()