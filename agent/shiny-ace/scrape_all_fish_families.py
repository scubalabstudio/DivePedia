import requests
from bs4 import BeautifulSoup
import json
import sys
import time
from datetime import datetime
from urllib.parse import urljoin
import os
import subprocess

def get_family_links(main_url: str) -> list:
    """
    メインページから各科のリンクを取得
    
    Args:
        main_url: 図鑑のメインページURL
        
    Returns:
        科のリンクリスト
    """
    try:
        print(f"メインページから科のリンクを取得中: {main_url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(main_url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        family_links = []
        
        # class="list"のセクションから科のリンクを取得
        for section in soup.find_all('section', class_='list'):
            link = section.find('a')
            if link and link.get('href'):
                # 科の名前を取得
                family_name = ""
                br = link.find('br')
                if br and br.next_sibling:
                    text = br.next_sibling
                    if isinstance(text, str):
                        family_name = text.strip()
                    else:
                        family_name = text.get_text(strip=True)
                
                # 絶対URLに変換
                absolute_url = urljoin(main_url, link.get('href'))
                
                family_links.append({
                    'name': family_name,
                    'url': absolute_url
                })
                print(f"  発見: {family_name} - {absolute_url}")
        
        print(f"\n合計 {len(family_links)} 科のリンクを取得しました")
        return family_links
        
    except Exception as e:
        print(f"エラー: {e}")
        return []

def scrape_fish_simple(url: str) -> list:
    """
    各科のページから魚のデータを取得（extract_fish_simple.pyの関数）
    
    Args:
        url: スクレイピング対象のURL
        
    Returns:
        IDと名前のリスト
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        fish_list = []
        
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
                    fish_list.append(fish_name)
        
        return fish_list
        
    except Exception as e:
        print(f"エラー: {e}")
        return []

def main():
    """メイン処理"""
    # メインページのURL取得
    if len(sys.argv) > 1:
        main_url = sys.argv[1]
    else:
        print("図鑑のメインページURLを入力してください:")
        print("例: http://shiny-ace.com/zukan.html")
        main_url = input().strip()
        if not main_url:
            print("エラー: URLが指定されていません")
            sys.exit(1)
    
    # 出力ディレクトリの作成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"fish_data_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    print(f"\n出力ディレクトリ: {output_dir}")
    
    # 科のリンクを取得
    family_links = get_family_links(main_url)
    
    if not family_links:
        print("科のリンクが取得できませんでした")
        sys.exit(1)
    
    # 全体の結果を格納
    all_results = {
        'source_url': main_url,
        'scraped_at': datetime.now().isoformat(),
        'total_families': len(family_links),
        'families': []
    }
    
    # 各科のページをスクレイピング
    print("\n" + "="*60)
    print("各科のページをスクレイピング開始")
    print("="*60)
    
    total_fish_count = 0
    fish_id_counter = 1
    
    for i, family_info in enumerate(family_links, 1):
        print(f"\n[{i}/{len(family_links)}] {family_info['name']}")
        print(f"  URL: {family_info['url']}")
        
        # 魚のリストを取得
        fish_names = scrape_fish_simple(family_info['url'])
        
        if fish_names:
            print(f"  → {len(fish_names)}種の魚を取得")
            
            # IDを付与してデータを構造化
            fish_with_ids = []
            for name in fish_names:
                fish_with_ids.append({
                    'id': fish_id_counter,
                    'name': name,
                    'family': family_info['name']
                })
                fish_id_counter += 1
            
            # 科ごとのデータを保存
            family_data = {
                'family_name': family_info['name'],
                'url': family_info['url'],
                'fish_count': len(fish_names),
                'fish_list': fish_with_ids
            }
            
            all_results['families'].append(family_data)
            
            # 科ごとの個別ファイルも保存
            family_filename = family_info['name'].replace('/', '_').replace(' ', '_')
            family_file = os.path.join(output_dir, f"{family_filename}.json")
            with open(family_file, 'w', encoding='utf-8') as f:
                json.dump(fish_with_ids, f, ensure_ascii=False, indent=2)
            
            total_fish_count += len(fish_names)
        else:
            print(f"  → データ取得失敗またはデータなし")
        
        # サーバーに負荷をかけないよう待機
        if i < len(family_links):
            time.sleep(1)
    
    # 全体の統計情報を追加
    all_results['total_fish_count'] = total_fish_count
    
    # 全体のデータを保存
    print("\n" + "="*60)
    print("結果を保存中...")
    print("="*60)
    
    # 1. 完全なデータ（全科統合）
    all_data_file = os.path.join(output_dir, "all_fish_data.json")
    with open(all_data_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"✓ 全データ保存: {all_data_file}")
    
    # 2. シンプルなリスト（ID + 名前 + 科）
    simple_list = []
    for family in all_results['families']:
        simple_list.extend(family['fish_list'])
    
    simple_file = os.path.join(output_dir, "fish_simple_all.json")
    with open(simple_file, 'w', encoding='utf-8') as f:
        json.dump(simple_list, f, ensure_ascii=False, indent=2)
    print(f"✓ シンプルリスト保存: {simple_file}")
    
    # 3. 名前のみのテキストファイル
    names_file = os.path.join(output_dir, "all_fish_names.txt")
    with open(names_file, 'w', encoding='utf-8') as f:
        for fish in simple_list:
            f.write(f"{fish['name']}\n")
    print(f"✓ 名前リスト保存: {names_file}")
    
    # 4. サマリーレポート
    report_file = os.path.join(output_dir, "scraping_report.txt")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write("魚図鑑スクレイピングレポート\n")
        f.write("="*60 + "\n\n")
        f.write(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"ソースURL: {main_url}\n")
        f.write(f"取得した科の数: {len(family_links)}\n")
        f.write(f"取得した魚の総数: {total_fish_count}\n\n")
        
        f.write("科ごとの内訳:\n")
        f.write("-"*40 + "\n")
        for family in all_results['families']:
            f.write(f"{family['family_name']}: {family['fish_count']}種\n")
    
    print(f"✓ レポート保存: {report_file}")
    
    # 完了メッセージ
    print("\n" + "="*60)
    print("✅ スクレイピング完了！")
    print("="*60)
    print(f"取得した科の数: {len(family_links)}")
    print(f"取得した魚の総数: {total_fish_count}")
    print(f"出力ディレクトリ: {output_dir}")

if __name__ == "__main__":
    main()
