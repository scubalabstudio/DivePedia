# config/supabase.py
import os
from supabase import create_client
from dotenv import load_dotenv

# .envファイルから環境変数を読み込み
load_dotenv()

# Supabaseの接続情報
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://ihyksziopqzyalrznfqr.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImloeWtzemlvcHF6eWFscnpuZnFyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc2Mjg5NzEsImV4cCI6MjA3MzIwNDk3MX0.1BA11pUFp4l1PzicgcUpzItvv47A9kQuD-2He91Hs2s')

def get_client():
    """Supabaseクライアントを取得"""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# 必要に応じて、よく使う操作を関数化
def test_connection():
    """接続テスト"""
    try:
        client = get_client()
        # creaturesテーブルから1件取得してテスト
        result = client.table('creatures').select('*').limit(1).execute()
        print("✅ Supabase接続成功")
        return True
    except Exception as e:
        print(f"❌ Supabase接続失敗: {e}")
        return False
