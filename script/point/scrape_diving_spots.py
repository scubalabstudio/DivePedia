#!/usr/bin/env python3
"""
Diving spots scraper for scuba-monsters.com
Extracts prefecture and spot names from the diving spots index page
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time
from urllib.parse import urljoin

def scrape_diving_spots():
    """Scrape diving spots from scuba-monsters.com"""
    base_url = "https://scuba-monsters.com/spot/"
    
    try:
        print("Fetching diving spots page...")
        response = requests.get(base_url, timeout=30)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        spots = []
        
        # Look for different possible structures
        # Try to find prefecture sections or grouped content
        
        # Method 1: Look for prefecture headers followed by spot links
        prefecture_sections = soup.find_all(['h2', 'h3', 'h4'], string=re.compile(r'(県|府|都|道)'))
        
        current_prefecture = None
        
        for section in soup.find_all(['div', 'section', 'ul', 'li', 'a']):
            text = section.get_text(strip=True)
            
            # Check if this is a prefecture name
            if re.search(r'(北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|埼玉県|千葉県|東京都|神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|三重県|滋賀県|京都府|大阪府|兵庫県|奈良県|和歌山県|鳥取県|島根県|岡山県|広島県|山口県|徳島県|香川県|愛媛県|高知県|福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県)', text):
                current_prefecture = text
                continue
            
            # Look for diving spot names (exclude common navigation words)
            if text and current_prefecture and len(text) > 1:
                exclude_words = ['トップ', 'ホーム', 'ダイビング', 'スポット', 'ポイント', 'マップ', '地図', 'エリア', '一覧', 'リスト', 'メニュー', 'ナビ']
                if not any(word in text for word in exclude_words) and not text.startswith('http'):
                    spots.append({
                        "name": text,
                        "prefecture": current_prefecture
                    })
        
        # Method 2: Look for specific patterns in links and text
        # Find all links that might be diving spots
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)
            
            # Check if this looks like a diving spot URL
            if '/spot/' in href and text and len(text) > 1:
                # Try to extract prefecture from URL or surrounding context
                # Look for prefecture info in parent elements
                parent_text = ""
                parent = link.parent
                while parent and len(parent_text) < 100:
                    parent_text += parent.get_text(strip=True)
                    parent = parent.parent
                    if not parent:
                        break
                
                # Extract prefecture from context
                prefecture_match = re.search(r'(北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|埼玉県|千葉県|東京都|神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|三重県|滋賀県|京都府|大阪府|兵庫県|奈良県|和歌山県|鳥取県|島根県|岡山県|広島県|山口県|徳島県|香川県|愛媛県|高知県|福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県)', parent_text)
                
                if prefecture_match:
                    prefecture = prefecture_match.group(1)
                    
                    # Clean up spot name
                    spot_name = re.sub(r'^\d+\.?\s*', '', text)  # Remove leading numbers
                    spot_name = re.sub(r'\s+', ' ', spot_name).strip()  # Clean whitespace
                    
                    if spot_name and len(spot_name) > 1:
                        # Check if already exists
                        existing = next((s for s in spots if s['name'] == spot_name and s['prefecture'] == prefecture), None)
                        if not existing:
                            spots.append({
                                "name": spot_name,
                                "prefecture": prefecture
                            })
        
        # Remove duplicates and sort
        unique_spots = []
        seen = set()
        for spot in spots:
            key = (spot['name'], spot['prefecture'])
            if key not in seen:
                seen.add(key)
                unique_spots.append(spot)
        
        # Sort by prefecture, then by name
        unique_spots.sort(key=lambda x: (x['prefecture'], x['name']))
        
        print(f"Found {len(unique_spots)} unique diving spots")
        
        return unique_spots
        
    except requests.RequestException as e:
        print(f"Error fetching page: {e}")
        return []
    except Exception as e:
        print(f"Error parsing page: {e}")
        return []

def save_to_json(spots, filename):
    """Save spots data to JSON file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(spots, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(spots)} spots to {filename}")
    except Exception as e:
        print(f"Error saving to file: {e}")

def main():
    """Main function"""
    print("Starting diving spots scraper...")
    
    spots = scrape_diving_spots()
    
    if spots:
        # Save to processed directory
        output_file = "../../data/processed/point/diving_spots.json"
        save_to_json(spots, output_file)
        
        # Print summary
        print("\nSummary by prefecture:")
        prefecture_counts = {}
        for spot in spots:
            pref = spot['prefecture']
            prefecture_counts[pref] = prefecture_counts.get(pref, 0) + 1
        
        for pref, count in sorted(prefecture_counts.items()):
            print(f"{pref}: {count} spots")
    else:
        print("No spots found")

if __name__ == "__main__":
    main()