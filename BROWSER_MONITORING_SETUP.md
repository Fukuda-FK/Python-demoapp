# New Relic ブラウザモニタリング & セッションリプレイ設定ガイド

## セッションリプレイとは

ユーザーのブラウザ操作を録画し、エラー発生時の状況を再現できる機能です。

### 実現できること

- 🎥 **ユーザー操作の録画**: クリック、スクロール、入力を記録
- 🐛 **エラー再現**: エラー発生時の操作手順を可視化
- 📊 **UX改善**: ユーザーが迷う箇所を特定
- ⏱️ **調査時間短縮**: ユーザーヒアリング不要

---

## セットアップ手順

### ステップ1: New Relic UIでセッションリプレイを有効化

**重要**: この設定は**New Relic UI上**で行います（コード変更不要）

#### 手順

1. **New Relic UIにログイン**
   - https://one.newrelic.com/

2. **APM設定画面を開く**
   - **APM & Services** → **FastAPI-ECSite** を選択
   - 左メニューから **Settings** をクリック

3. **Application設定を開く**
   - **Application** セクションを選択

4. **Browser monitoring設定を探す**
   - ページを下にスクロール
   - **Browser monitoring** セクションを見つける

5. **Session replayを有効化**
   - **Session replay** トグルを **ON** に切り替え
   - **Save** ボタンをクリック

#### 設定画面の場所

```
New Relic UI
  └─ APM & Services
      └─ FastAPI-ECSite
          └─ Settings (左メニュー)
              └─ Application
                  └─ Browser monitoring
                      └─ Session replay [トグル]
```

---

### ステップ2: ブラウザエージェントの確認（実装済み）

HTMLに以下のスクリプトが含まれていることを確認：

```html
<head>
    <script type="text/javascript">
    ;window.NREUM||(NREUM={});
    NREUM.init={
        session_replay:{
            enabled:true,
            sampling_rate:100.0,
            error_sampling_rate:100.0,
            mask_all_inputs:true
        }
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

---

## セッションリプレイの確認方法

### デモシナリオでテスト

#### 1. エラーを発生させる

1. http://43.207.1.222:3000 にアクセス
2. 「🔧 管理画面」タブを開く
3. 「🐛 シナリオ1: コードエラー」をON
4. 商品をカートに入れて決済実行
5. エラーが発生

#### 2. New Relic UIで確認

**方法A: Browserから確認**

1. New Relic UI: **Browser** → **FastAPI-ECSite**
2. 左メニューから **Session replay** をクリック
3. エラーが発生したセッションを選択
4. 再生ボタンをクリック

**方法B: APMから確認**

1. New Relic UI: **APM & Services** → **FastAPI-ECSite**
2. **Errors** タブを開く
3. エラーを選択
4. エラー詳細画面に **Session replay** リンクが表示
5. クリックしてセッション再生

---

## セッションリプレイで確認できる内容

### 記録される情報

✅ **ユーザー操作**
- クリックイベント
- スクロール位置
- ページ遷移
- ボタン押下

✅ **フォーム入力**
- 入力フィールドの操作（値はマスク）
- フォーカス移動
- 送信タイミング

✅ **エラー情報**
- JavaScriptエラー発生タイミング
- エラー発生直前の操作
- エラーメッセージ

✅ **パフォーマンス**
- ページ読み込み時間
- AJAX呼び出し
- レスポンス待機時間

### 記録されない情報（プライバシー保護）

❌ 入力値の実際の内容（マスク済み）
❌ パスワード
❌ クレジットカード番号
❌ 個人情報

---

## APMとの連携

### 統合監視の仕組み

```
[ユーザー操作]
    ↓
[Browser Agent]
    ├─ セッション記録開始
    ├─ trace.id 生成
    └─ ユーザー操作を記録
    ↓
[API呼び出し] /api/payment
    ↓
[APM Agent]
    ├─ 同じ trace.id を使用
    ├─ トランザクション記録
    └─ エラー検知
    ↓
[エラー発生]
    ↓
[New Relic Platform]
    ├─ Browser: セッションリプレイ保存
    ├─ APM: エラー詳細保存
    └─ trace.id で自動紐付け
```

### New Relic UIでの確認フロー

1. **APM → Errors** でエラーを確認
2. エラー詳細に **Session replay** リンク表示
3. クリックでセッション再生
4. エラー発生までの操作を確認
5. **Logs** タブでサーバーログも確認
6. **Infrastructure** でサーバーリソースも確認

**結果**: フロントエンド → バックエンド → インフラの全レイヤーを統合確認

---

## トラブルシューティング

### セッションリプレイが表示されない

**確認事項**:

1. **New Relic UIで有効化されているか**
   ```
   APM → Settings → Application → Browser monitoring → Session replay [ON]
   ```

2. **ブラウザエージェントが読み込まれているか**
   - ブラウザの開発者ツールを開く
   - Console タブで `window.NREUM` を確認
   - オブジェクトが表示されればOK

3. **エラーが発生しているか**
   - セッションリプレイはエラー発生時に優先的に記録
   - `error_sampling_rate:100.0` で全エラーを記録

4. **データ反映を待つ**
   - セッションリプレイは数分後に表示
   - 最大5分程度待つ

---

## デモシナリオ別の確認ポイント

### シナリオ1: コードエラー

**セッションリプレイで確認**:
- ユーザーが「決済を実行」ボタンをクリック
- エラーメッセージが表示されるまでの流れ
- エラー発生タイミング

**APMで確認**:
- ZeroDivisionError のスタックトレース
- エラー発生箇所（main.py の行番号）

**統合確認**:
- セッションリプレイ → APMエラー → Logs → Infrastructure

---

### シナリオ2: DBエラー

**セッションリプレイで確認**:
- 決済ボタンクリック
- ローディング表示
- エラーメッセージ表示

**APMで確認**:
- 失敗したSQLクエリ
- データベース接続エラー

---

### シナリオ3: リソース不足

**セッションリプレイで確認**:
- 決済ボタンクリック
- 長時間のローディング（5秒）
- 最終的に成功または失敗

**Infrastructureで確認**:
- メモリ使用率の急上昇
- CPU使用率の増加

---

## まとめ

### セッションリプレイの価値

| Before（従来） | After（セッションリプレイ） |
|---------------|------------------------|
| ユーザーにヒアリング | 操作を録画で確認 |
| 再現手順が不明確 | 正確な操作手順を把握 |
| エラー調査に時間がかかる | 即座に原因特定 |
| フロントとバックを別々に調査 | 統合して確認 |

### 設定完了チェックリスト

- ✅ New Relic UIでSession replay ON
- ✅ HTMLにブラウザエージェント追加済み
- ✅ デモシナリオでエラー発生
- ✅ Browser → Session replayで再生確認
- ✅ APM → Errorsからリンク確認

### アクセス

- **アプリケーション**: http://43.207.1.222:3000
- **New Relic Browser**: Browser → FastAPI-ECSite → Session replay
- **New Relic APM**: APM & Services → FastAPI-ECSite → Errors
