# Pull Request: New Relic APMでインフラログを表示可能にする改善

## 概要
New Relic APMのエラー画面でインフラログが表示されない問題を修正しました。

## 変更内容

### 1. アプリケーションログ設定の強化 (`app/main.py`)
- New Relic専用のログフォーマッター（`NewRelicContextFormatter`）を追加
- ログにトレースIDとコンテキスト情報が自動付与されるように改善

### 2. New Relic設定の強化 (`app/newrelic.ini`)
- `application_logging.forwarding.context_data.enabled = true` を追加
- コンテキストデータ（トレースID、エンティティGUID）をログに含めるように設定

### 3. ECS環境変数の追加 (`cloudformation/fastapi-demo-ecs-infrastructure.yaml`)
- アプリケーションコンテナに `NEW_RELIC_LOG` と `NEW_RELIC_LOG_LEVEL` を追加
- New Relic Infrastructureコンテナに `NRIA_LOG_LEVEL` と `NRIA_CUSTOM_ATTRIBUTES` を追加

### 4. ドキュメント追加 (`INFRA_LOGS_FIX.md`)
- 改善内容の詳細説明
- デプロイ手順
- トラブルシューティングガイド

## 期待される効果

✅ New Relic APMのエラー画面で以下が表示されるようになります:
- エラー発生時刻前後のアプリケーションログ
- インフラメトリクス（CPU、メモリ使用率）
- トレースIDで紐付けられたログエントリ

✅ ログとエラーが自動的に関連付けられ、トラブルシューティングが容易になります

## テスト方法

1. Dockerイメージをビルドしてデプロイ
2. アプリケーションでエラーを発生させる
3. New Relic APM > Errors > [エラー詳細] > Logsタブを確認
4. ログとインフラメトリクスが表示されることを確認

## 関連ドキュメント
- `INFRA_LOGS_FIX.md`: 詳細な改善内容とデプロイ手順
- `NEWRELIC_LOGS_SETUP.md`: 既存のNew Relic設定ドキュメント

## レビュー依頼
この変更により、New Relic APMでのログ可視性が大幅に向上します。
masterブランチへのマージをお願いします。
