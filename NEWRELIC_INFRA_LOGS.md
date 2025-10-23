# New Relic Infrastructure & Logs セットアップ完了

## インストール済みコンポーネント

✅ **New Relic Infrastructure Agent** (v1.70.0)
✅ **Fluent Bit** (v3.2.10) - ログ収集
✅ **Logs Integration** - アプリケーションログ転送

## 設定情報

- **アカウントID**: YOUR_ACCOUNT_ID
- **APIキー**: YOUR_API_KEY
- **Infraキー**: YOUR_INSTANCE_ID

## 収集されるデータ

### Infrastructure Monitoring
- ✅ CPU使用率
- ✅ メモリ使用量
- ✅ ディスクI/O
- ✅ ネットワークトラフィック
- ✅ プロセス情報
- ✅ システムメトリクス

### Logs
- ✅ FastAPIアプリケーションログ (systemd経由)
- ✅ ログタイプ: fastapi-application
- ✅ サービス名: FastAPI-ECSite

## 設定ファイル

**ログ設定**: `/etc/newrelic-infra/logging.d/fastapi-demo-logs.yml`
```yaml
logs:
  - name: fastapi-demo-logs
    systemd: fastapi-demo
    attributes:
      logtype: fastapi-application
      service: FastAPI-ECSite
```

## サービス管理

```bash
# Infrastructure Agent
sudo systemctl status newrelic-infra
sudo systemctl restart newrelic-infra
sudo systemctl stop newrelic-infra

# ログ確認
sudo journalctl -u newrelic-infra -f
```

## New Relic UIで確認

### Infrastructure
🔗 https://onenr.io/01wZ05eybj6
- ホストメトリクス
- プロセス監視
- システムパフォーマンス

### Logs
🔗 https://onenr.io/0LRE0pKylwa
- アプリケーションログ
- エラーログ
- リクエストログ

## 統合監視

New Relic UIで以下が統合表示されます:
- **APM**: FastAPI-ECSite (アプリケーション性能)
- **Infrastructure**: EC2インスタンス (i-06488d2eed723fbb8)
- **Logs**: アプリケーションログ
- **Database**: RDS PostgreSQL (接続情報)

## テスト

```bash
# トランザクション生成
curl -X POST http://43.207.1.222:3000/api/payment \
  -H "Content-Type: application/json" \
  -d '{"amount": 5000, "cardNumber": "1234567890123456", "storeId": "STORE001"}'

# ログ生成
curl http://43.207.1.222:3000/api/db-test
```

数分後にNew Relic UIでデータが表示されます。
