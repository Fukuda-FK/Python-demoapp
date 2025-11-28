# Bedrock Agent向けX-Rayトレーシング設定手順

## 概要
このドキュメントでは、ECSサービス `nrdemo-fastapi-demo-service` のコンテナアプリケーションに、Bedrock Agent呼び出しのトレース情報をAWS X-Rayで記録し、CloudWatch Observabilityで分析できるようにする手順を説明します。

## 前提条件
- AWS CLI設定済み
- Docker環境
- ECRリポジトリへのアクセス権限
- ECSサービスへのデプロイ権限

## 実施済みの設定

### 1. IAMロール権限追加 ✅
```bash
aws iam attach-role-policy \
  --role-name nrdemo-ecs-task-role \
  --policy-arn arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess \
  --region ap-northeast-1
```

### 2. アプリケーションコード更新 ✅
- `requirements.txt`: AWS X-Ray SDK、Boto3を追加
- `main.py`: X-Ray統合、Bedrock Agent呼び出しエンドポイント追加

## デプロイ手順

### ステップ1: Dockerイメージのビルドとプッシュ

```bash
# リポジトリディレクトリに移動
cd Python-demoapp/app

# ECRログイン
aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin 272128256293.dkr.ecr.ap-northeast-1.amazonaws.com

# Dockerイメージをビルド
docker build -t nrdemo-fastapi-demo-app:latest .

# タグ付け
docker tag nrdemo-fastapi-demo-app:latest 272128256293.dkr.ecr.ap-northeast-1.amazonaws.com/nrdemo-fastapi-demo-app:latest

# ECRにプッシュ
docker push 272128256293.dkr.ecr.ap-northeast-1.amazonaws.com/nrdemo-fastapi-demo-app:latest
```

### ステップ2: ECSタスク定義の更新

```bash
# 新しいタスク定義を登録
aws ecs register-task-definition \
  --cli-input-json file://ecs-task-definition-xray.json \
  --region ap-northeast-1
```

### ステップ3: ECSサービスの更新

```bash
# サービスを新しいタスク定義で更新
aws ecs update-service \
  --cluster nrdemo-fastapi-demo-cluster \
  --service nrdemo-fastapi-demo-service \
  --task-definition nrdemo-fastapi-demo-task \
  --force-new-deployment \
  --region ap-northeast-1
```

### ステップ4: デプロイ確認

```bash
# サービスステータス確認
aws ecs describe-services \
  --cluster nrdemo-fastapi-demo-cluster \
  --services nrdemo-fastapi-demo-service \
  --region ap-northeast-1 \
  --query 'services[0].deployments'

# タスクログ確認
aws logs tail /ecs/nrdemo-fastapi-demo-app --follow --region ap-northeast-1
```

## 動作確認

### 1. Bedrock Agent呼び出しテスト

```bash
# アプリケーションのパブリックIPを取得
TASK_ARN=$(aws ecs list-tasks --cluster nrdemo-fastapi-demo-cluster --service-name nrdemo-fastapi-demo-service --region ap-northeast-1 --query 'taskArns[0]' --output text)

PUBLIC_IP=$(aws ecs describe-tasks --cluster nrdemo-fastapi-demo-cluster --tasks $TASK_ARN --region ap-northeast-1 --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' --output text | xargs -I {} aws ec2 describe-network-interfaces --network-interface-ids {} --region ap-northeast-1 --query 'NetworkInterfaces[0].Association.PublicIp' --output text)

# Bedrock Agent呼び出し
curl -X POST http://$PUBLIC_IP:3000/api/bedrock-agent \
  -H "Content-Type: application/json" \
  -d '{"prompt": "テスト用のプロンプト"}'
```

### 2. CloudWatch X-Rayでトレース確認

1. AWSコンソール → CloudWatch → X-Ray traces
2. Service map で `nrdemo-fastapi-demo-service` を確認
3. Traces タブでトレース詳細を確認
4. Bedrock Agent呼び出しのセグメントを確認

### 3. CloudWatch Observabilityでの分析

1. AWSコンソール → CloudWatch → Application Signals
2. Services → `nrdemo-fastapi-demo-service` を選択
3. Traces タブで以下を確認:
   - Bedrock Agent呼び出しのレイテンシ
   - エラー率
   - スループット

## トレース情報の内容

X-Rayトレースには以下の情報が記録されます:

- **サービス名**: nrdemo-fastapi-demo-service
- **Bedrock Agent ID**: 環境変数から取得
- **プロンプト内容**: リクエストのプロンプト
- **レスポンス長**: Bedrock Agentからのレスポンスサイズ
- **実行時間**: 各セグメントの処理時間
- **エラー情報**: 例外発生時のスタックトレース

## トラブルシューティング

### X-Rayトレースが表示されない場合

1. **X-Rayデーモンコンテナの確認**
```bash
aws logs tail /ecs/nrdemo-fastapi-demo-app --filter-pattern "xray" --region ap-northeast-1
```

2. **IAM権限の確認**
```bash
aws iam list-attached-role-policies --role-name nrdemo-ecs-task-role --region ap-northeast-1
```

3. **環境変数の確認**
```bash
aws ecs describe-task-definition --task-definition nrdemo-fastapi-demo-task --region ap-northeast-1 --query 'taskDefinition.containerDefinitions[?name==`nrdemo-fastapi-demo-container`].environment'
```

### Bedrock Agent呼び出しエラー

1. **Bedrock権限の確認**
   - タスクロールに `bedrock:InvokeAgent` 権限があることを確認

2. **Agent IDの確認**
   - 環境変数 `BEDROCK_AGENT_ID` と `BEDROCK_AGENT_ALIAS_ID` が正しく設定されているか確認

## 参考リンク

- [AWS X-Ray Developer Guide](https://docs.aws.amazon.com/xray/latest/devguide/)
- [Amazon Bedrock Agent Runtime API](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_Operations_Agents_for_Amazon_Bedrock_Runtime.html)
- [CloudWatch Application Signals](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Application-Signals.html)
