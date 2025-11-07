# New Relic APMでインフラログを表示するための改善

## 問題
New Relic APMのエラー画面でインフラログが表示されない

## 実施した改善内容

### 1. Pythonアプリケーションのログ設定強化 (`app/main.py`)

```python
# New Relicログハンドラーを追加
try:
    from newrelic.agent import NewRelicContextFormatter
    handler = logging.StreamHandler()
    formatter = NewRelicContextFormatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
except ImportError:
    pass
```

**効果**: ログにNew Relicのトレース情報が自動的に付与され、APMとインフラログが連携します。

### 2. New Relic設定ファイルの強化 (`app/newrelic.ini`)

追加した設定:
```ini
# Infrastructure Integration
application_logging.forwarding.context_data.enabled = true
application_logging.forwarding.context_data.include = *
application_logging.forwarding.context_data.exclude =
```

**効果**: コンテキストデータ（トレースID、エンティティGUIDなど）がログに含まれ、インフラログとの紐付けが強化されます。

### 3. ECSタスク定義の環境変数追加 (`cloudformation/fastapi-demo-ecs-infrastructure.yaml`)

アプリケーションコンテナに追加:
```yaml
- Name: NEW_RELIC_LOG
  Value: stdout
- Name: NEW_RELIC_LOG_LEVEL
  Value: info
```

New Relic Infrastructureコンテナに追加:
```yaml
- Name: NRIA_LOG_LEVEL
  Value: info
- Name: NRIA_CUSTOM_ATTRIBUTES
  Value: '{"environment":"demo","service":"fastapi"}'
```

**効果**: ログ出力が標準出力に確実に送られ、CloudWatch Logsを経由してNew Relicに転送されます。

## デプロイ手順

### 1. Dockerイメージのビルドとプッシュ

```bash
cd app
docker build -t nrdemo-fastapi-demo-app:latest .

# ECRにログイン
aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.ap-northeast-1.amazonaws.com

# タグ付けとプッシュ
docker tag nrdemo-fastapi-demo-app:latest <account-id>.dkr.ecr.ap-northeast-1.amazonaws.com/nrdemo-fastapi-demo-app:latest
docker push <account-id>.dkr.ecr.ap-northeast-1.amazonaws.com/nrdemo-fastapi-demo-app:latest
```

### 2. CloudFormationスタックの更新

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

### 3. ECSサービスの強制更新（新しいタスク定義を適用）

```bash
aws ecs update-service \
  --cluster nrdemo-fastapi-demo-cluster \
  --service nrdemo-fastapi-demo-service \
  --force-new-deployment
```

## 動作確認

### 1. エラーを発生させる

アプリケーションの管理画面で任意のエラーシナリオをONにして決済を実行。

### 2. New Relic UIで確認

1. **APM > Errors** を開く
2. 最新のエラーをクリック
3. **Logs** タブをクリック
4. 以下が表示されることを確認:
   - エラー発生時刻前後のアプリケーションログ
   - インフラメトリクス（CPU、メモリ使用率）
   - トレースIDで紐付けられたログエントリ

### 3. 確認項目チェックリスト

- [ ] APMエラー画面に「Logs」タブが表示される
- [ ] エラー発生時刻前後のログが時系列で表示される
- [ ] ログに`trace.id`が含まれている
- [ ] インフラメトリクス（CPU、メモリ）が表示される
- [ ] CloudWatch Logsにログが出力されている
- [ ] New Relic Logsでログが検索できる（`entity.guid`でフィルタ）

## トラブルシューティング

### ログが表示されない場合

**確認1**: CloudWatch Logsにログが出力されているか
```bash
aws logs tail /ecs/nrdemo-fastapi-demo-app --follow
```

**確認2**: ECSタスクが正常に起動しているか
```bash
aws ecs list-tasks --cluster nrdemo-fastapi-demo-cluster --service-name nrdemo-fastapi-demo-service
aws ecs describe-tasks --cluster nrdemo-fastapi-demo-cluster --tasks <task-arn>
```

**確認3**: New Relic Agentが正常に動作しているか
```bash
# ECSタスクのログを確認
aws logs tail /ecs/nrdemo-fastapi-demo-app --follow --filter-pattern "newrelic"
```

### インフラメトリクスが表示されない場合

**原因**: New Relic Infrastructureコンテナが起動していない

**解決策**:
```bash
# タスク定義を確認
aws ecs describe-task-definition --task-definition nrdemo-fastapi-demo-task

# newrelic-infraコンテナのログを確認
aws logs tail /ecs/nrdemo-fastapi-demo-app --follow --log-stream-name-prefix newrelic
```

### ログとエラーが紐付かない場合

**原因**: `trace.id`がログに含まれていない

**解決策**:
1. `NewRelicContextFormatter`が正しく適用されているか確認
2. `application_logging.local_decorating.enabled = true`が設定されているか確認
3. アプリケーションを再起動

## 期待される結果

改善後、New Relic APMのエラー画面で以下が表示されるようになります:

```
┌─ Error Details ─────────────────────────────────┐
│ Error Class: ZeroDivisionError                  │
│ Error Message: division by zero                 │
│ trace.id: abc123def456                          │
└──────────────────────────────────────────────────┘

┌─ Logs (trace.id=abc123def456) ──────────────────┐
│ 09:48:14 [INFO] Payment attempt: ¥10000         │
│ 09:48:15 [ERROR] [CODE ERROR] Division by zero  │
│ 09:48:15 [INFO] Database connection released    │
└──────────────────────────────────────────────────┘

┌─ Infrastructure (ECS Task) ─────────────────────┐
│ CPU Usage: 45%                                  │
│ Memory: 512MB / 1GB (51%)                       │
│ Network I/O: 1.2 MB/s                           │
└──────────────────────────────────────────────────┘
```

## まとめ

この改善により:
1. ✅ アプリケーションログにトレース情報が自動付与
2. ✅ インフラログとAPMエラーが`trace.id`で紐付け
3. ✅ New Relic UIでエラー、ログ、インフラメトリクスを統合表示
4. ✅ CloudWatch Logs経由でログが確実に転送

追加のコード変更は不要で、既存のログ出力がそのまま活用されます。
