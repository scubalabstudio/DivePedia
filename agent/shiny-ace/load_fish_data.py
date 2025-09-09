# load_fish_data.py
import json
import csv

def load_json(filename):
    """JSON形式のデータを読み込む"""
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_jsonl(filename):
    """JSONL形式のデータを読み込む"""
    data = []
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))
    return data

def load_urls(filename):
    """URLリストを読み込む"""
    with open(filename, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def load_minimal(filename):
    """軽量JSONを読み込んで、名前とURLのペアを返す"""
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return [(item['name'], item['url']) for item in data['items']]

# 使用例
if __name__ == "__main__":
    # JSONLから読み込んで処理
    fish_list = load_jsonl("fish_data_20240101_120000.jsonl")
    
    for fish in fish_list:
        print(f"処理中: {fish['name_ja']} - {fish['detail_url']}")
        # ここで詳細データの取得処理を実行
