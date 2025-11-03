# New Relic Logs in Context 設定完了ガイド

## 実施した変更内容

### 1. New Relic設定ファイルの作成

**ファイル**: `config/newrelic.ini`

```ini
[newrelic]
license_key = ${NEW_RELIC_LICENSE_KEY}
app_name = ${NEW_RELIC_APP_NAME}

monitor_mode = true
log_file = stdout
log_level = info

transaction_tracer.enabled = true
transaction_tracer.record_sql = obfuscated

error_collector.enabled = true

distributed_tracing.enabled = true

# Application Logging (Logs in Context)
application_logging.enabled = true
application_logging.forwarding.enabled = true
application_logging.forwarding.max_samples_stored = 10000
application_logging.metrics.enabled = true
application_logging.local_decorating.enabled = true
```

**重要な設定**:
- `application_logging.forwarding.enabled = true`: APM経由でログを直接New Relicに送信
- `application_logging.local_decorating.enabled = true`: NR-LINKINGマーカーを自動付与（Infrastructure経由のログも紐付け可能）

### 2. Dockerfileの修正

**変更内容**:
```dockerfile
# New Relic設定ファイルをコピー
COPY ../config/newrelic.ini /app/newrelic.ini

# 環境変数を設定
ENV NEW_RELIC_CONFIG_FILE=/app/newrelic.ini
```

### 3. CloudFormationテンプレートの修正

**変更内容**:
ECSタスク定義に環境変数を追加：
```yaml
- Name: NEW_RELIC_CONFIG_FILE
  Value: /app/newrelic.ini
```

### 4. アプリケーションコード（既に実装済み）

`app/main.py`には既に以下が実装されています：

✅ `import newrelic.agent`
✅ `logging.basicConfig()` でログ設定
✅ `logger.info()` / `logger.error()` でログ出力
✅ `newrelic.agent.add_custom_attributes()` でカスタム属性追加
✅ `newrelic.agent.notice_error()` でエラー通知

**追加コード不要**: 既存のコードで完全に動作します。

## 実現される機能

### 1. APM経由のログ転送（リアルタイム）

```
Pythonアプリケーション
  ↓ logger.error("Error message")
[New Relic APM Agent]
  ↓ 自動的にtrace.idを付与
  ↓ JSONメタデータとして送信
New Relic Logs
```

### 2. Infrastructure経由のログ転送（CloudWatch Logs経由）

```
Pythonアプリケーション
  ↓ logger.error("Error message")
CloudWatch Logs (標準出力)
  ↓ NR-LINKINGマーカー付き
  ↓ "Error message NR-LINKING|trace_id|..."
[New Relic Infrastructure Agent]
  ↓ trace.idを抽出
New Relic Logs
```

### 3. APM Errorsでの統合表示

New Relic UI: **APM > Errors > [エラー詳細]**

```
┌─ Error Details ─────────────────────────────────┐
│ Error Class: ZeroDivisionError                  │
│ Error Message: division by zero                 │
│ trace.id: abc123def456                          │
│                                                  │
│ Custom Attributes:                              │
│   payment.amount: 10000                         │
│   payment.storeId: STORE001                     │
│   error.scenario: code_error                    │
└──────────────────────────────────────────────────┘

┌─ Logs (trace.id=abc123def456) ──────────────────┐
│ 09:48:14 [INFO] Payment attempt: ¥10000         │
│ 09:48:15 [ERROR] [CODE ERROR] Division by zero  │
│ 09:48:15 [INFO] Database connection released    │
└──────────────────────────────────────────────────┘

┌─ Infrastructure (ECS Task) ─────────────────────┐
│ CPU Usage: 45%                                  │
│ Memory: 512MB / 1GB (51%)                       │
└──────────────────────────────────────────────────┘
```

## デプロイ手順

### 1. Dockerイメージのビルドとプッシュ

```bash
# ECRにログイン
aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.ap-northeast-1.amazonaws.com

# イメージをビルド
cd app
docker build -t nrdemo-fastapi-demo-app:latest .

# タグ付け
docker tag nrdemo-fastapi-demo-app:latest <account-id>.dkr.ecr.ap-northeast-1.amazonaws.com/nrdemo-fastapi-demo-app:latest

# プッシュ
docker push <account-id>.dkr.ecr.ap-northeast-1.amazonaws.com/nrdemo-fastapi-demo-app:latest
```

### 2. CloudFormationスタックの更新

```bash
aws cloudformation update-stack \
  --stack-name your-stack-name \
  --template-body file://cloudformation/fastapi-demo-ecs-infrastructure.yaml \
  --parameters \
    ParameterKey=NewRelicLicenseKey,ParameterValue=YOUR_LICENSE_KEY \
    ParameterKey=DBPassword,ParameterValue=YOUR_DB_PASSWORD \
    ParameterKey=AllowedIPAddress,ParameterValue=0.0.0.0/0 \
  --capabilities CAPABILITY_NAMED_IAM
```

### 3. ECSサービスの更新（自動）

CloudFormationスタック更新により、ECSサービスが自動的に新しいタスク定義を使用します。

### 4. GitHub Actionsによる自動デプロイ（推奨）

masterブランチにpushすると自動的にデプロイされます：

```bash
git add .
git commit -m "Add New Relic Logs in Context configuration"
git push origin master
```

## 動作確認

### 1. エラーを発生させる

アプリケーションの管理画面で「シナリオ1: コードエラー」をONにして決済を実行。

### 2. New Relic UIで確認

1. **APM > Errors** を開く
2. 最新のエラーをクリック
3. **Logs** タブをクリック
4. エラー発生時刻前後のログが自動表示されることを確認

### 3. 確認項目

✅ APMエラー画面に「Logs」タブが表示される
✅ エラー発生時刻前後のログが時系列で表示される
✅ カスタム属性（payment.amount, payment.storeId等）が表示される
✅ ログメッセージに「NR-LINKING」マーカーが含まれている（CloudWatch Logs確認時）
✅ trace.idでログとエラーが紐付いている

## トラブルシューティング

### ログが表示されない場合

**確認1**: CloudWatch Logsにログが出力されているか
```bash
aws logs tail /ecs/nrdemo-fastapi-demo-app --follow
```

**確認2**: New Relic設定ファイルが正しく読み込まれているか
```bash
# ECSタスクのログを確認
aws ecs describe-tasks --cluster nrdemo-fastapi-demo-cluster --tasks <task-id>
```

**確認3**: 環境変数が正しく設定されているか
```bash
# ECSタスク定義を確認
aws ecs describe-task-definition --task-definition nrdemo-fastapi-demo-task
```

### NR-LINKINGマーカーが付与されない場合

**原因**: `application_logging.local_decorating.enabled = false`

**解決策**: `config/newrelic.ini`で`local_decorating.enabled = true`に設定されていることを確認。

### APM経由のログは表示されるが、Infrastructure経由のログが表示されない場合

**原因**: New Relic Infrastructure Agentがサイドカーコンテナとして動作していない。

**解決策**: CloudFormationテンプレートで`newrelic-infra`コンテナが定義されていることを確認（既に実装済み）。

## まとめ

この設定により、以下が自動的に実現されます：

1. **APM経由**: アプリケーションログがリアルタイムでNew Relicに送信
2. **Infrastructure経由**: CloudWatch Logsからもログが収集
3. **自動紐付け**: trace.idでAPMエラーとログが自動的に関連付け
4. **統合表示**: New Relic UIでエラー詳細とログを一画面で確認

**追加のコード変更は不要**です。既存のアプリケーションコードがそのまま動作します。
