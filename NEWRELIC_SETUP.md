# New Relic APM セットアップ完了

## インストール済み

✅ New Relic Python Agent (v11.0.1)
✅ 設定ファイル (newrelic.ini)
✅ systemdサービス統合

## 設定情報

- **アプリケーション名**: FastAPI-ECSite
- **ライセンスキー**: b9192835de12b671c6eac833583ab5eeFFFFNRAL
- **設定ファイル**: /home/ec2-user/fastapi-demo-system/newrelic.ini

## 有効化された機能

- ✅ トランザクショントレーシング
- ✅ SQLクエリ記録（難読化）
- ✅ エラーコレクション
- ✅ ブラウザモニタリング
- ✅ スレッドプロファイラー
- ✅ 分散トレーシング

## 起動コマンド

systemdサービスで自動起動:
```bash
NEW_RELIC_CONFIG_FILE=newrelic.ini newrelic-admin run-program python3 -m uvicorn main:app --host 0.0.0.0 --port 3000
```

## 確認方法

1. New Relic UIにログイン
2. APM & Services → FastAPI-ECSite を確認
3. トランザクション、エラー、データベースクエリが表示される

## テストトランザクション

```bash
# ヘルスチェック
curl http://43.207.1.222:3000/health

# 決済テスト
curl -X POST http://43.207.1.222:3000/api/payment \
  -H "Content-Type: application/json" \
  -d '{"amount": 10000, "cardNumber": "1234567890123456", "storeId": "STORE001"}'

# DB接続テスト
curl http://43.207.1.222:3000/api/db-test
```

## ログ確認

```bash
sudo journalctl -u fastapi-demo -f
```

## 注意事項

- データがNew Relic UIに表示されるまで数分かかる場合があります
- トランザクションを実行してデータを生成してください
