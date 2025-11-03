# FastAPI Demo System with New Relic

New Relicモニタリングを統合したFastAPIベースの決済デモシステム

## 機能

- FastAPIによる高速なREST API
- PostgreSQL RDSデータベース統合
- New Relicによる包括的な監視
  - APM (Application Performance Monitoring)
  - Infrastructure Monitoring (ECSサイドカー)
  - Distributed Tracing
  - Logs in Context
- 複数のエラーシナリオのシミュレーション
- 管理者向けデバッグモード

## アーキテクチャ

- **コンピュート**: AWS ECS Fargate (パブリックサブネット)
- **データベース**: Amazon RDS PostgreSQL 15.10 (プライベートサブネット)
- **コンテナレジストリ**: Amazon ECR
- **ログ**: CloudWatch Logs
- **監視**: New Relic APM + Infrastructure Agent (サイドカー)
- **CI/CD**: GitHub Actions

## 前提条件

- AWS アカウント
- New Relic アカウント
- GitHub アカウント
- Docker (ローカル開発の場合)
- Python 3.11+ (ローカル開発の場合)

## AWS ECS Fargateでのデプロイ

### 1. CloudFormationでインフラ構築

```bash
aws cloudformation create-stack \
  --stack-name nrdemo-fastapi-ecs \
  --template-body file://cloudformation/fastapi-demo-ecs-infrastructure.yaml \
  --parameters \
    ParameterKey=NewRelicLicenseKey,ParameterValue=YOUR_LICENSE_KEY \
    ParameterKey=DBPassword,ParameterValue=YOUR_SECURE_PASSWORD \
    ParameterKey=AllowedIPAddress,ParameterValue=YOUR_IP/32 \
  --capabilities CAPABILITY_NAMED_IAM
```

### 2. 初回イメージのビルドとプッシュ

```bash
# ECRにログイン
aws ecr get-login-password --region ap-northeast-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.ap-northeast-1.amazonaws.com

# イメージをビルド
docker build -t nrdemo-fastapi-demo-app ./app

# タグ付け
docker tag nrdemo-fastapi-demo-app:latest \
  <account-id>.dkr.ecr.ap-northeast-1.amazonaws.com/nrdemo-fastapi-demo-app:latest

# プッシュ
docker push <account-id>.dkr.ecr.ap-northeast-1.amazonaws.com/nrdemo-fastapi-demo-app:latest
```

### 3. ECSサービスの起動

CloudFormationスタック作成後、ECSサービスのDesiredCountを1に更新してタスクを起動します。

```bash
aws ecs update-service \
  --cluster nrdemo-fastapi-demo-cluster \
  --service nrdemo-fastapi-demo-service \
  --desired-count 1
```

## GitHub Actionsでの自動デプロイ

### GitHub環境設定 (pythondemo)

**Environment Secrets:**
- `AWS_OIDC_ROLE_ARN`: AWS OIDC Role ARN

**Environment Variables:**
- `AWS_REGION`: ap-northeast-1
- `ECR_REPOSITORY`: nrdemo-fastapi-demo-app
- `ECS_CLUSTER`: nrdemo-fastapi-demo-cluster
- `ECS_SERVICE`: nrdemo-fastapi-demo-service

### デプロイ方法

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

### 管理API (デモシナリオ制御)
- `POST /admin/failure` - エラーモード切替
- `POST /admin/slow` - スローモード切替
- `POST /admin/code-error` - コードエラーモード
- `POST /admin/db-error` - DBエラーモード
- `POST /admin/resource-error` - リソースエラーモード
- `GET /admin/status` - システムステータス

### ヘルスチェック
- `GET /health` - ヘルスチェック
- `GET /api/db-test` - データベース接続テスト

## ローカル開発環境

### セットアップ

```bash
# リポジトリをクローン
git clone https://github.com/Fukuda-FK/Python-demoapp.git
cd Python-demoapp

# 依存関係をインストール
cd app
pip install -r requirements.txt

# 環境変数を設定
cp config/.env.example .env
# .envファイルを編集してデータベース接続情報を設定
```

### ローカル実行

```bash
# New Relic設定ファイルを編集
# config/newrelic.iniのlicense_keyを設定

# アプリケーションを起動
cd app
newrelic-admin run-program uvicorn main:app --host 0.0.0.0 --port 3000
```

### Dockerでローカル実行

```bash
cd app
docker build -t fastapi-demo .
docker run -p 3000:3000 --env-file .env fastapi-demo
```

## インフラストラクチャ構成

### ネットワーク
- VPC (10.0.0.0/16)
- パブリックサブネット x2 (ECS配置)
- プライベートサブネット x2 (RDS配置)
- インターネットゲートウェイ

### コンピュート
- ECS Fargate (CPU: 512, Memory: 1024MB)
- アプリケーションコンテナ + New Relic Infrastructureサイドカー

### データベース
- RDS PostgreSQL 15.10 (db.t3.micro)
- 自動バックアップ無効 (デモ用途)

### セキュリティ
- ECSセキュリティグループ: ポート3000をAllowedIPAddressから許可
- DBセキュリティグループ: ポート5432をECSからのみ許可

## New Relic監視

### APM
- アプリケーションパフォーマンス監視
- トランザクショントレース
- エラー追跡
- カスタム属性

### Infrastructure
- ECSサイドカーコンテナとして実行
- コンテナメトリクス
- リソース使用状況

### Logs
- CloudWatch Logsに集約
- New Relic Logs in Context

## セキュリティに関する注意

**重要**: 以下のファイルには機密情報を含めないでください

- `.env` - 環境変数（.gitignoreに含まれています）
- `config/newrelic.ini` - プレースホルダーのみをコミット

**本番環境では必ず以下を実施してください:**
- 強力なデータベースパスワードを使用
- セキュリティグループで適切なIP制限を設定
- New Relicライセンスキーを環境変数で管理
- AWS Secrets Managerの使用を検討

## トラブルシューティング

### ECSタスクが起動しない
- CloudWatch Logsでエラーを確認
- セキュリティグループの設定を確認
- ECRイメージが存在するか確認

### データベース接続エラー
- RDSセキュリティグループがECSからのアクセスを許可しているか確認
- 環境変数のDB_HOSTが正しいか確認

### New Relicにデータが表示されない
- NEW_RELIC_LICENSE_KEYが正しく設定されているか確認
- New Relic Infrastructureサイドカーのログを確認

## ライセンス

MIT License

## 貢献

プルリクエストを歓迎します。大きな変更の場合は、まずissueを開いて変更内容を議論してください。
