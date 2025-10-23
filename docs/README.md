# FastAPI デモシステム

決済処理のデモアプリケーション（FastAPI版）

## セットアップ

1. 依存パッケージのインストール:
```bash
pip install -r requirements.txt
```

2. 環境変数の設定:
```bash
copy .env.example .env
```

3. PostgreSQLデータベースの準備（必要に応じて）

## 起動方法

```bash
uvicorn main:app --reload --port 3000
```

ブラウザで http://localhost:3000 にアクセス

## 機能

- 商品一覧表示とカート機能
- 決済処理API
- 障害シミュレーション（エラーモード、遅延モード）
- データベース接続テスト
- 管理画面

## エンドポイント

- `GET /` - フロントエンド
- `POST /api/payment` - 決済処理
- `GET /api/transactions` - 取引履歴
- `GET /api/db-test` - DB接続テスト
- `POST /admin/failure` - エラーモード切替
- `POST /admin/slow` - 遅延モード切替
- `GET /admin/status` - システム状態確認
