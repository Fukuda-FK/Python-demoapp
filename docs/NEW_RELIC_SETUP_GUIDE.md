# New Relic 完全セットアップガイド

## 目次
1. [APMエージェント導入](#1-apmエージェント導入)
2. [Infrastructureエージェント導入](#2-infrastructureエージェント導入)
3. [Logs in Context設定](#3-logs-in-context設定)
4. [動作確認](#4-動作確認)

---

## 1. APMエージェント導入

### 目的
アプリケーションのパフォーマンス監視とエラートラッキング

### 手順

#### 1.1 New Relic Pythonエージェントのインストール

**作業内容**: Pythonパッケージマネージャーでエージェントをインストール

```bash
pip3 install newrelic
```

**この作業で実現すること**:
- アプリケーションコードを自動計測
- トランザクション、エラー、外部呼び出しを記録
- パフォーマンスメトリクスを収集

---

#### 1.2 設定ファイル (newrelic.ini) の作成

**作業内容**: New Relicの設定ファイルを作成

```ini
[newrelic]
# ライセンスキー（New Relic UIから取得）
license_key = YOUR_LICENSE_KEY

# アプリケーション名（New Relic UIに表示される名前）
app_name = FastAPI-ECSite

# 監視モード有効化
monitor_mode = true

# ログ出力先（標準出力）
log_file = stdout
log_level = info

# トランザクショントレーサー
transaction_tracer.enabled = true
transaction_tracer.record_sql = obfuscated  # SQL文を難読化して記録

# エラーコレクター
error_collector.enabled = true

# 分散トレーシング
distributed_tracing.enabled = true

# Application Logging (Logs in Context)
application_logging.enabled = true
application_logging.forwarding.enabled = true
application_logging.metrics.enabled = true
application_logging.local_decorating.enabled = true
```

**この作業で実現すること**:
- アプリケーション名の設定
- データ送信先の指定
- 監視機能の有効化
- ログとトレースの自動紐付け

---

#### 1.3 アプリケーションコードの修正

### 必須: アプリコードに追記が必要な情報

#### 最低限必要なコード（1行）

```python
import newrelic.agent  # New Relicモジュールのimport
```

**重要**: `import newrelic.agent` だけで、New Relicが自動的に：
- ログを収集
- trace.idを付与
- NR-LINKINGマーカーを追加
- APM Errorsと紐付け

---

#### logging設定は必須？

**A: いいえ、既にアプリケーションでログ出力をしている場合は不要です。**

**パターン1: 既にログ設定がある場合（追加不要）**
```python
# 既存のアプリケーションコード
import logging
logger = logging.getLogger(__name__)

# New Relicを追加する場合
import newrelic.agent  # ← これだけ追加！

# 既存のログ出力はそのまま使える
logger.info("Application started")
logger.error("Error occurred")
```

**パターン2: ログ設定がない場合（追加必要）**
```python
import logging
import newrelic.agent

# ログ設定を追加（ログ出力を有効化するため）
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ログ出力
logger.info("Application started")
logger.error("Error occurred")
```

**まとめ**:

| 状況 | 必要なコード |
|------|----------------|
| 既に`logger.info()`等を使っている | `import newrelic.agent` のみ |
| ログ出力をまだしていない | `import newrelic.agent` + `logging.basicConfig()` + `logger = logging.getLogger()` |

---

#### オプション: カスタム属性とエラー通知（推奨）

業務情報を追加したい場合のみ追記：

```python
@app.post("/api/payment")
async def payment(req: PaymentRequest):
    # オプション1: カスタム属性（業務情報を追加）
    newrelic.agent.add_custom_attributes([
        ('payment.amount', req.amount),
        ('payment.storeId', req.storeId)
    ])
    
    logger.info(f"Payment attempt: ¥{req.amount}")
    
    try:
        # 決済処理
        process_payment(req)
    except Exception as e:
        logger.error(f"Payment error: {str(e)}")
        newrelic.agent.notice_error()  # オプション2: エラー通知
        raise
```

**カスタム属性とエラー通知の必要性**:

| 機能 | 必須？ | 理由 |
|------|--------|------|
| `import newrelic.agent` | 必須 | New Relic機能を使うため |
| `logging.basicConfig()` | 条件付き | 既にログ設定があれば不要 |
| `logger.info/error()` | 必須 | ログを出力する |
| `add_custom_attributes()` | オプション | 業務情報でフィルタリングしたい場合 |
| `notice_error()` | オプション | エラーを明示的に記録したい場合 |

---

#### 完全な例（推奨構成）

```python
import logging
import newrelic.agent
from fastapi import FastAPI, HTTPException

# ロギング設定（必須）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.post("/api/payment")
async def payment(req: PaymentRequest):
    # カスタム属性（オプション）
    newrelic.agent.add_custom_attributes([
        ('payment.amount', req.amount),
        ('payment.storeId', req.storeId),
        ('payment.cardLast4', req.cardNumber[-4:] if req.cardNumber else 'N/A')
    ])
    
    # 通常のログ出力（必須）
    logger.info(f"Payment attempt: ¥{req.amount} at {req.storeId}")
    
    try:
        # 業務処理
        result = await process_payment(req)
        logger.info(f"Payment successful: {result}")
        return result
    except Exception as e:
        # エラーログ（必須）
        logger.error(f"Payment error: {str(e)}")
        # エラー通知（オプション）
        newrelic.agent.notice_error()
        raise HTTPException(status_code=500, detail="Payment failed")
```

---

#### まとめ: アプリコードに追記が必要なもの

**必須（1行）**:
```python
import newrelic.agent
```

**条件付き（ログ設定がない場合のみ）**:
```python
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

**オプション（推奨）**:
```python
newrelic.agent.add_custom_attributes([...])  # 業務情報追加
newrelic.agent.notice_error()                # エラー明示通知
```

**不要（自動生成）**:
- NR-LINKINGマーカーの手動追加
- trace.idの手動設定
- span.idの手動設定
- entity.guidの手動設定

**この作業で実現すること**:
- 構造化ログの出力
- エラーの自動検知と記録
- カスタム属性による詳細な分析
- ログとAPMトレースの紐付け

---

#### 1.4 アプリケーション起動方法の変更

**作業内容**: New Relicエージェント経由でアプリケーションを起動

**変更前**:
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 3000
```

**変更後**:
```bash
NEW_RELIC_CONFIG_FILE=newrelic.ini newrelic-admin run-program python -m uvicorn main:app --host 0.0.0.0 --port 3000
```

**この作業で実現すること**:
- アプリケーションコードの自動計測
- リクエスト/レスポンスの記録
- データベースクエリの追跡
- 外部API呼び出しの監視

---

#### 1.5 systemdサービスファイルの更新

**作業内容**: 自動起動設定にNew Relicを組み込む

```ini
[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/fastapi-demo-system
Environment=PATH=/home/ec2-user/.local/bin:/usr/local/bin:/usr/bin
Environment=NEW_RELIC_CONFIG_FILE=/home/ec2-user/fastapi-demo-system/newrelic.ini
ExecStart=/home/ec2-user/.local/bin/newrelic-admin run-program /usr/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 3000
Restart=always
```

**この作業で実現すること**:
- サーバー再起動時も自動的にNew Relic監視開始
- 設定ファイルパスの明示的な指定
- 安定した監視環境の構築

---

## 2. Infrastructureエージェント導入

### 目的
サーバーリソース（CPU、メモリ、ディスク）の監視

### 手順

#### 2.1 New Relic CLIとInfrastructureエージェントのインストール

**作業内容**: 公式インストールスクリプトを実行

```bash
curl -Ls https://download.newrelic.com/install/newrelic-cli/scripts/install.sh | bash && \
sudo NEW_RELIC_API_KEY=YOUR_API_KEY \
     NEW_RELIC_ACCOUNT_ID=YOUR_ACCOUNT_ID \
     /usr/local/bin/newrelic install -n logs-integration
```

**この作業で実現すること**:
- Infrastructureエージェントのインストール
- Fluent Bit（ログ収集ツール）のインストール
- システムメトリクスの自動収集開始
- ログ転送機能の有効化

---

#### 2.2 アプリケーションログ転送設定

**作業内容**: systemdログを収集する設定ファイルを作成

```yaml
# /etc/newrelic-infra/logging.d/fastapi-demo.yml
logs:
  - name: fastapi-demo-logs
    systemd: fastapi-demo  # systemdサービス名
    attributes:
      logtype: fastapi-application
      service: FastAPI-ECSite
```

**この作業で実現すること**:
- アプリケーションログの自動収集
- ログにサービス名を自動付与
- New Relic Logsへの転送
- APMとの自動紐付け

---

#### 2.3 Infrastructureエージェントの再起動

**作業内容**: 設定を反映させるためサービス再起動

```bash
sudo systemctl restart newrelic-infra
```

**この作業で実現すること**:
- 新しいログ設定の適用
- ログ収集の開始
- メトリクスとログの統合監視

---

## 3. Logs in Context設定

### 目的
APMエラーとログを自動で紐付け、原因特定を迅速化

### インフラログとアプリログの統合アーキテクチャ

本システムでは、**2つの独立したログ収集経路**を組み合わせて、完全なオブザーバビリティを実現しています：

#### ログ収集の2つの経路

**経路1: APMエージェント経由（アプリケーションログ）**
```
Pythonアプリケーション
  ↓ logger.info() / logger.error()
[New Relic APM Agent]
  ↓ application_logging.forwarding.enabled = true
New Relic Logs (直接転送)
```

**経路2: Infrastructureエージェント経由（systemdログ）**
```
Pythonアプリケーション
  ↓ logger.info() / logger.error()
systemd journal (標準出力)
  ↓ journalctl -u fastapi-demo
[Fluent Bit] ← /etc/newrelic-infra/logging.d/fastapi-demo.yml
  ↓
[Infrastructure Agent]
  ↓
New Relic Logs (インフラ経由転送)
```

#### なぜ2つの経路が必要なのか

| 項目 | APM経由 | Infrastructure経由 |
|------|---------|--------------------|
| **収集対象** | アプリケーション内部ログ | systemd全体のログ |
| **メタデータ** | trace.id, span.id, entity.guid | hostname, service, logtype |
| **用途** | エラートレースとの紐付け | サーバー全体の監視 |
| **遅延** | リアルタイム | 数秒の遅延 |
| **利点** | APM Errorsと完全統合 | アプリ停止時もログ収集可能 |

#### 2つの経路が同じログをどう扱うか

**重複排除の仕組み**:

1. **APM経由のログ**には `trace.id` が自動付与される
2. **Infrastructure経由のログ**には `hostname` と `service` が付与される
3. New Relicプラットフォームが **trace.id** で自動的にグループ化
4. 同じログが2回送信されても、trace.idで統合表示される

**実際のログフロー例**:

```python
# アプリケーションコード
logger.error(f"[DB ERROR] Transaction table access failed - Amount: ¥{req.amount}")
newrelic.agent.notice_error()
```

**↓ APM経由で送信されるログ**:
```json
{
  "message": "[DB ERROR] Transaction table access failed - Amount: ¥10000",
  "trace.id": "abc123def456",
  "span.id": "span789",
  "entity.guid": "MzY4ODEyMHxBUE18QVBQTElDQVRJT058MTEwMzQ0NzgwNg",
  "entity.name": "FastAPI-ECSite",
  "timestamp": 1729692495000,
  "log.level": "ERROR"
}
```

**↓ Infrastructure経由で送信されるログ**:
```json
{
  "message": "[DB ERROR] Transaction table access failed - Amount: ¥10000 NR-LINKING|abc123def456|span789|...",
  "hostname": "ip-10-123-10-95.ap-northeast-1.compute.internal",
  "service": "FastAPI-ECSite",
  "logtype": "fastapi-application",
  "timestamp": 1729692495000,
  "plugin.type": "systemd"
}
```

**↓ New Relic UIでの統合表示**:
```
APM > Errors > [エラー詳細]
  ├─ Error Details (APMから)
  │   ├─ error.class: PostgresError
  │   ├─ error.message: Transaction table access failed
  │   └─ trace.id: abc123def456
  │
  └─ Logs (両方の経路から統合)
      ├─ [APM経由] [DB ERROR] Transaction table access failed
      ├─ [Infra経由] Payment attempt: ¥10000 at STORE001
      └─ [Infra経由] INFO: Database connection pool status
```

### アプリエラーとインフラログの関連付けの仕組み

#### 3つの識別子による自動紐付け

```
[アプリケーション実行]
    ↓
[New Relic APM Agent]
    ├─ trace.id (トレースID) を生成
    ├─ span.id (スパンID) を生成
    └─ entity.guid (エンティティGUID) を付与
    ↓
[ログ出力時に自動付与]
    ├─ trace.id: "abc123..."  ← APMトレースと紐付け
    ├─ span.id: "def456..."   ← 特定の処理と紐付け
    ├─ entity.guid: "MzY4..." ← アプリケーションと紐付け
    ├─ entity.name: "FastAPI-ECSite"
    └─ hostname: "ip-10-123-10-95"
    ↓
[Infrastructure Agent収集]
    ├─ hostname で同一サーバーを識別
    ├─ timestamp で時間軸を合わせる
    └─ entity.guid でアプリケーションを特定
    ↓
[New Relic Platform]
    ├─ trace.id でAPMエラーとログを紐付け
    ├─ hostname でInfrastructureメトリクスと紐付け
    ├─ timestamp で時系列に並べる
    └─ entity.guid でアプリとインフラを統合
```

#### 具体例：エラー発生時の完全な関連付けフロー

**ステップ1: エラー発生とAPMトレース生成**
```python
# コード実行
@app.post("/api/payment")
async def payment(req: PaymentRequest):
    # APMエージェントが自動的にtrace.idを生成
    # trace.id: "abc123def456"
    
    if db_error_mode:
        logger.error(f"[DB ERROR] Transaction table access failed")
        newrelic.agent.notice_error()  # エラーをAPMに記録
        raise HTTPException(status_code=500, ...)
```

**ステップ2: APMエージェントがログにメタデータを自動付与**
```json
{
  "message": "[DB ERROR] Transaction table access failed - Amount: ¥10000, Store: STORE001",
  "trace.id": "abc123def456",
  "span.id": "span789",
  "entity.guid": "MzY4ODEyMHxBUE18QVBQTElDQVRJT058MTEwMzQ0NzgwNg",
  "entity.name": "FastAPI-ECSite",
  "hostname": "ip-10-123-10-95.ap-northeast-1.compute.internal",
  "timestamp": 1729692495000,
  "log.level": "ERROR",
  "error.scenario": "database_error",
  "error.severity": "high"
}
```

**ステップ3: 標準出力に「NR-LINKING」マーカー付きログ出力**
```
2025-10-23 09:48:15 - main - ERROR - [DB ERROR] Transaction table access failed - Amount: ¥10000, Store: STORE001 NR-LINKING|abc123def456|span789|ip-10-123-10-95.ap-northeast-1.compute.internal|MzY4ODEyMHxBUE18QVBQTElDQVRJT058MTEwMzQ0NzgwNg|FastAPI-ECSite||
```

**ステップ4: Fluent BitがsystemdログからNR-LINKINGを抽出**
```yaml
# /etc/newrelic-infra/logging.d/fastapi-demo.yml
logs:
  - name: fastapi-demo-logs
    systemd: fastapi-demo
    attributes:
      logtype: fastapi-application
      service: FastAPI-ECSite
```

Fluent Bitが自動的に:
- `NR-LINKING|abc123def456|...` を検出
- trace.idを抽出してメタデータとして付与
- Infrastructureエージェント経由でNew Relicに送信

**ステップ5: New Relicプラットフォームでの統合**

```
[New Relic Logs Database]
  ↓ trace.id="abc123def456" でクエリ
  |
  ├─ [APM経由のログ] ← リアルタイム、完全なメタデータ
  │   ├─ [DB ERROR] Transaction table access failed
  │   ├─ trace.id: abc123def456
  │   ├─ entity.guid: MzY4...
  │   └─ error.scenario: database_error
  │
  └─ [Infrastructure経由のログ] ← systemd全体のコンテキスト
      ├─ Payment attempt: ¥10000 at STORE001
      ├─ INFO: Database connection pool acquired
      ├─ [DB ERROR] Transaction table access failed (重複)
      └─ hostname: ip-10-123-10-95
```

**ステップ6: APM Errors画面での表示**

New Relic UIの **APM > Errors > [エラー詳細]** で以下が自動的に統合表示される:

```
┌─ Error Details ─────────────────────────────────┐
│ Error Class: PostgresError                      │
│ Error Message: Transaction table access failed  │
│ trace.id: abc123def456                          │
│ Timestamp: 2025-10-23 09:48:15                  │
│                                                  │
│ Custom Attributes:                              │
│   payment.amount: 10000                         │
│   payment.storeId: STORE001                     │
│   error.scenario: database_error                │
│   error.severity: high                          │
└──────────────────────────────────────────────────┘

┌─ Logs (trace.id=abc123def456) ──────────────────┐
│ 09:48:14 [INFO] Payment attempt: ¥10000      │ ← Infra経由
│ 09:48:15 [ERROR] [DB ERROR] Transaction...   │ ← APM経由
│ 09:48:15 [ERROR] [DB ERROR] Transaction...   │ ← Infra経由(重複)
│ 09:48:15 [INFO] Database connection released    │ ← Infra経由
└──────────────────────────────────────────────────┘

┌─ Infrastructure (hostname=ip-10-123-10-95) ─────┐
│ CPU Usage: 45% (09:48:15時点)                   │
│ Memory: 512MB / 1GB (51%)                       │
│ Disk I/O: 120 IOPS                              │
└──────────────────────────────────────────────────┘

┌─ Related Entities (entity.guid=MzY4...) ────────┐
│ • FastAPI-ECSite (APM)                          │
│ • ip-10-123-10-95 (Infrastructure)              │
│ • payment_demo (Database)                       │
└──────────────────────────────────────────────────┘
```

#### なぜエラーに沿ったログが自動的にグループ化されるのか

**理由1: trace.idによる完全一致**
- APMエージェントが生成した `trace.id` が全ログに付与される
- New Relicは `trace.id` でログをクエリして自動グループ化
- 同じHTTPリクエスト内のすべてのログが1つのトレースに紐付く

**理由2: NR-LINKINGマーカーによる自動抽出**
```
ログ出力: "Error message NR-LINKING|trace_id|span_id|hostname|entity_guid|entity_name||"
                        ↑
                  この部分をFluent Bitが自動検出
                        ↓
              メタデータとして構造化
                        ↓
              New Relicに送信時に付与
```

**理由3: タイムスタンプによる時系列整列**
- すべてのログに正確なタイムスタンプが付与される
- New Relicが時系列順に自動ソート
- エラー前後のログが時系列で表示される

**理由4: entity.guidによるアプリケーション識別**
- 同じアプリケーション（FastAPI-ECSite）のログのみを抽出
- 他のアプリケーションのログは除外される
- マイクロサービス環境でも正確に識別

**理由5: hostnameによるインフラメトリクス紐付け**
- ログの `hostname` とInfrastructureメトリクスの `hostname` が一致
- エラー発生時のCPU/メモリ状況を自動表示
- サーバーリソース起因のエラーを即座に判別

#### 実際のNRQLクエリ例

New Relic UIが内部で実行しているクエリ:

```sql
-- APM Errorsページで特定のエラーをクリックした時
SELECT * FROM Log 
WHERE trace.id = 'abc123def456'
ORDER BY timestamp ASC
LIMIT 100

-- 結果: APM経由とInfra経由の両方のログが統合表示される
```

```sql
-- 同時刻のInfrastructureメトリクスを取得
SELECT average(cpuPercent), average(memoryUsedPercent)
FROM SystemSample
WHERE hostname = 'ip-10-123-10-95.ap-northeast-1.compute.internal'
AND timestamp BETWEEN 1729692490000 AND 1729692500000
```

#### まとめ: 2つの経路の相互補完

| 機能 | APM経由 | Infrastructure経由 | 統合効果 |
|------|---------|-------------------|----------|
| **エラートレース** | ✅ 完全対応 | ❌ 対応なし | APMでエラー詳細を取得 |
| **systemdログ** | ❌ 取得不可 | ✅ 完全取得 | アプリ起動/停止ログも取得 |
| **リアルタイム性** | ✅ 即時 | ⚠️ 数秒遅延 | エラー検知は即時 |
| **メタデータ** | ✅ trace.id等 | ✅ hostname等 | 両方のメタデータで検索可能 |
| **アプリ停止時** | ❌ 取得不可 | ✅ 取得可能 | クラッシュログも記録 |

**結論**: 2つの経路を組み合わせることで、**エラー発生時の完全なコンテキスト**（アプリログ + インフラログ + メトリクス）を自動的に取得できる

### 設定内容

#### 3.1 newrelic.iniでの有効化

```ini
# Application Logging (Logs in Context)
application_logging.enabled = true
application_logging.forwarding.enabled = true
application_logging.forwarding.max_samples_stored = 10000
application_logging.metrics.enabled = true
application_logging.local_decorating.enabled = true
```

**各設定の意味**:
- `enabled`: ログ機能全体の有効化
- `forwarding.enabled`: ログをNew Relicに**直接転送**（APM経由の転送を有効化）
- `max_samples_stored`: 保存するログサンプル数
- `metrics.enabled`: ログメトリクスの収集
- `local_decorating.enabled`: ログに**NR-LINKINGマーカー**を自動付与（Infrastructure経由でも紐付け可能にする）

---

### NR-LINKINGマーカーとは？

**Q1: NR-LINKINGはアプリコードや設定ファイルに記載が必要？**

A: **いいえ、必要ありません。`application_logging.local_decorating.enabled = true` をnewrelic.iniに設定するだけで、New Relic APMエージェントが自動的にNR-LINKINGマーカーを付与します。**

#### NR-LINKINGの自動生成フロー

```
1. アプリケーションコード
   logger.error("[DB ERROR] Transaction failed")
   ↓ 通常のログ出力（特別なコード不要）

2. New Relic APMエージェントが自動介入
   ↓ local_decorating.enabled = true が有効な場合
   ↓ ログに自動的にNR-LINKINGを追加

3. 標準出力に出力されるログ
   "[DB ERROR] Transaction failed NR-LINKING|abc123|span789|..."
   ↓ アプリコードは何も意識しない

4. systemd journalに記録
   ↓ journalctl -u fastapi-demo で確認可能

5. Fluent BitがNR-LINKINGを検出・抽出
   ↓ trace.idをメタデータ化

6. New Relic Logsに送信
   {"message": "...", "trace.id": "abc123", ...}
```

#### 必要な設定は1行だけ

**newrelic.ini**:
```ini
[newrelic]
application_logging.local_decorating.enabled = true  # ← これだけ！
```

**アプリケーションコード**:
```python
# 通常のログ出力だけでOK（特別なコード不要）
logger.error("Error message")
# ↑ New Relicエージェントが自動的にNR-LINKINGを付与
```

**Infrastructure設定ファイル**:
```yaml
# /etc/newrelic-infra/logging.d/fastapi-demo.yml
logs:
  - name: fastapi-demo-logs
    systemd: fastapi-demo  # ← systemdログを収集するだけ
    # NR-LINKINGに関する設定は不要！
```

**重要**: NR-LINKINGマーカーは**New Relic APMエージェントが自動的に生成**します。アプリケーションコードやInfrastructure設定ファイルに手動で追加する必要はありません。

---

**Q2: NR-LINKINGをつけないと関連付けされないの？**

A: **いいえ、APM経由のログは関連付けされます。NR-LINKINGはInfrastructure経由のログを関連付けるためのものです。**

#### 関連付けの2つのパターン

**パターン1: APM経由のログ（NR-LINKING不要）**
```
Pythonアプリケーション
  ↓ logger.error("Error message")
[APM Agent]
  ↓ 自動的にtrace.idをJSONメタデータとして付与
  ↓ {"message": "...", "trace.id": "abc123", ...}
New Relic Logs
  ↓ trace.idで自動紐付け ✅ 完了
```

**パターン2: Infrastructure経由のログ（NR-LINKING必要）**
```
Pythonアプリケーション
  ↓ logger.error("Error message")
systemd journal (標準出力)
  ↓ テキスト形式: "Error message NR-LINKING|abc123|..."
[Fluent Bit]
  ↓ NR-LINKINGマーカーを検出
  ↓ trace.idを抽出してメタデータ化
  ↓ {"message": "Error message", "trace.id": "abc123", ...}
New Relic Logs
  ↓ trace.idで自動紐付け ✅ 完了
```

#### なぜNR-LINKINGが必要なのか

| 項目 | APM経由 | Infrastructure経由 |
|------|---------|--------------------|
| **データ形式** | JSON（構造化データ） | テキスト（文字列） |
| **trace.idの位置** | JSONフィールドとして明確 | テキスト内に埋め込み |
| **抽出方法** | 自動的にパース可能 | マーカーがないと抽出不可 |
| **NR-LINKING** | 不要 | **必須** |

#### 具体例：同じログの2つの形式

**APM経由（JSON形式）**:
```json
{
  "message": "[DB ERROR] Transaction table access failed",
  "trace.id": "abc123def456",
  "span.id": "span789",
  "entity.guid": "MzY4...",
  "timestamp": 1729692495000
}
```
→ trace.idがJSONフィールドとして明確に存在するため、New Relicが自動的に読み取れる

**Infrastructure経由（テキスト形式）**:
```
2025-10-23 09:48:15 - main - ERROR - [DB ERROR] Transaction table access failed NR-LINKING|abc123def456|span789|ip-10-123-10-95|MzY4...|FastAPI-ECSite||
```
→ trace.idがテキストの一部として埋め込まれているため、`NR-LINKING|`マーカーで位置を特定して抽出する必要がある

#### NR-LINKINGマーカーのフォーマット

```
NR-LINKING|trace_id|span_id|hostname|entity_guid|entity_name||
           │        │       │        │           │
           │        │       │        │           └─ アプリ名
           │        │       │        └────────── エンティティGUID
           │        │       └───────────────── ホスト名
           │        └──────────────────────── スパンID
           └─────────────────────────────── トレースID（最重要）
```

Fluent Bitはこのフォーマットを認識し、各値を抽出してメタデータとしてNew Relicに送信します。

#### まとめ

**Q: `local_decorating.enabled = false` にしたらどうなる？**

A: 
- ✅ **APM経由のログ**: 引き続き関連付けされる（JSONメタデータでtrace.idが付与されるため）
- ❌ **Infrastructure経由のログ**: 関連付けされない（NR-LINKINGマーカーがないため、trace.idを抽出できない）

**結論**: `local_decorating.enabled = true` にすることで、**2つの経路から送信されるログがどちらもtrace.idで紐付けられる**ようになります。これにより、APM Errors画面でエラーをクリックした時に、両方の経路からのログが統合表示されます。

---

#### 3.2 コード内でのカスタム属性追加

```python
# エラー発生時
newrelic.agent.add_custom_attributes({
    'payment.amount': req.amount,
    'payment.storeId': req.storeId,
    'error.type': 'DatabaseError'
})
newrelic.agent.notice_error()
logger.error(f"DB Error - Amount: ¥{req.amount}")
```

**この作業で実現すること**:
- エラーに業務情報を付与
- ログとエラーの詳細な紐付け
- カスタム属性でのフィルタリング
- 原因特定の高速化

---

### カスタム属性とデフォルト属性の違い

#### デフォルトで自動取得される属性（コード不要）

New Relic APMエージェントは以下を**自動的に**記録します：

**トランザクション情報**:
- `request.method`: HTTPメソッド (GET, POST等)
- `request.uri`: リクエストURL
- `response.status`: HTTPステータスコード
- `http.statusCode`: レスポンスコード

**アプリケーション情報**:
- `host.displayName`: ホスト名
- `appName`: アプリケーション名
- `entity.guid`: エンティティGUID

**パフォーマンス情報**:
- `duration`: 処理時間
- `databaseDuration`: DB処理時間
- `externalDuration`: 外部API呼び出し時間

**エラー情報**:
- `error.class`: エラークラス名 (ZeroDivisionError等)
- `error.message`: エラーメッセージ
- `error.expected`: 予期されたエラーか

**データベース情報**:
- `database.statement`: SQLクエリ（難読化済み）
- `database.operation`: 操作タイプ (SELECT, INSERT等)

**例：自動取得されるトランザクション**:
```json
{
  "name": "WebTransaction/Function/main:payment",
  "duration": 0.183,
  "request.method": "POST",
  "request.uri": "/api/payment",
  "response.status": "500",
  "error.class": "ZeroDivisionError",
  "error.message": "division by zero",
  "database.statement": "INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?)",
  "host.displayName": "ip-10-123-10-95"
}
```

#### カスタム属性（コードで明示的に追加）

業務固有の情報を追加する場合に使用：

```python
newrelic.agent.add_custom_attributes({
    'payment.amount': 10000,        # 決済金額
    'payment.storeId': 'STORE001',  # 店舗ID
    'payment.cardLast4': '3456',    # カード下4桁
    'error.type': 'DatabaseError'   # エラー種別
})
```

**カスタム属性の利点**:
- ✅ 業務ロジックに沿った分析が可能
- ✅ 特定の店舗や金額でフィルタリング
- ✅ ビジネスメトリクスの可視化
- ✅ エラーの影響範囲を即座に把握

**New Relic UIでの活用例**:
```sql
-- NRQL（New Relic Query Language）でクエリ
SELECT count(*) FROM Transaction 
WHERE payment.storeId = 'STORE001' 
AND error.class IS NOT NULL
```

#### まとめ：いつカスタム属性を追加すべきか

| 情報 | 自動取得 | カスタム属性が必要 |
|------|----------|--------------------|
| HTTPメソッド/URL | ✅ | - |
| レスポンスコード | ✅ | - |
| エラークラス名 | ✅ | - |
| 処理時間 | ✅ | - |
| SQLクエリ | ✅ | - |
| **決済金額** | ❌ | ✅ 必要 |
| **店舗ID** | ❌ | ✅ 必要 |
| **ユーザーID** | ❌ | ✅ 必要 |
| **エラー種別（業務）** | ❌ | ✅ 必要 |

---

## 4. ブラウザモニタリングとセッションリプレイ設定

### 目的
フロントエンドのユーザー操作を記録し、エラー発生時の状況を再現

### 手順

#### 4.1 New Relic UIでセッションリプレイを有効化

**作業内容**: APM設定画面でセッションリプレイをONにする

**手順**:
1. New Relic UIにログイン
2. **APM & Services** → **FastAPI-ECSite** を選択
3. 左メニューから **Settings** をクリック
4. **Application** セクションを選択
5. **Browser monitoring** セクションまでスクロール
6. **Session replay** トグルを **ON** に切り替え
7. **Save** ボタンをクリック

**この作業で実現すること**:
- ユーザーの画面操作をビデオのように記録
- エラー発生時のユーザー操作を再生
- クリック、スクロール、入力などを記録
- エラーの再現手順を可視化

---

#### 4.2 ブラウザエージェントの追加（実装済み）

**作業内容**: HTMLにBrowser Monitoringスクリプトを追加

```html
<head>
    <script type="text/javascript">
    ;window.NREUM||(NREUM={});NREUM.init={
        session_replay:{
            enabled:true,
            sampling_rate:100.0,
            error_sampling_rate:100.0,
            mask_all_inputs:true
        }
    };
    ;NREUM.loader_config={
        accountID:"3688120",
        applicationID:"1103447806",
        licenseKey:"NRJS-dfb894caf5e1edd9871"
    };
    </script>
    <script src="https://js-agent.newrelic.com/nr-loader-spa-1.298.0.min.js"></script>
</head>
```

**設定の意味**:
- `enabled:true`: セッションリプレイ有効化
- `sampling_rate:100.0`: 全セッションを記録（100%）
- `error_sampling_rate:100.0`: エラー時は必ず記録
- `mask_all_inputs:true`: 入力値をマスク（個人情報保護）

**この作業で実現すること**:
- ブラウザでのユーザー操作を自動記録
- JavaScriptエラーを自動検知
- ページ読み込み時間を記録
- AJAXリクエストを追跡

---

#### 4.3 セッションリプレイの確認方法

**New Relic UIでの確認手順**:

1. **エラーを発生させる**
   - アプリケーションでデモシナリオを実行
   - 例: 「シナリオ1: コードエラー」をONにして決済

2. **Browserでセッションリプレイを確認**
   - New Relic UI: **Browser** → **FastAPI-ECSite**
   - 左メニューから **Session replay** をクリック
   - エラーが発生したセッションを選択
   - 再生ボタンをクリック

3. **確認できる内容**
   - ✅ ユーザーのクリック操作
   - ✅ ページ遷移
   - ✅ フォーム入力（マスク済み）
   - ✅ エラー発生直前の操作
   - ✅ スクロール位置
   - ✅ ボタンクリックのタイミング

**セッションリプレイの価値**:
- **エラー再現手順が明確**: ユーザーが何をしたか一目瞭然
- **バグの再現が容易**: 同じ操作を繰り返して検証
- **UX改善**: ユーザーの迷う箇所を特定
- **調査時間短縮**: ユーザーにヒアリング不要

---

#### 4.4 セッションリプレイとAPMの連携

**統合監視の仕組み**:

```
[ユーザー操作]
    ↓
[Browser Agent] セッション記録開始
    ├─ クリックイベント記録
    ├─ ページ遷移記録
    └─ AJAXリクエスト記録
    ↓
[API呼び出し] /api/payment
    ↓
[APM Agent] トランザクション記録
    ├─ trace.id 生成
    └─ エラー検知
    ↓
[エラー発生]
    ↓
[New Relic Platform]
    ├─ Browser: セッションリプレイ保存
    ├─ APM: エラー詳細保存
    └─ trace.id で自動紐付け
```

**New Relic UIでの確認**:
1. **APM → Errors** でエラーを選択
2. エラー詳細画面に **Session replay** リンクが表示
3. クリックするとエラー発生時のセッションが再生

---

## 5. 動作確認

### 5.1 APM確認

**New Relic UI**: APM & Services → FastAPI-ECSite

**確認項目**:
- ✅ トランザクション一覧が表示される
- ✅ レスポンスタイムが記録されている
- ✅ データベースクエリが表示される
- ✅ 外部サービス呼び出しが記録されている

---

### 4.2 Infrastructure確認

**New Relic UI**: Infrastructure → Hosts

**確認項目**:
- ✅ CPU使用率が表示される
- ✅ メモリ使用量が表示される
- ✅ ディスクI/Oが記録されている
- ✅ ネットワークトラフィックが表示される

---

### 4.3 Logs確認

**New Relic UI**: Logs

**確認項目**:
- ✅ アプリケーションログが表示される
- ✅ `service: FastAPI-ECSite` でフィルタできる
- ✅ ログレベル（INFO/ERROR）が記録されている
- ✅ タイムスタンプが正確

---

### 4.4 Logs in Context確認

**手順**:
1. デモシナリオでエラーを発生させる
2. APM → Errors → エラーを選択
3. **Logs** タブをクリック
4. エラー発生時のログが自動表示される

**確認項目**:
- ✅ APMエラー画面にLogsタブが表示される
- ✅ エラー発生時刻前後のログが表示される
- ✅ カスタム属性（payment.amount等）が表示される
- ✅ ログからAPMトレースへリンクできる

---

## 5. トラブルシューティング

### APMデータが表示されない

**確認事項**:
```bash
# エージェントが起動しているか
ps aux | grep newrelic-admin

# ログにエラーがないか
sudo journalctl -u fastapi-demo -n 50

# 設定ファイルが正しいか
cat ~/fastapi-demo-system/newrelic.ini | grep license_key
```

---

### Infrastructureデータが表示されない

**確認事項**:
```bash
# エージェントが起動しているか
sudo systemctl status newrelic-infra

# ログを確認
sudo journalctl -u newrelic-infra -n 50
```

---

### ログが表示されない

**確認事項**:
```bash
# ログ設定ファイルが存在するか
ls -la /etc/newrelic-infra/logging.d/

# Fluent Bitが起動しているか
ps aux | grep fluent-bit

# アプリケーションがログを出力しているか
sudo journalctl -u fastapi-demo -f
```

---

## 6. まとめ

### 導入した監視機能

| 機能 | 目的 | 確認場所 |
|------|------|----------|
| **APM** | アプリケーション性能監視 | APM & Services |
| **Infrastructure** | サーバーリソース監視 | Infrastructure → Hosts |
| **Logs** | ログ収集・検索 | Logs |
| **Logs in Context** | ログとトレースの紐付け | APM → Errors → Logs |

### 実現できること

✅ **迅速な原因特定**: APMエラーから1クリックでログ確認  
✅ **統合監視**: アプリ・インフラ・ログを一元管理  
✅ **詳細な分析**: カスタム属性で業務情報を記録  
✅ **自動紐付け**: 時間軸でデータを自動関連付け  

### デモURL

- **アプリケーション**: http://43.207.1.222:3000
- **管理画面**: 「管理画面」タブ
- **デモシナリオ**: シナリオ1〜3で各種エラーを再現
