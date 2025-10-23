# RDS接続情報

## RDSインスタンス詳細

- **インスタンス識別子**: fastapi-demo-db
- **エンドポイント**: fastapi-demo-db.cm711nipgl4d.ap-northeast-1.rds.amazonaws.com
- **ポート**: 5432
- **エンジン**: PostgreSQL 15.8
- **インスタンスクラス**: db.t3.micro
- **ストレージ**: 20GB
- **データベース名**: payment_demo
- **ユーザー名**: dbadmin
- **パスワード**: DemoPassword123!

## セキュリティグループ

- **RDS SG**: sg-0d416a32845915f34
- **EC2 SG**: sg-02900c8401da071af (アクセス許可済み)

## 接続テスト

### ローカルテスト
```bash
python test_rds.py
```

### APIテスト
```bash
# DB接続確認
curl http://43.207.1.222:3000/api/db-test

# 決済テスト
curl -X POST http://43.207.1.222:3000/api/payment \
  -H "Content-Type: application/json" \
  -d '{"amount": 5000, "cardNumber": "1234567890123456", "storeId": "STORE001"}'

# トランザクション履歴
curl http://43.207.1.222:3000/api/transactions
```

## RDS管理コマンド

```bash
# RDS状態確認
aws rds describe-db-instances --db-instance-identifier fastapi-demo-db

# RDS停止
aws rds stop-db-instance --db-instance-identifier fastapi-demo-db

# RDS起動
aws rds start-db-instance --db-instance-identifier fastapi-demo-db

# RDS削除
aws rds delete-db-instance --db-instance-identifier fastapi-demo-db --skip-final-snapshot
```

## 接続確認済み

✅ RDS作成完了
✅ セキュリティグループ設定完了
✅ アプリケーション接続完了
✅ テーブル作成完了
✅ データ保存・取得動作確認済み
