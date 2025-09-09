# extract_fish_simple.py
import requests
from bs4 import BeautifulSoup
import json
import sys
from datetime import datetime
from urllib.parse import urljoin

def scrape_fish_simple(url: str) -> list:
    """
    URLから魚のIDと名前のみを取得
    
    Args:
        url: スクレイピング対象のURL
        
    Returns:
        IDと名前のリスト
    """
    try:
        print(f"スクレイピング開始: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 魚のデータを収集
        fish_list = []
        id_counter = 1
        
        # class="list"のセクションを全て取得
        for element in soup.find_all('section', class_='list'):
            link = element.find('a')
            if link:
                # 魚の名前を取得
                fish_name = ""
                
                small_tag = link.find('small')
                if small_tag:
                    fish_name = small_tag.get_text(strip=True)
                else:
                    br = link.find('br')
                    if br and br.next_sibling:
                        text = br.next_sibling
                        if isinstance(text, str):
                            fish_name = text.strip()
                        else:
                            fish_name = text.get_text(strip=True)
                
                if fish_name:
                    fish_list.append({
                        'id': id_counter,
                        'name': fish_name
                    })
                    id_counter += 1
        
        print(f"取得完了: {len(fish_list)}種の魚を取得しました")
        return fish_list
        
    except Exception as e:
        print(f"エラー: {e}")
        return []

def main():
    """メイン処理"""
    # URL取得
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        print("スクレイピングするURLを入力してください:")
        url = input().strip()
        if not url:
            print("エラー: URLが指定されていません")
            sys.exit(1)
    
    # データ取得
    fish_list = scrape_fish_simple(url)
    
    if not fish_list:
        print("データの取得に失敗しました")
        sys.exit(1)
    
    # ファイル名の決定
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"fish_simple_{timestamp}.json"
    
    # JSON形式で保存
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(fish_list, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 保存完了: {filename}")
    print(f"取得した魚の数: {len(fish_list)}種")
    
    # 最初の5件を表示
    print("\n最初の5件:")
    for fish in fish_list[:5]:
        print(f"  {fish['id']:3d}. {fish['name']}")
    if len(fish_list) > 5:
        print(f"  ... 他 {len(fish_list) - 5}件")

if __name__ == "__main__":
    main()
