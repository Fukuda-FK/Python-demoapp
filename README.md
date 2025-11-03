# FastAPI Demo System

New Relicモニタリングを統合したFastAPIベースの決済デモシステム

## 機能

- FastAPIによる高速なREST API
- PostgreSQLデータベース統合
- New Relicによる包括的な監視
  - APM (Application Performance Monitoring)
  - Distributed Tracing
  - Logs in Context
  - Browser Monitoring
- 複数のエラーシナリオのシミュレーション
- 管理者向けデバッグモード

## セットアップ

### 前提条件

- Python 3.9+
- PostgreSQL 15+
- New Relicアカウント

### ローカル開発環境

1. リポジトリをクローン
```bash
git clone https://github.com/Fukuda-FK/fastapi-demo-system.git
cd fastapi-demo-system
```

2. 依存関係をインストール
```bash
cd app
pip install -r requirements.txt
```

3. 環境変数を設定
```bash
cp config/.env.example .env
# .envファイルを編集してデータベース接続情報を設定
```

4. New Relic設定
```bash
# config/newrelic.iniを編集してライセンスキーを設定
license_key = YOUR_NEW_RELIC_LICENSE_KEY
```

5. アプリケーションを起動
```bash
newrelic-admin run-program uvicorn main:app --host 0.0.0.0 --port 3000
```

## AWS CloudFormationでのデプロイ

CloudFormationテンプレートを使用して、完全なインフラストラクチャを自動構築できます。

```bash
aws cloudformation create-stack \
  --stack-name fastapi-demo \
  --template-body file://cloudformation/fastapi-demo-infrastructure.yaml \
  --parameters \
    ParameterKey=NewRelicLicenseKey,ParameterValue=YOUR_LICENSE_KEY \
    ParameterKey=KeyPairName,ParameterValue=YOUR_KEY_PAIR \
    ParameterKey=DBPassword,ParameterValue=YOUR_DB_PASSWORD \
    ParameterKey=AllowedIPAddress,ParameterValue=YOUR_IP/32 \
  --capabilities CAPABILITY_IAM
```

### インフラストラクチャ構成

- VPC (10.0.0.0/16)
- パブリックサブネット x2
- プライベートサブネット x2
- Application Load Balancer
- EC2インスタンス (t3.small)
- RDS PostgreSQL (db.t3.micro)
- New Relic Infrastructure Agent

## API エンドポイント

### 決済API
- `POST /api/payment` - 決済処理
- `GET /api/transactions` - トランザクション一覧
- `DELETE /api/transactions/clear` - トランザクション削除

### 管理API
- `POST /admin/failure` - エラーモード切替
- `POST /admin/slow` - スローモード切替
- `POST /admin/code-error` - コードエラーモード
- `POST /admin/db-error` - DBエラーモード
- `POST /admin/resource-error` - リソースエラーモード
- `GET /admin/status` - システムステータス

### ヘルスチェック
- `GET /health` - ヘルスチェック
- `GET /api/db-test` - データベース接続テスト

## セキュリティに関する注意

**重要**: 以下のファイルには機密情報を含めないでください

- `.env` - 環境変数（.gitignoreに含まれています）
- `config/newrelic.ini` - プレースホルダーのみをコミット

本番環境では必ず以下を実施してください：
- 強力なデータベースパスワードを使用
- セキュリティグループで適切なIP制限を設定
- SSL/TLS証明書を使用
- New Relicライセンスキーを環境変数で管理

## ライセンス

MIT License
