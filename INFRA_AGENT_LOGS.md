# New Relic Infrastructureエージェント経由でログを表示

## 概要
アプリケーションコードを変更せず、New Relic Infrastructureエージェント経由でログを収集し、APMエラー画面に表示します。

## 実施内容

### 1. 共有ボリュームの追加
アプリケーションコンテナとInfrastructureエージェントコンテナ間でログファイルを共有:
```yaml
Volumes:
  - Name: logs
    Host: {}
```

### 2. アプリケーションコンテナの設定
- ログを`/var/log/app/application.log`にも出力
- 標準出力とファイル出力を両方実施（teeコマンド使用）

### 3. Infrastructureエージェントの設定
- `NRIA_LOG_FORWARD=true`: ログ転送を有効化
- `/var/log/app`をマウントしてログファイルを読み取り
- ログに`logtype: infrastructure`属性を自動付与

## 動作の流れ

```
Pythonアプリケーション
  ↓ stdout (標準出力)
  ├→ CloudWatch Logs (awslogs driver)
  └→ /var/log/app/application.log (teeコマンド)
       ↓
New Relic Infrastructure Agent
  ↓ ログファイルを監視・収集
  ↓ logtype=infrastructure属性を付与
New Relic Logs
  ↓ trace.idで自動紐付け
APM Errors画面
  ├─ アプリケーションログ (APM経由)
  └─ インフラログ (Infrastructure経由) ← 新規追加
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
