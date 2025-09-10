# get_creature_info_from_wikipedia.py
import requests
import json
import time
from typing import Dict, Optional, List
import re
from urllib.parse import quote

class WikipediaCreatureInfoFetcher:
    def __init__(self):
        self.wikipedia_api = "https://ja.wikipedia.org/w/api.php"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MarineLifeBot/1.0 (https://example.com/bot)'
        })
    
    def get_creature_info(self, japanese_name: str) -> Optional[Dict]:
        """
        日本語の生き物名からWikipedia情報を取得
        """
        try:
            # 1. ページの内容を取得
            params = {
                'action': 'query',
                'format': 'json',
                'titles': japanese_name,
                'prop': 'extracts|langlinks',
                'exintro': True,
                'explaintext': True,
                'exsentences': 3,
                'lllimit': 500,
                'redirects': 1
            }
            
            response = self.session.get(self.wikipedia_api, params=params)
            data = response.json()
            
            if 'query' not in data or 'pages' not in data['query']:
                return None
            
            pages = data['query']['pages']
            page_id = list(pages.keys())[0]
            
            # ページが存在しない場合
            if page_id == '-1':
                return None
            
            page = pages[page_id]
            
            # 英語名を取得
            english_name = None
            if 'langlinks' in page:
                for lang in page['langlinks']:
                    if lang['lang'] == 'en':
                        english_name = lang['*']
                        # 学名の括弧を除去（英語名をクリーンに）
                        english_name = re.sub(r'\s*\([^)]*\)', '', english_name)
                        break
            
            # 英語名が見つからない場合はスキップ
            if not english_name:
                return None
            
            # 説明文を取得（最初の3文）
            description = page.get('extract', '')
            
            # 説明文をクリーンアップ（学名部分を除去）
            description = re.sub(r'（[A-Z][a-z]+ [a-z]+）', '', description)
            description = re.sub(r'\([A-Z][a-z]+ [a-z]+\)', '', description)
            description = re.sub(r'学名[:：]\s*[A-Z][a-z]+ [a-z]+', '', description)
            description = re.sub(r'\s+', ' ', description).strip()
            
            return {
                'japanese_name': japanese_name,
                'english_name': english_name,
                'description': description,
                'wikipedia_url': f"https://ja.wikipedia.org/wiki/{quote(japanese_name)}",
                'source': 'Wikipedia'
            }
            
        except Exception as e:
            print(f"  エラー ({japanese_name}): {e}")
            return None
    
    def process_creature_list(self, creatures: List[Dict]) -> List[Dict]:
        """
        生き物リストを処理してWikipedia情報を追加
        """
        enriched_creatures = []
        found_count = 0
        not_found_names = []
        
        print(f"Wikipedia情報を取得中... (全{len(creatures)}件)")
        print("="*60)
        
        for i, creature in enumerate(creatures, 1):
            name = creature.get('name', '')
            if not name:
                continue
            
            print(f"[{i}/{len(creatures)}] 検索中: {name}")
            
            # Wikipedia情報を取得
            wiki_info = self.get_creature_info(name)
            
            if wiki_info and wiki_info.get('english_name'):
                # 情報が見つかった場合
                enriched_creature = {
                    **creature,
                    'english_name': wiki_info['english_name'],
                    'description': wiki_info['description'][:200] + '...' if len(wiki_info['description']) > 200 else wiki_info['description']
                }
                enriched_creatures.append(enriched_creature)
                found_count += 1
                print(f"  ✓ 英語名: {wiki_info['english_name']}")
            else:
                # 情報が見つからなかった場合（出力しない）
                not_found_names.append(name)
                print(f"  × 情報なし（スキップ）")
            
            # API制限を避けるため待機
            time.sleep(0.5)
        
        print("\n" + "="*60)
        print(f"処理完了:")
        print(f"  - 情報取得成功: {found_count}件")
        print(f"  - スキップ: {len(not_found_names)}件")
        
        if not_found_names and len(not_found_names) <= 20:
            print(f"\n情報が見つからなかった生き物:")
            for name in not_found_names[:20]:
                print(f"  - {name}")
        
        return enriched_creatures

def main():
    """
    メイン処理
    """
    import sys
    
    # 入力ファイルの指定
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        print("JSONファイルを指定してください:")
        input_file = input().strip()
        if not input_file:
            print("エラー: ファイルが指定されていません")
            sys.exit(1)
    
    # JSONファイルを読み込み
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            creatures = json.load(f)
        
        # リスト形式でない場合の対応
        if isinstance(creatures, dict):
            if 'creatures' in creatures:
                creatures = creatures['creatures']
            elif 'data' in creatures:
                creatures = creatures['data']
            else:
                print("エラー: 対応していないJSON形式です")
                sys.exit(1)
        
        print(f"読み込み完了: {len(creatures)}件のデータ")
        
    except Exception as e:
        print(f"ファイル読み込みエラー: {e}")
        sys.exit(1)
    
    # Wikipedia情報取得
    fetcher = WikipediaCreatureInfoFetcher()
    enriched_creatures = fetcher.process_creature_list(creatures)
    
    # 結果を保存
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"creatures_with_english_{timestamp}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(enriched_creatures, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 保存完了: {output_file}")
    print(f"保存された生き物数: {len(enriched_creatures)}件")
    
    # サンプル表示
    if enriched_creatures:
        print("\nサンプル (最初の3件):")
        for creature in enriched_creatures[:3]:
            print(f"\n【{creature['name']}】")
            print(f"  英語名: {creature.get('english_name', 'N/A')}")
            print(f"  説明: {creature.get('description', 'N/A')[:100]}...")

# 単体テスト用の関数
def test_single_creature():
    """
    単一の生き物でテスト
    """
    fetcher = WikipediaCreatureInfoFetcher()
    
    test_names = [
        "ウミテング",
        "カクレクマノミ",
        "ジンベエザメ",
        "ウツボ",
        "マンボウ",
        "チンアナゴ"
    ]
    
    print("テスト実行:")
    print("="*60)
    
    for name in test_names:
        print(f"\n検索: {name}")
        info = fetcher.get_creature_info(name)
        
        if info:
            print(f"  ✓ 英語名: {info.get('english_name', 'N/A')}")
            print(f"  ✓ 説明: {info.get('description', 'N/A')[:100]}...")
        else:
            print(f"  × 情報が見つかりませんでした")
        
        time.sleep(0.5)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        # テストモード
        test_single_creature()
    else:
        # 通常モード
        main()
