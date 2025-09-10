# simple_wikipedia_fetcher.py
import requests
import json
import time
import re

def get_english_name_from_wikipedia(japanese_name):
    """日本語名から英語名と説明を取得"""
    api_url = "https://ja.wikipedia.org/w/api.php"
    
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
    
    try:
        response = requests.get(api_url, params=params)
        data = response.json()
        
        pages = data['query']['pages']
        page_id = list(pages.keys())[0]
        
        if page_id == '-1':
            return None
        
        page = pages[page_id]
        
        # 英語名を取得
        english_name = None
        if 'langlinks' in page:
            for lang in page['langlinks']:
                if lang['lang'] == 'en':
                    english_name = lang['*']
                    english_name = re.sub(r'\s*\([^)]*\)', '', english_name)
                    break
        
        if not english_name:
            return None
        
        # 説明文を取得
        description = page.get('extract', '')
        # 学名を除去
        description = re.sub(r'[（(][A-Z][a-z]+ [a-z]+[）)]', '', description)
        description = re.sub(r'\s+', ' ', description).strip()
        
        return {
            'english_name': english_name,
            'description': description[:200] + '...' if len(description) > 200 else description
        }
    
    except:
        return None

# メイン処理
def process_file(input_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        creatures = json.load(f)
    
    results = []
    
    for creature in creatures:
        name = creature.get('name', '')
        print(f"検索中: {name}")
        
        info = get_english_name_from_wikipedia(name)
        
        if info:
            creature['english_name'] = info['english_name']
            creature['description'] = info['description']
            results.append(creature)
            print(f"  ✓ {info['english_name']}")
        else:
            print(f"  × スキップ")
        
        time.sleep(0.5)
    
    # 保存
    with open('output_with_english.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n完了: {len(results)}件を保存")

if __name__ == "__main__":
    import sys
    process_file(sys.argv[1] if len(sys.argv) > 1 else 'input.json')
