# New Relic デモシナリオ

## 課題：障害発生時の原因特定を迅速化したい

従来の課題：
- アプリとインフラのログを時間ごとに突き合わせる作業に時間がかかる
- 原因がコード、DB、サーバーリソースのどれか切り分けが困難

## New Relicで解決できること

### 統合監視による迅速な原因特定
- **APM**: アプリケーションのエラーとスタックトレース
- **Logs in Context**: ログとトレースの自動紐付け
- **Infrastructure**: サーバーリソースの監視

## デモシナリオ

### シナリオ1: コードエラー 🐛

**発生するエラー**: ZeroDivisionError (ゼロ除算エラー)

**手順**:
1. 管理画面で「シナリオ1: コードエラー」をON
2. 商品をカートに入れて決済実行
3. エラー発生

**New Relicで確認**:
- **APM → Errors**: エラー詳細とスタックトレース
- **コードの何行目**でエラーが発生したか即座に判明
- **Logs in Context**: エラー発生時のログを自動で紐付け

**ログ出力**:
```
ERROR [CODE ERROR] Division by zero in payment calculation - Amount: ¥89800
```

---

### シナリオ2: DBエラー 💾

**発生するエラー**: PostgreSQL - relation "non_existent_table" does not exist

**手順**:
1. 管理画面で「シナリオ2: DBエラー」をON
2. 商品をカートに入れて決済実行
3. DBエラー発生

**New Relicで確認**:
- **APM → Databases**: 失敗したSQLクエリ
- **Logs in Context**: DBエラーログとトレースの紐付け
- **エラーメッセージ**: 存在しないテーブルへのアクセス

**ログ出力**:
```
ERROR [DB ERROR] Invalid SQL query - Amount: ¥89800
```

---

### シナリオ3: リソース不足 📊

**発生する問題**: メモリ使用量増加 + CPU負荷

**手順**:
1. 管理画面で「シナリオ3: リソース不足」をON
2. 商品をカートに入れて決済実行
3. 処理が遅延（5秒）

**New Relicで確認**:
- **Infrastructure → Hosts**: メモリ使用率の急上昇
- **APM → Transactions**: レスポンスタイムの増加
- **原因切り分け**: コードやDBではなくリソース問題と判明

**ログ出力**:
```
WARNING [RESOURCE] High memory usage detected - Amount: ¥89800
```

---

## デモの流れ

### 準備
1. http://43.207.1.222:3000 にアクセス
2. New Relic UIを別タブで開く

### 実演手順

#### 1. 正常動作の確認
- 商品を購入して正常に決済完了
- New Relic APMでトランザクション確認

#### 2. シナリオ1実行
- 「シナリオ1: コードエラー」ON
- 決済実行 → エラー発生
- **New Relic APM**: スタックトレースで`main.py`の該当行を確認
- **Logs**: エラーログを確認

#### 3. シナリオ2実行
- 「全て正常化」→「シナリオ2: DBエラー」ON
- 決済実行 → DBエラー発生
- **New Relic APM → Databases**: 失敗したクエリ確認
- **Logs in Context**: DBエラーログとトレースの紐付け確認

#### 4. シナリオ3実行
- 「全て正常化」→「シナリオ3: リソース不足」ON
- 決済実行 → 処理遅延
- **New Relic Infrastructure**: メモリ使用率の上昇確認
- **APM**: レスポンスタイムの増加確認

## New Relicの価値

### Before (従来)
❌ ログファイルを手動で検索
❌ アプリとインフラのログを時間で突き合わせ
❌ 原因特定に数時間かかる

### After (New Relic)
✅ APMでエラー箇所を即座に特定
✅ Logs in Contextで自動紐付け
✅ Infrastructure監視でリソース問題も把握
✅ **原因特定が数分に短縮**

## アクセス

- **アプリケーション**: http://43.207.1.222:3000
- **管理画面**: 「🔧 管理画面」タブ
- **New Relic UI**: APM & Services → FastAPI-ECSite
