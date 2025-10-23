# New Relic Logs in Context 設定完了

## 実装内容

### 1. Application Logging有効化

**newrelic.ini設定**:
```ini
application_logging.enabled = true
application_logging.forwarding.enabled = true
application_logging.forwarding.max_samples_stored = 10000
application_logging.metrics.enabled = true
application_logging.local_decorating.enabled = true
```

### 2. カスタム属性の追加

各エラーシナリオで以下の情報を自動付与:

**シナリオ1: コードエラー**
```python
newrelic.agent.add_custom_attributes({
    'payment.amount': req.amount,
    'payment.storeId': req.storeId,
    'payment.cardLast4': req.cardNumber[-4:]
})
newrelic.agent.notice_error()
```

**シナリオ2: DBエラー**
```python
newrelic.agent.add_custom_attributes({
    'error.type': 'DatabaseError',
    'error.table': 'non_existent_table'
})
```

**シナリオ3: リソース不足**
```python
newrelic.agent.add_custom_attributes({
    'resource.type': 'MemoryPressure',
    'resource.allocated_mb': 100
})
newrelic.agent.record_custom_event('ResourceWarning', {
    'type': 'HighMemory',
    'amount': req.amount
})
```

### 3. 構造化ログ

すべてのログに以下の情報を含む:
- タイムスタンプ
- ログレベル (INFO/ERROR/WARNING)
- 決済金額
- 店舗ID
- エラータイプ

## New Relic UIでの確認方法

### APMからログへ
1. **APM & Services** → **FastAPI-ECSite**
2. **Errors** タブでエラーを選択
3. エラー詳細画面で **Logs** タブをクリック
4. エラー発生時のログが自動表示される

### Logsからトレースへ
1. **Logs** → ログ検索
2. エラーログを選択
3. **See logs in context** をクリック
4. 関連するAPMトレースが表示される

### 統合ビュー
- **エラー発生時刻**でAPM、Logs、Infrastructureが自動紐付け
- タイムライン上で全レイヤーの状態を確認可能

## デモシナリオでの確認

### シナリオ1実行後
1. APM → Errors → ZeroDivisionError
2. Logs in Context で以下を確認:
   - `[CODE ERROR] Division by zero`
   - `payment.amount: 10000`
   - `payment.storeId: STORE001`

### シナリオ2実行後
1. APM → Errors → UndefinedTableError
2. Logs in Context で以下を確認:
   - `[DB ERROR] Invalid SQL query`
   - `error.type: DatabaseError`
   - `error.table: non_existent_table`

### シナリオ3実行後
1. APM → Transactions (遅延確認)
2. Logs で以下を確認:
   - `[RESOURCE] High memory usage detected`
   - `resource.type: MemoryPressure`
3. Infrastructure → Hosts でメモリ使用率上昇確認

## 実現できること

✅ **APMエラー画面からログへ直接アクセス**
- エラー詳細 → Logsタブ → 関連ログ表示

✅ **ログからAPMトレースへ直接アクセス**
- ログ検索 → See logs in context → APMトレース表示

✅ **カスタム属性でフィルタリング**
- `payment.storeId: STORE001` でフィルタ
- `error.type: DatabaseError` でフィルタ

✅ **タイムライン統合**
- エラー発生時刻でAPM + Logs + Infrastructure統合表示

## テスト方法

```bash
# シナリオ1: コードエラー
curl -X POST http://43.207.1.222:3000/admin/code-error \
  -H "Content-Type: application/json" \
  -d '{"enable": true}'

curl -X POST http://43.207.1.222:3000/api/payment \
  -H "Content-Type: application/json" \
  -d '{"amount": 10000, "cardNumber": "1234567890123456", "storeId": "STORE001"}'

# New Relic UIで確認
# APM → Errors → ZeroDivisionError → Logs タブ
```

## 価値

**Before**: ログファイルとAPMを別々に確認、時間で突き合わせ
**After**: APMエラー画面から1クリックで関連ログ表示、原因特定が数分に短縮
