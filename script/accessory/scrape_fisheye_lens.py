#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scrape Fisheye lens data from official website
Extract macro and wide conversion lenses
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import os

def scrape_fisheye_lens_page():
    """Scrape the Fisheye lens page for conversion lenses"""
    url = "https://www.fisheye-jp.com/products/lens/lens.html"
    
    try:
        print("Fetching Fisheye lens page...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        lenses = []
        
        # Look for lens product information
        # Method 1: Find product titles and descriptions
        product_elements = soup.find_all(['h2', 'h3', 'h4', 'div', 'p'], string=re.compile(r'.*(マクロ|ワイド|Macro|Wide|Conversion|コンバージョン).*', re.IGNORECASE))
        
        for element in product_elements:
            text = element.get_text(strip=True)
            
            # Look for lens model names
            if re.search(r'(UWL|WWL|SMC|CMC|MFO|EMWL|MWL|WFL)', text):
                lenses.append(text)
        
        # Method 2: Look for specific product links
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            text = link.get_text(strip=True)
            
            # Check if this looks like a lens product
            if any(model in text for model in ['UWL', 'WWL', 'SMC', 'CMC', 'MFO', 'EMWL', 'MWL', 'WFL']):
                lenses.append(text)
        
        # Method 3: Look in product listings
        product_lists = soup.find_all(['ul', 'ol', 'div'], class_=re.compile(r'product|item|list'))
        for product_list in product_lists:
            items = product_list.find_all(['li', 'div', 'span'])
            for item in items:
                text = item.get_text(strip=True)
                if any(model in text for model in ['UWL', 'WWL', 'SMC', 'CMC', 'MFO', 'EMWL', 'MWL', 'WFL']):
                    lenses.append(text)
        
        return list(set(lenses))  # Remove duplicates
        
    except Exception as e:
        print(f"Error scraping Fisheye page: {e}")
        return []

def extract_lens_info(lens_text):
    """Extract lens model and type from text"""
    
    # Define lens patterns
    macro_patterns = [
        r'.*SMC.*',  # Super Macro Conversion
        r'.*CMC.*',  # Compact Macro Conversion  
        r'.*MFO.*',  # Mid-Range Focus Optimizer
        r'.*マクロ.*',
        r'.*Macro.*'
    ]
    
    wide_patterns = [
        r'.*WWL.*',  # Wide Water Lens
        r'.*UWL.*',  # Underwater Wide Lens
        r'.*EMWL.*', # Macro Wide Lens
        r'.*MWL.*',  # Macro Wide Lens
        r'.*WFL.*',  # Wide Fisheye Lens
        r'.*ワイド.*',
        r'.*Wide.*'
    ]
    
    lens_type = 'unknown'
    
    # Determine type
    for pattern in macro_patterns:
        if re.match(pattern, lens_text, re.IGNORECASE):
            lens_type = 'macro'
            break
    
    if lens_type == 'unknown':
        for pattern in wide_patterns:
            if re.match(pattern, lens_text, re.IGNORECASE):
                lens_type = 'wide'
                break
    
    # Extract model name (look for common model patterns)
    model_match = re.search(r'(UWL-\w+|WWL-\w+|SMC-\w+|CMC-\w+|MFO-\w+|EMWL|MWL-\w+|WFL\w+)', lens_text)
    if model_match:
        model = model_match.group(1)
    else:
        # Use the full text as model if no specific pattern found
        model = lens_text.strip()
    
    return model, lens_type

def create_fisheye_lens_data():
    """Create Fisheye lens data in the required format"""
    
    # Based on the WebFetch results, create comprehensive lens data
    fisheye_lenses = [
        # Macro Conversion Lenses
        "NA Mid-Range Focus Optimizer MFO-3",
        "NA Super Macro Conversion Lens SMC-3", 
        "NA Mid-Range Focus Optimizer MFO-1",
        "NA Super Macro Conversion Lens SMC-2",
        "NA Compact Macro Conversion Lens CMC-2",
        "NA Compact Macro Conversion Lens CMC-1",
        "WF Macro Conversion Lens WFL03 +12",
        "Macro Mate M52/M67",
        
        # Wide Conversion Lenses
        "NA Wide Conversion Lens WWL-1B",
        "NA Macro Wide Conversion Lens EMWL",
        "NA Wide Conversion Lens WWL-C", 
        "NA Macro Wide Conversion Lens MWL-1",
        "WF Wide Air Lens WFL12M67",
        "WF Wide Air Lens WFL11M52",
        "WF Wide Conversion Lens WFL07 Cell",
        "WF Wide Conversion Lens UWL-24M52MG",
        "WF Wide Conversion Lens UWL-24M52R",
        "FIX Fisheye Conversion Lens UWL-28M52MG",
        "FIX Fisheye Conversion Lens UWL-28M52R"
    ]
    
    lens_data = []
    
    for lens_name in fisheye_lenses:
        model, lens_type = extract_lens_info(lens_name)
        
        # Format according to accessory.json structure
        lens_item = {
            "name": lens_name,
            "company": "Fisheye"
        }
        
        lens_data.append(lens_item)
    
    return lens_data

def save_fisheye_lens_data(lens_data, output_path="../../data/processed/accessory/"):
    """Save the lens data to JSON file"""
    
    os.makedirs(output_path, exist_ok=True)
    
    # Separate macro and wide lenses
    macro_lenses = []
    wide_lenses = []
    
    for lens in lens_data:
        name = lens['name'].lower()
        if any(keyword in name for keyword in ['macro', 'マクロ', 'smc', 'cmc', 'mfo']):
            macro_lenses.append(lens)
        elif any(keyword in name for keyword in ['wide', 'ワイド', 'wwl', 'uwl', 'wfl', 'emwl', 'mwl']):
            wide_lenses.append(lens)
    
    # Save macro lenses
    if macro_lenses:
        macro_filename = f"{output_path}fisheye_macro_lens.json"
        with open(macro_filename, 'w', encoding='utf-8') as f:
            json.dump(macro_lenses, f, ensure_ascii=False, indent=4)
        print(f"Saved {len(macro_lenses)} macro lenses to {macro_filename}")
    
    # Save wide lenses  
    if wide_lenses:
        wide_filename = f"{output_path}fisheye_wide_lens.json"
        with open(wide_filename, 'w', encoding='utf-8') as f:
            json.dump(wide_lenses, f, ensure_ascii=False, indent=4)
        print(f"Saved {len(wide_lenses)} wide lenses to {wide_filename}")
    
    # Save all lenses
    all_filename = f"{output_path}fisheye_all_lens.json"
    with open(all_filename, 'w', encoding='utf-8') as f:
        json.dump(lens_data, f, ensure_ascii=False, indent=4)
    print(f"Saved all {len(lens_data)} Fisheye lenses to {all_filename}")
    
    return macro_lenses, wide_lenses

def main():
    """Main function"""
    print("Starting Fisheye lens data extraction...")
    
    # Create lens data based on WebFetch results
    lens_data = create_fisheye_lens_data()
    
    print(f"Created data for {len(lens_data)} Fisheye lenses")
    
    # Save the data
    macro_lenses, wide_lenses = save_fisheye_lens_data(lens_data)
    
    print(f"\nSummary:")
    print(f"Macro conversion lenses: {len(macro_lenses)}")
    print(f"Wide conversion lenses: {len(wide_lenses)}")
    print(f"Total Fisheye lenses: {len(lens_data)}")
    
    # Show samples
    print(f"\nSample macro lenses:")
    for lens in macro_lenses[:3]:
        print(f"  - {lens['name']}")
    
    print(f"\nSample wide lenses:")
    for lens in wide_lenses[:3]:
        print(f"  - {lens['name']}")

if __name__ == "__main__":
    main()