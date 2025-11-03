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
- Docker (ECSデプロイの場合)

### ローカル開発環境

1. リポジトリをクローン
```bash
git clone https://github.com/Fukuda-FK/Python-demoapp.git
cd Python-demoapp
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

## AWS ECS Fargateでのデプロイ

### CloudFormationでインフラ構築

```bash
aws cloudformation create-stack \
  --stack-name nrdemo-fastapi-ecs \
  --template-body file://cloudformation/fastapi-demo-ecs-infrastructure.yaml \
  --parameters \
    ParameterKey=NewRelicLicenseKey,ParameterValue=YOUR_LICENSE_KEY \
    ParameterKey=DBPassword,ParameterValue=YOUR_DB_PASSWORD \
    ParameterKey=AllowedIPAddress,ParameterValue=YOUR_IP/32 \
  --capabilities CAPABILITY_NAMED_IAM
```

### インフラストラクチャ構成

- VPC (10.0.0.0/16)
- パブリックサブネット x2 (ALB配置)
- プライベートサブネット x2 (ECS/RDS配置)
- NAT Gateway x2 (各AZ)
- Application Load Balancer (パブリック)
- ECS Fargate (プライベート)
- RDS PostgreSQL (db.t3.micro)
- ECR Repository
- Secrets Manager (認証情報管理)

### GitHub Actionsでの自動デプロイ

1. **GitHub環境設定 (pythondemo)**

Environment Secrets:
- `AWS_OIDC_ROLE_ARN`: AWS OIDC Role ARN

Environment Variables:
- `AWS_REGION`: ap-northeast-1
- `ECR_REPOSITORY`: nrdemo-fastapi-demo-app
- `ECS_CLUSTER`: nrdemo-fastapi-demo-cluster
- `ECS_SERVICE`: nrdemo-fastapi-demo-service

2. **デプロイ**

masterブランチへのプッシュで自動デプロイ:
```bash
git push origin master
```

手動デプロイ:
- GitHub ActionsのUIから「Deploy FastAPI Application」ワークフローを実行

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

## Docker

### ローカルでビルド・実行

```bash
cd app
docker build -t fastapi-demo .
docker run -p 3000:3000 --env-file .env fastapi-demo
```

### ECRへプッシュ

```bash
# ECRにログイン
aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.ap-northeast-1.amazonaws.com

# イメージをビルド
docker build -t nrdemo-fastapi-demo-app ./app

# タグ付け
docker tag nrdemo-fastapi-demo-app:latest <account-id>.dkr.ecr.ap-northeast-1.amazonaws.com/nrdemo-fastapi-demo-app:latest

# プッシュ
docker push <account-id>.dkr.ecr.ap-northeast-1.amazonaws.com/nrdemo-fastapi-demo-app:latest
```

## セキュリティに関する注意

**重要**: 以下のファイルには機密情報を含めないでください

- `.env` - 環境変数（.gitignoreに含まれています）
- `config/newrelic.ini` - プレースホルダーのみをコミット

本番環境では必ず以下を実施してください：
- 強力なデータベースパスワードを使用
- セキュリティグループで適切なIP制限を設定
- SSL/TLS証明書を使用
- New Relicライセンスキーを環境変数で管理
- AWS Secrets Managerで認証情報を管理

## ライセンス

MIT License
