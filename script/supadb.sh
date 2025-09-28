#!/bin/bash

# .envファイルを読み込み
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# 色付き出力
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 使い方を表示
usage() {
    echo "使い方:"
    echo "  ./scripts/supadb.sh              # 対話モード"
    echo "  ./scripts/supadb.sh query 'SQL'  # SQLクエリ実行"
    echo "  ./scripts/supadb.sh tables       # テーブル一覧"
    echo "  ./scripts/supadb.sh count TABLE  # 件数確認"
    echo "  ./scripts/supadb.sh quick        # よく使うクエリ"
}

# メイン処理
case "$1" in
    "")
        # 対話モード
        echo -e "${GREEN}✅ Supabaseに接続中...${NC}"
        psql "$DATABASE_URL"
        ;;
    
    "query")
        # クエリ実行
        psql "$DATABASE_URL" -c "$2"
        ;;
    
    "tables")
        # テーブル一覧
        psql "$DATABASE_URL" -c "\dt public.*"
        ;;
    
    "count")
        # 件数確認
        if [ -z "$2" ]; then
            echo -e "${RED}テーブル名を指定してください${NC}"
            exit 1
        fi
        psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM $2;"
        ;;
    
    "quick")
        # よく使うクエリメニュー
        echo "よく使うクエリ:"
        echo "1) creaturesの件数"
        echo "2) カテゴリ別集計"
        echo "3) 最新10件"
        echo "4) テーブル一覧"
        read -p "選択 (1-4): " choice
        
        case $choice in
            1)
                psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM creatures;"
                ;;
            2)
                psql "$DATABASE_URL" -c "SELECT category, COUNT(*) FROM creatures GROUP BY category ORDER BY COUNT(*) DESC;"
                ;;
            3)
                psql "$DATABASE_URL" -c "SELECT * FROM creatures ORDER BY created_at DESC LIMIT 10;"
                ;;
            4)
                psql "$DATABASE_URL" -c "\dt public.*"
                ;;
            *)
                echo "無効な選択"
                ;;
        esac
        ;;
    
    "help")
        usage
        ;;
    
    *)
        # 直接SQLとして実行
        psql "$DATABASE_URL" -c "$*"
        ;;
esac
