import os
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))
from config.supabase import get_client

class MigrationRunner:
    def __init__(self):
        self.supabase = get_client()
        self.migrations_dir = Path(__file__).parent
        
    def create_migration_table(self):
        """マイグレーション履歴テーブルを作成"""
        sql = """
        CREATE TABLE IF NOT EXISTS migration_history (
            id SERIAL PRIMARY KEY,
            filename VARCHAR(255) UNIQUE NOT NULL,
            executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """
        # Supabase SQL Editorで実行
        print("migration_historyテーブルを作成してください")
        print(sql)
    
    def get_executed_migrations(self):
        """実行済みマイグレーションを取得"""
        result = self.supabase.table('migration_history').select('filename').execute()
        return [m['filename'] for m in result.data]
    
    def run_migrations(self):
        """未実行のマイグレーションを実行"""
        executed = self.get_executed_migrations()
        
        # SQLファイルを取得（番号順）
        sql_files = sorted([f for f in os.listdir(self.migrations_dir) 
                          if f.endswith('.sql') and not f.startswith('rollback')])
        
        for sql_file in sql_files:
            if sql_file not in executed:
                print(f"実行中: {sql_file}")
                
                # SQLファイルを読み込み
                with open(self.migrations_dir / sql_file, 'r') as f:
                    sql = f.read()
                
                print(f"以下のSQLをSupabase SQL Editorで実行してください:")
                print("-" * 50)
                print(sql)
                print("-" * 50)
                
                # 実行履歴に記録
                self.supabase.table('migration_history').insert({
                    'filename': sql_file
                }).execute()
                
                print(f"✅ {sql_file} を実行済みとして記録")

if __name__ == "__main__":
    runner = MigrationRunner()
    runner.create_migration_table()
    runner.run_migrations()
