# scrape_izuzuki_simple.py
import requests
from bs4 import BeautifulSoup
import json
import sys
from datetime import datetime
from urllib.parse import urljoin

def scrape_izuzuki_page(url: str) -> list:
    """
    IzuzukiページからID、名前、科名のみを取得
    
    Args:
        url: スクレイピング対象のURL
        
    Returns:
        シンプルな生き物データのリスト
    """
    try:
        print(f"スクレイピング中: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        creatures = []
        creature_id = 1
        
        # 全てのthumlistを処理
        thumlist_divs = soup.find_all('div', class_='thumlist')
        
        if not thumlist_divs:
            # thumlistがない場合、直接thumitemを探す
            all_items = soup.find_all('div', class_='thumitem')
            for item in all_items:
                name = extract_name_from_item(item)
                if name:
                    creatures.append({
                        'id': creature_id,
                        'name': name,
                        'family': ''  # 科名なし
                    })
                    creature_id += 1
        else:
            for thumlist in thumlist_divs:
                # 科名を取得
                family_elem = thumlist.find('p', class_='kaMei_fish')
                if not family_elem:
                    family_elem = thumlist.find('p', class_='kaMei_slug')
                family_name = family_elem.get_text(strip=True) if family_elem else ''
                
                # この科の生き物を取得
                for item in thumlist.find_all('div', class_='thumitem'):
                    name = extract_name_from_item(item)
                    if name:
                        creatures.append({
                            'id': creature_id,
                            'name': name,
                            'family': family_name
                        })
                        creature_id += 1
        
        print(f"取得完了: {len(creatures)}種")
        return creatures
        
    except Exception as e:
        print(f"エラー: {e}")
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
            creature_name = texts[-1]
    
    return creature_name if creature_name else None

def main():
    """メイン処理"""
    
    # URLの取得
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        print("URLを入力してください:")
        url = input().strip()
        if not url:
            print("エラー: URLが指定されていません")
            sys.exit(1)
    
    # データ取得
    creatures = scrape_izuzuki_page(url)
    
    if not creatures:
        print("データの取得に失敗しました")
        sys.exit(1)
    
    # ファイル名の生成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"creatures_simple_{timestamp}.json"
    
    # JSON形式で保存
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(creatures, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 保存完了: {filename}")
    print(f"取得した生き物の数: {len(creatures)}種")
    
    # 最初の5件を表示
    print("\n最初の5件:")
    for creature in creatures[:5]:
        print(f"  {creature}")

if __name__ == "__main__":
    main()
