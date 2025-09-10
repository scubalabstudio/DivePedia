# classify_and_merge_marine_data.py

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Set
import re
from collections import defaultdict

class MarineDataClassifier:
    def __init__(self):
        self.fish_data = []
        self.sea_slug_data = []
        self.crustacean_data = []
        
        # 分類用のキーワード
        self.fish_keywords = [
            '魚', 'サカナ', 'fish', 'Fish',
            'ハタ科', 'ベラ科', 'スズメダイ科', 'チョウチョウウオ科', 
            'フグ科', 'カワハギ科', 'ニザダイ科', 'ブダイ科',
            'アジ科', 'タイ科', 'イサキ科', 'フエダイ科'
        ]
        
        self.sea_slug_keywords = [
            'ウミウシ', 'うみうし', 'slug', 'Slug',
            'ミドリガイ', 'アメフラシ', 'ヒトエガイ', 'フシエラガイ',
            'イロウミウシ', 'ミノウミウシ', 'ドーリス', 'モウミウシ'
        ]
        
        self.crustacean_keywords = [
            'エビ', 'カニ', 'ヤドカリ', '甲殻類',
            'イセエビ', 'ガザミ', 'ワタリガニ', 'テッポウエビ',
            'モエビ', 'サラサエビ', 'オトヒメエビ', 'カクレエビ'
        ]
        
        # その他の海洋生物キーワード（エビ・カニカテゴリーに含める）
        self.other_marine_keywords = [
            'ウニ', 'ナマコ', 'ヒトデ', 'ウミシダ', 'クラゲ',
            'サンゴ', 'イソギンチャク', 'ホヤ', '海藻', '海草',
            '巻貝', '二枚貝', 'イカ', 'タコ', 'ヒドロ虫'
        ]
        
        # 統計情報
        self.stats = {
            'total_files': 0,
            'total_records': 0,
            'fish_count': 0,
            'sea_slug_count': 0,
            'crustacean_count': 0,
            'duplicates_removed': 0,
            'variations_merged': 0,  # 追加：バリエーション統合数
            'unclassified': 0
        }
        
        # バリエーションを示すパターン
        self.variation_patterns = [
            r'[（(][幼成老若]魚[）)]',  # 幼魚、成魚、老魚、若魚
            r'[（(]yg[）)]',  # yg (young)
            r'[（(]juv[）)]',  # juvenile
            r'[（(]ad[）)]',  # adult
            r'[（(][雄雌オスメス♂♀][）)]',  # 性別
            r'[（(][大中小][型]?[）)]',  # サイズ
            r'[（(]\d+[cmCM][）)]',  # サイズ（数値）
            r'[（(]婚姻色[）)]',  # 婚姻色
            r'[（(]求愛色[）)]',  # 求愛色
            r'[（(]夏色[）)]',  # 季節変化
            r'[（(]冬色[）)]',
            r'[（(]夜[）)]',  # 時間帯
            r'[（(]昼[）)]',
            r'[（(]産卵期[）)]',  # 産卵期
            r'[（(]非産卵期[）)]',
            r'[（(]変異[）)]',  # 変異
            r'[（(]型[）)]',  # ～型
            r'[（(]タイプ[）)]',  # タイプ
            r'[（(]バリエーション[）)]',
            r'[（(]個体差[）)]',
            r'[（(]地域変異[）)]',
            r'[（(]色彩変異[）)]',
            r'[（(]模様違い[）)]',
            r'[（(]別名[）)]',
            r'[（(]旧称[）)]',
            r'[（(]新称[）)]',
        ]

    def normalize_name(self, name: str) -> str:
        """
        名前を正規化（重複判定用）
        幼魚・成魚などのバリエーションを除去
        """
        if not name:
            return ""
        
        # 基本的な正規化
        normalized = name.strip()
        
        # カタカナの表記揺れを統一
        replacements = {
            'ヴ': 'ブ',
            'ヅ': 'ズ',
            'ヂ': 'ジ',
            '・': '',
            '･': '',
            '　': ' ',  # 全角スペースを半角に
        }
        
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        # バリエーションパターンを除去
        for pattern in self.variation_patterns:
            normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE)
        
        # その他の括弧内情報を除去（ただし、名前の一部である可能性があるものは残す）
        # 例：「カクレクマノミ（幼魚）」→「カクレクマノミ」
        # 　　「ニシキヤッコ（太平洋型）」→「ニシキヤッコ」
        normalized = re.sub(r'[（(][^）)]*[）)]', '', normalized)
        
        # 連続するスペースを1つに
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # 前後の空白を除去
        normalized = normalized.strip()
        
        # 小文字化して比較
        return normalized.lower()
    
    def get_base_name(self, name: str) -> str:
        """
        バリエーション情報を除いた基本名を取得
        （表示用：大文字小文字は保持）
        """
        if not name:
            return ""
        
        base_name = name.strip()
        
        # バリエーションパターンを除去
        for pattern in self.variation_patterns:
            base_name = re.sub(pattern, '', base_name, flags=re.IGNORECASE)
        
        # その他の括弧内情報を除去
        base_name = re.sub(r'[（(][^）)]*[）)]', '', base_name)
        
        # 連続するスペースを1つに
        base_name = re.sub(r'\s+', ' ', base_name)
        
        return base_name.strip()

    def classify_creature(self, creature_data: Dict) -> str:
        """
        生き物データを分類
        Returns:
            'fish', 'sea_slug', 'crustacean', or 'unknown'
        """
        # データから分類の手がかりを探す
        name = creature_data.get('name', '').lower()
        family = creature_data.get('family', '').lower()
        category = creature_data.get('category', '').lower()
        
        # ファイルパスやURLからの情報も利用
        url = creature_data.get('url', '').lower()
        detail_url = creature_data.get('detail_url', '').lower()
        
        combined_text = f"{name} {family} {category} {url} {detail_url}"
        
        # 魚類の判定
        for keyword in self.fish_keywords:
            if keyword.lower() in combined_text:
                return 'fish'
        
        # ウミウシの判定
        for keyword in self.sea_slug_keywords:
            if keyword.lower() in combined_text:
                return 'sea_slug'
        
        # エビ・カニ・その他の判定
        for keyword in self.crustacean_keywords + self.other_marine_keywords:
            if keyword.lower() in combined_text:
                return 'crustacean'
        
        # URLパターンでの判定
        if '/fish/' in combined_text or '/sakana/' in combined_text:
            return 'fish'
        elif '/slug/' in combined_text or '/umiushi/' in combined_text:
            return 'sea_slug'
        elif '/other/' in combined_text or '/ab/' in combined_text or '/ka2/' in combined_text:
            return 'crustacean'
        
        # 分類できない場合
        return 'unknown'

    def load_json_file(self, filepath: str) -> List[Dict]:
        """
        JSONファイルを読み込む
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # データ構造の判定
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                # 様々な形式に対応
                if 'creatures' in data:
                    return data['creatures']
                elif 'fish_list' in data:
                    return data['fish_list']
                elif 'items' in data:
                    return data['items']
                elif 'data' in data:
                    return data['data']
                else:
                    # 辞書の値がリストの場合
                    for value in data.values():
                        if isinstance(value, list) and len(value) > 0:
                            # 最初のリスト型の値を返す
                            if isinstance(value[0], dict):
                                return value
                    return []
            else:
                return []
        except Exception as e:
            print(f"  警告: {filepath} の読み込みに失敗: {e}")
            return []

    def process_directory(self, directory_path: str):
        """
        ディレクトリ内の全JSONファイルを処理
        """
        print(f"ディレクトリをスキャン中: {directory_path}")
        
        # JSONファイルを検索
        json_files = []
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.json'):
                    json_files.append(os.path.join(root, file))
        
        print(f"{len(json_files)}個のJSONファイルを発見")
        self.stats['total_files'] = len(json_files)
        
        # 各ファイルを処理
        for i, filepath in enumerate(json_files, 1):
            print(f"\n[{i}/{len(json_files)}] 処理中: {os.path.basename(filepath)}")
            creatures = self.load_json_file(filepath)
            
            if not creatures:
                continue
            
            print(f"  {len(creatures)}件のデータを読み込み")
            self.stats['total_records'] += len(creatures)
            
            # 各生き物を分類
            for creature in creatures:
                category = self.classify_creature(creature)
                
                if category == 'fish':
                    self.fish_data.append(creature)
                elif category == 'sea_slug':
                    self.sea_slug_data.append(creature)
                elif category == 'crustacean':
                    self.crustacean_data.append(creature)
                else:
                    # 分類できないものはエビ・カニカテゴリーに入れる
                    self.crustacean_data.append(creature)
                    self.stats['unclassified'] += 1

    def merge_variations(self, data_list: List[Dict]) -> List[Dict]:
        """
        バリエーション（幼魚・成魚など）を統合
        """
        merged_data = {}
        variations_count = 0
        
        for item in data_list:
            name = item.get('name', '')
            if not name:
                continue
            
            # 正規化された名前を取得
            normalized = self.normalize_name(name)
            base_name = self.get_base_name(name)
            
            if normalized not in merged_data:
                # 新規追加（基本名を使用）
                item_copy = item.copy()
                item_copy['name'] = base_name
                item_copy['original_names'] = [name]  # 元の名前を記録
                merged_data[normalized] = item_copy
            else:
                # 既存のデータと統合
                existing = merged_data[normalized]
                
                # 元の名前を記録
                if 'original_names' not in existing:
                    existing['original_names'] = [existing.get('name', '')]
                if name not in existing['original_names']:
                    existing['original_names'].append(name)
                
                # より情報が多い方のデータを保持
                for key, value in item.items():
                    if key not in existing or (value and not existing.get(key)):
                        existing[key] = value
                
                variations_count += 1
        
        self.stats['variations_merged'] += variations_count
        
        # リストに変換
        result = list(merged_data.values())
        
        # original_namesフィールドをクリーンアップ（オプション）
        for item in result:
            if 'original_names' in item and len(item['original_names']) > 1:
                # バリエーション情報として保存
                item['variations'] = ', '.join(item['original_names'])
            # original_namesフィールドを削除（必要に応じて）
            item.pop('original_names', None)
        
        return result

    def remove_duplicates(self, data_list: List[Dict]) -> List[Dict]:
        """
        重複を除去（バリエーション統合後）
        """
        # まずバリエーションを統合
        merged_data = self.merge_variations(data_list)
        
        # その後、完全な重複を除去
        seen_names = {}
        unique_data = []
        duplicates = 0
        
        for item in merged_data:
            name = item.get('name', '')
            if not name:
                continue
            
            normalized = self.normalize_name(name)
            
            if normalized not in seen_names:
                # 新規追加
                seen_names[normalized] = item
                unique_data.append(item)
            else:
                # 重複発見 - より情報が多い方を保持
                existing = seen_names[normalized]
                
                # 情報量を比較（None以外のフィールド数）
                existing_info = sum(1 for v in existing.values() if v)
                new_info = sum(1 for v in item.values() if v)
                
                if new_info > existing_info:
                    # 新しいデータの方が情報が多い
                    idx = unique_data.index(existing)
                    unique_data[idx] = item
                    seen_names[normalized] = item
                
                duplicates += 1
        
        self.stats['duplicates_removed'] += duplicates
        return unique_data

    def save_classified_data(self, output_dir: str = None):
        """
        分類されたデータを保存
        """
        if not output_dir:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = f"classified_data_{timestamp}"
        
        os.makedirs(output_dir, exist_ok=True)
        
        print("\n" + "="*60)
        print("バリエーションを統合し、重複を除去中...")
        
        # 重複除去とバリエーション統合
        unique_fish = self.remove_duplicates(self.fish_data)
        unique_sea_slug = self.remove_duplicates(self.sea_slug_data)
        unique_crustacean = self.remove_duplicates(self.crustacean_data)
        
        # IDを再割り当て
        for i, item in enumerate(unique_fish, 1):
            item['id'] = i
        
        for i, item in enumerate(unique_sea_slug, 1):
            item['id'] = i
        
        for i, item in enumerate(unique_crustacean, 1):
            item['id'] = i
        
        # 統計を更新
        self.stats['fish_count'] = len(unique_fish)
        self.stats['sea_slug_count'] = len(unique_sea_slug)
        self.stats['crustacean_count'] = len(unique_crustacean)
        
        print("データを保存中...")
        
        # 1. 魚類データ
        fish_file = os.path.join(output_dir, "fish_data.json")
        with open(fish_file, 'w', encoding='utf-8') as f:
            json.dump(unique_fish, f, ensure_ascii=False, indent=2)
        print(f"✓ 魚類データ保存: {fish_file} ({len(unique_fish)}種)")
        
        # 2. ウミウシデータ
        sea_slug_file = os.path.join(output_dir, "sea_slug_data.json")
        with open(sea_slug_file, 'w', encoding='utf-8') as f:
            json.dump(unique_sea_slug, f, ensure_ascii=False, indent=2)
        print(f"✓ ウミウシデータ保存: {sea_slug_file} ({len(unique_sea_slug)}種)")
        
        # 3. エビ・カニ・その他データ
        crustacean_file = os.path.join(output_dir, "crustacean_other_data.json")
        with open(crustacean_file, 'w', encoding='utf-8') as f:
            json.dump(unique_crustacean, f, ensure_ascii=False, indent=2)
        print(f"✓ エビ・カニ・その他データ保存: {crustacean_file} ({len(unique_crustacean)}種)")
        
        # 4. 統計レポート
        report_file = os.path.join(output_dir, "classification_report.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write("海洋生物データ分類レポート\n")
            f.write("="*60 + "\n\n")
            f.write(f"処理日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"処理ファイル数: {self.stats['total_files']}\n")
            f.write(f"総レコード数: {self.stats['total_records']}\n")
            f.write(f"重複除去数: {self.stats['duplicates_removed']}\n")
            f.write(f"バリエーション統合数: {self.stats['variations_merged']}\n")
            f.write(f"分類不能数: {self.stats['unclassified']}\n\n")
            f.write("分類結果:\n")
            f.write("-"*40 + "\n")
            f.write(f"魚類: {self.stats['fish_count']}種\n")
            f.write(f"ウミウシ: {self.stats['sea_slug_count']}種\n")
            f.write(f"エビ・カニ・その他: {self.stats['crustacean_count']}種\n")
            f.write(f"合計: {self.stats['fish_count'] + self.stats['sea_slug_count'] + self.stats['crustacean_count']}種\n")
        
        print(f"✓ レポート保存: {report_file}")
        
        return output_dir

def main():
    """メイン処理"""
    # データディレクトリの指定
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    else:
        print("データディレクトリを入力してください（デフォルト: ./data）:")
        data_dir = input().strip()
        if not data_dir:
            data_dir = "./data"
    
    if not os.path.exists(data_dir):
        print(f"エラー: ディレクトリが存在しません: {data_dir}")
        sys.exit(1)
    
    # 分類器の初期化
    classifier = MarineDataClassifier()
    
    # ディレクトリを処理
    classifier.process_directory(data_dir)
    
    # 結果を保存
    output_dir = classifier.save_classified_data()
    
    # サマリー表示
    print("\n" + "="*60)
    print("✅ 処理完了！")
    print("="*60)
    print(f"処理ファイル数: {classifier.stats['total_files']}")
    print(f"総レコード数: {classifier.stats['total_records']}")
    print(f"重複除去数: {classifier.stats['duplicates_removed']}")
    print(f"バリエーション統合数: {classifier.stats['variations_merged']}")
    print("\n分類結果:")
    print(f"  魚類: {classifier.stats['fish_count']}種")
    print(f"  ウミウシ: {classifier.stats['sea_slug_count']}種")
    print(f"  エビ・カニ・その他: {classifier.stats['crustacean_count']}種")
    print(f"\n出力ディレクトリ: {output_dir}")

if __name__ == "__main__":
    main()
