# scrape_izuzuki_ebikani.py
import requests
from bs4 import BeautifulSoup
import json
import sys
import time
from datetime import datetime
from urllib.parse import urljoin

def get_category_links(main_url: str) -> list:
    """
    エビカニ他のメインページからカテゴリーリンクを取得
    """
    try:
        print(f"カテゴリーリンクを取得中: {main_url}")
        
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
            # "種類別"というテキストを含むp要素を探す
            p = thumlist.find('p', class_='kaMei_other')
            if p and '種類別' in p.get_text():
                print("種類別セクションを発見")
                
                # このセクション内のthumitemを取得
                for item in thumlist.find_all('div', class_='thumitem'):
                    link = item.find('a')
                    if link and link.get('href'):
                        # カテゴリー名を取得
                        name = ""
                        br = link.find('br')
                        if br and br.next_sibling:
                            if isinstance(br.next_sibling, str):
                                name = br.next_sibling.strip()
                            else:
                                name = br.next_sibling.get_text(strip=True)
                        
                        if name:
                            url = urljoin(main_url, link.get('href'))
                            category_links.append({
                                'name': name,
                                'url': url
                            })
                            print(f"  発見: {name}")
                break
        
        return category_links
        
    except Exception as e:
        print(f"エラー: {e}")
        return []

def scrape_category_page(url: str, category_name: str) -> list:
    """
    カテゴリーページから生き物データを取得
    """
    try:
        print(f"  スクレイピング中: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        creatures = []
        
        # 全てのthumlistを処理
        thumlist_divs = soup.find_all('div', class_='thumlist')
        
        if not thumlist_divs:
            # thumlistがない場合、直接thumitemを探す
            all_items = soup.find_all('div', class_='thumitem')
            for item in all_items:
                name = extract_name_from_item(item)
                if name:
                    creatures.append({
                        'name': name,
                        'family': '',
                        'category': category_name
                    })
        else:
            for thumlist in thumlist_divs:
                # 科名を取得（複数のクラス名に対応）
                family_elem = None
                for class_name in ['kaMei_fish', 'kaMei_slug', 'kaMei_other']:
                    family_elem = thumlist.find('p', class_=class_name)
                    if family_elem:
                        break
                
                family_name = family_elem.get_text(strip=True) if family_elem else ''
                
                # 50音順などのラベルは除外
                if family_name and '50音順' not in family_name and '種類別' not in family_name:
                    # この科の生き物を取得
                    for item in thumlist.find_all('div', class_='thumitem'):
                        name = extract_name_from_item(item)
                        if name:
                            creatures.append({
                                'name': name,
                                'family': family_name,
                                'category': category_name
                            })
        
        print(f"    → {len(creatures)}種を取得")
        return creatures
        
    except Exception as e:
        print(f"  エラー: {e}")
        return []

def extract_name_from_item(item):
    """
    thumitemから名前を抽出
    """
    link = item.find('a')
    if not link:
        return None
    
    # 生き物の名前を取得
    creature_name = ""
    br = link.find('br')
    if br:
        next_elem = br.next_sibling
        if next_elem:
            if isinstance(next_elem, str):
                creature_name = next_elem.strip()
            else:
                creature_name = next_elem.get_text(strip=True)
    
    # 名前が取得できない場合の代替方法
    if not creature_name:
        texts = list(link.stripped_strings)
        if texts:
            # 最後のテキストが名前の可能性が高い
            creature_name = texts[-1]
    
    return creature_name if creature_name else None

def main():
    """メイン処理"""
    
    # URLの取得
    if len(sys.argv) > 1:
        main_url = sys.argv[1]
    else:
        print("Izuzukiエビカニ他のメインページURLを入力してください:")
        print("例: https://izuzuki.com/Zukan/Other/index.html")
        main_url = input().strip()
        if not main_url:
            # デフォルトURL
            main_url = "https://izuzuki.com/Zukan/Other/index.html"
    
    # カテゴリーリンクを取得
    category_links = get_category_links(main_url)
    
    if not category_links:
        print("\nカテゴリーリンクが取得できませんでした")
        sys.exit(1)
    
    print(f"\n{len(category_links)}個のカテゴリーを発見")
    print("="*60)
    
    # 全体の結果を格納
    all_creatures = []
    creature_id = 1
    
    # 各カテゴリーをスクレイピング
    for i, category_info in enumerate(category_links, 1):
        print(f"\n[{i}/{len(category_links)}] {category_info['name']}")
        
        creatures = scrape_category_page(category_info['url'], category_info['name'])
        
        # IDを付与して全体リストに追加
        for creature in creatures:
            creature['id'] = creature_id
            all_creatures.append({
                'id': creature_id,
                'name': creature['name'],
                'family': creature['family']
            })
            creature_id += 1
        
        # サーバーに負荷をかけないよう待機
        if i < len(category_links):
            time.sleep(1)
    
    # 保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ebikani_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_creatures, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*60)
    print("✅ スクレイピング完了！")
    print("="*60)
    print(f"取得したカテゴリー数: {len(category_links)}")
    print(f"取得した生き物の総数: {len(all_creatures)}種")
    print(f"保存先: {filename}")
    
    # 最初の10件を表示
    if all_creatures:
        print("\n最初の10件:")
        for creature in all_creatures[:10]:
            family = f" ({creature['family']})" if creature['family'] else ""
            print(f"  {creature['id']:4d}. {creature['name']}{family}")
        if len(all_creatures) > 10:
            print(f"  ... 他 {len(all_creatures) - 10}件")

if __name__ == "__main__":
    main()
