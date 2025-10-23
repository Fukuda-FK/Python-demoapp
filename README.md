# FastAPI ECサイト デモシステム

New Relic APM統合を含むFastAPIベースのECサイトデモアプリケーション

## ディレクトリ構造

```
fastapi-demo-system/
├── app/                    # アプリケーションコード
│   ├── main.py            # FastAPIアプリケーション本体
│   ├── static/            # 静的ファイル（HTML/CSS/JS）
│   ├── requirements.txt   # Python依存パッケージ
│   └── test_rds.py        # RDS接続テスト
├── config/                 # 設定ファイル
│   ├── newrelic.ini       # New Relic APM設定
│   └── .env.example       # 環境変数テンプレート
├── deployment/             # デプロイメント設定
│   ├── fastapi-demo.service      # systemdサービス設定
│   └── fastapi-demo-logs.yml     # New Relic Logs設定
└── docs/                   # ドキュメント
    ├── NEW_RELIC_SETUP_GUIDE.md  # New Relic完全セットアップガイド
    ├── DEMO_SCENARIOS.md          # デモシナリオ説明
    └── その他ドキュメント
```

## クイックスタート

### 1. 依存パッケージのインストール

```bash
cd app
pip3 install -r requirements.txt
```

### 2. 環境変数の設定

```bash
cp config/.env.example .env
# .envファイルを編集してデータベース接続情報を設定
```

### 3. New Relic設定

```bash
# config/newrelic.iniを編集
# - license_key: New RelicライセンスキーをNew Relic UIから取得
# - app_name: アプリケーション名を設定
```

### 4. アプリケーション起動

```bash
# 開発環境
cd app
NEW_RELIC_CONFIG_FILE=../config/newrelic.ini newrelic-admin run-program python -m uvicorn main:app --host 0.0.0.0 --port 3000

# 本番環境（systemd）
sudo cp deployment/fastapi-demo.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start fastapi-demo
sudo systemctl enable fastapi-demo
```

## 機能

- 決済処理デモ
- New Relic APM統合
- エラーシナリオデモ（コードエラー、DBエラー、リソースエラー等）
- カスタム属性による詳細な監視
- Logs in Context（ログとトレースの自動紐付け）

## ドキュメント

詳細なセットアップ手順は [docs/NEW_RELIC_SETUP_GUIDE.md](docs/NEW_RELIC_SETUP_GUIDE.md) を参照してください。

## ライセンス

MIT License
