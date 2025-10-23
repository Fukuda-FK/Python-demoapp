import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def test_rds_connection():
    print("🔍 RDS接続テスト開始...")
    
    try:
        conn = await asyncpg.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        
        print("✅ RDS接続成功")
        
        # バージョン確認
        version = await conn.fetchval("SELECT version()")
        print(f"📊 PostgreSQL Version: {version}")
        
        # テーブル作成
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                transaction_id VARCHAR(50) UNIQUE NOT NULL,
                amount DECIMAL(10, 2) NOT NULL,
                card_number VARCHAR(20),
                store_id VARCHAR(20),
                status VARCHAR(20),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        print("✅ テーブル作成完了")
        
        # テストデータ挿入
        await conn.execute(
            "INSERT INTO transactions (transaction_id, amount, card_number, store_id, status) VALUES ($1, $2, $3, $4, $5)",
            "TEST001", 1000.00, "****1234", "STORE001", "completed"
        )
        print("✅ テストデータ挿入完了")
        
        # データ確認
        count = await conn.fetchval("SELECT COUNT(*) FROM transactions")
        print(f"📈 総トランザクション数: {count}")
        
        # 最新データ取得
        row = await conn.fetchrow("SELECT * FROM transactions ORDER BY created_at DESC LIMIT 1")
        print(f"📝 最新トランザクション: {dict(row)}")
        
        await conn.close()
        print("✅ RDSテスト完了")
        
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    asyncio.run(test_rds_connection())
