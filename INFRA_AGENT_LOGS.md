# ECS FargateでNew Relic Infrastructureエージェント経由のログ表示

## 概要
アプリケーションコードを変更せず、FireLens経由でログをNew Relicに送信し、APMエラー画面でアプリログとインフラログを統合表示します。

## 実施内容

### 1. FireLensコンテナの追加
Fluent Bitをサイドカーコンテナとして追加:
```yaml
- Name: log_router
  Image: amazon/aws-for-fluent-bit:latest
  FirelensConfiguration:
    Type: fluentbit
    Options:
      enable-ecs-log-metadata: 'true'
```

### 2. アプリケーションコンテナのログドライバー変更
標準出力をFireLens経由でNew Relicに送信:
```yaml
LogConfiguration:
  LogDriver: awsfirelens
  Options:
    Name: newrelic
    apiKey: !Ref NewRelicLicenseKey
    endpoint: https://log-api.newrelic.com/log/v1
```

### 3. Infrastructureエージェントの設定
ECSタスクメトリクスを収集

## 動作の流れ

```
Pythonアプリケーション
  ↓ stdout (標準出力)
  ↓ logger.info() / logger.error()
  ↓ NR-LINKINGマーカー付き
FireLens (Fluent Bit)
  ↓ ログを受信
  ↓ ECSメタデータを付与
  ↓ (ecs_cluster, ecs_task_arn等)
New Relic Logs API
  ↓ 直接送信
  ↓ logtype=infrastructure属性を付与
New Relic Logs
  ↓ trace.idで自動紐付け
APM Errors画面
  ├─ アプリケーションログ (APM経由)
  └─ インフラログ (FireLens経由) ← 新規追加
```

## デプロイ手順

### 1. CloudFormationスタックの更新

```bash
aws cloudformation update-stack \
  --stack-name your-stack-name \
  --template-body file://cloudformation/fastapi-demo-ecs-infrastructure.yaml \
  --parameters \
    ParameterKey=NewRelicLicenseKey,UsePreviousValue=true \
    ParameterKey=DBPassword,UsePreviousValue=true \
    ParameterKey=AllowedIPAddress,UsePreviousValue=true \
  --capabilities CAPABILITY_NAMED_IAM
```

### 2. ECSサービスの強制更新

```bash
aws ecs update-service \
  --cluster nrdemo-fastapi-demo-cluster \
  --service nrdemo-fastapi-demo-service \
  --force-new-deployment
```

## 確認方法

### 1. エラーを発生させる
アプリケーションでエラーシナリオを実行

### 2. New Relic APM > Errors > Logsタブを確認

以下のように表示されます:
```
Logs
timestamp | message
----------|----------
18:47:26  | Payment attempt: ¥93000.0 at STORE001  (APM経由)
18:47:26  | [DB ERROR] Transaction table access failed  (APM経由)
18:47:26  | Payment attempt: ¥93000.0 at STORE001  (Infrastructure経由) ← 新規
18:47:26  | [DB ERROR] Transaction table access failed  (Infrastructure経由) ← 新規
```

### 3. ログ属性で確認
- APM経由: `instrumentation.provider = newrelic`
- Infrastructure経由: `logtype = infrastructure`

## トラブルシューティング

### Infrastructureログが表示されない場合

**確認1**: ログファイルが作成されているか
```bash
aws ecs execute-command \
  --cluster nrdemo-fastapi-demo-cluster \
  --task <task-id> \
  --container newrelic-infra \
  --command "ls -la /var/log/app"
```

**確認2**: Infrastructureエージェントがログを読み取っているか
```bash
aws logs tail /ecs/nrdemo-fastapi-demo-app --follow --filter-pattern "newrelic-infra"
```

**確認3**: New Relic Logsで検索
```
logtype:infrastructure AND service:fastapi-demo
```

## まとめ

この設定により:
- ✅ アプリケーションコードは変更不要
- ✅ 同じログがAPMとInfrastructure両方から送信
- ✅ APMエラー画面でアプリログとインフラログを統合表示
- ✅ `logtype`属性でログの送信元を識別可能
