# scrape_izuzuki_all_simple.py
import requests
from bs4 import BeautifulSoup
import json
import sys
import time
from datetime import datetime
from urllib.parse import urljoin

def get_category_links(main_url: str) -> list:
    """
    メインページからカテゴリーリンクを取得
    """
    try:
        print(f"カテゴリーリンクを取得中...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(main_url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        category_links = []
        
        # 種類別セクションを探す
        for thumlist in soup.find_all('div', class_='thumlist'):
            p = thumlist.find('p', class_='kaMei_slug')
            if p and '種類別' in p.get_text():
                for item in thumlist.find_all('div', class_='thumitem'):
                    link = item.find('a')
                    if link and link.get('href'):
                        br = link.find('br')
                        if br and br.next_sibling:
                            name = br.next_sibling.strip() if isinstance(br.next_sibling, str) else br.next_sibling.get_text(strip=True)
                            url = urljoin(main_url, link.get('href'))
                            category_links.append({'name': name, 'url': url})
                            print(f"  発見: {name}")
        
        return category_links
        
    except Exception as e:
        print(f"エラー: {e}")
        return []

def scrape_page_simple(url: str) -> list:
    """
    ページから生き物データを取得（シンプル版）
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        creatures = []
        
        for thumlist in soup.find_all('div', class_='thumlist'):
            # 科名を取得
            family_elem = thumlist.find('p', class_=['kaMei_fish', 'kaMei_slug'])
            family_name = family_elem.get_text(strip=True) if family_elem else ''
            
            # 生き物を取得
            for item in thumlist.find_all('div', class_='thumitem'):
                link = item.find('a')
                if link:
                    name = ""
                    br = link.find('br')
                    if br and br.next_sibling:
                        if isinstance(br.next_sibling, str):
                            name = br.next_sibling.strip()
                        else:
                            name = br.next_sibling.get_text(strip=True)
                    
                    if not name:
                        texts = list(link.stripped_strings)
                        if texts:
                            name = texts[-1]
                    
                    if name:
                        creatures.append({
                            'name': name,
                            'family': family_name
                        })
        
        return creatures
        
    except Exception as e:
        print(f"エラー: {e}")
        return []

def main():
    """メイン処理"""
    
    if len(sys.argv) > 1:
        main_url = sys.argv[1]
    else:
        print("URLを入力してください:")
        main_url = input().strip()
        if not main_url:
            print("エラー: URLが指定されていません")
            sys.exit(1)
    
    all_creatures = []
    creature_id = 1
    
    # 単一ページか複数カテゴリーページかを判定
    if 'index.html' in main_url and '/Slug/' in main_url:
        # メインページから複数カテゴリーを取得
        print("複数カテゴリーを取得します")
        category_links = get_category_links(main_url)
        
        for i, category in enumerate(category_links, 1):
            print(f"\n[{i}/{len(category_links)}] {category['name']}")
            creatures = scrape_page_simple(category['url'])
            
            for creature in creatures:
                creature['id'] = creature_id
                all_creatures.append(creature)
                creature_id += 1
            
            print(f"  → {len(creatures)}種を取得")
            
            if i < len(category_links):
                time.sleep(1)
    else:
        # 単一ページを処理
        print("単一ページを処理します")
        creatures = scrape_page_simple(main_url)
        
        for creature in creatures:
            creature['id'] = creature_id
            all_creatures.append(creature)
            creature_id += 1
    
    # 保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"creatures_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_creatures, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 保存完了: {filename}")
    print(f"取得した生き物の総数: {len(all_creatures)}種")

if __name__ == "__main__":
    main()
