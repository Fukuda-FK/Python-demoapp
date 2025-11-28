from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import asyncpg
import os
import time
import random
import httpx
import asyncio
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import newrelic.agent
import boto3
from aws_xray_sdk.core import xray_recorder, patch_all

# X-Rayの設定
xray_recorder.configure(
    service='nrdemo-fastapi-demo-service',
    context_missing='LOG_ERROR'
)
patch_all()  # boto3, httpx等を自動的にトレース

# New Relic Logs in Context設定
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()

try:
    from newrelic.agent import NewRelicContextFormatter
    formatter = NewRelicContextFormatter()
except ImportError:
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

handler.setFormatter(formatter)
logger.addHandler(handler)

load_dotenv()

failure_mode = False
slow_mode = False
backend_only_failure_mode = False
db_error_mode = False
code_error_mode = False
resource_error_mode = False
db_pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool
    
    # First, try to create the database if it doesn't exist
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = int(os.getenv("DB_PORT", "5432"))
    db_name = os.getenv("DB_NAME", "payment_demo")
    db_user = os.getenv("DB_USER", "dbadmin")
    db_password = os.getenv("DB_PASSWORD", "DemoPassword123!")
    
    try:
        # Connect to postgres database to create our database
        conn = await asyncpg.connect(
            host=db_host,
            port=db_port,
            database="postgres",
            user=db_user,
            password=db_password
        )
        # Check if database exists
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", db_name
        )
        if not exists:
            await conn.execute(f'CREATE DATABASE {db_name}')
            logger.info(f"Database {db_name} created successfully")
        await conn.close()
    except Exception as e:
        logger.warning(f"Database creation check failed: {e}")
    
    # Now connect to the application database
    db_pool = await asyncpg.create_pool(
        host=db_host,
        port=db_port,
        database=db_name,
        user=db_user,
        password=db_password,
        min_size=1,
        max_size=10
    )
    await init_database()
    print("========================================")
    print("  FastAPI ワークロード デモシステム")
    print("========================================")
    yield
    await db_pool.close()

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")

class PaymentRequest(BaseModel):
    amount: float
    cardNumber: Optional[str] = None
    storeId: str = "STORE001"

class AdminRequest(BaseModel):
    enable: bool

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": time.time()}

@app.post("/api/payment")
async def payment(req: PaymentRequest):
    start_time = time.time()
    logger.info(f"Payment attempt: ¥{req.amount} at {req.storeId} [Failure: {failure_mode}, Slow: {slow_mode}]")
    
    # New Relic カスタム属性追加
    newrelic.agent.add_custom_attributes([
        ('payment.amount', req.amount),
        ('payment.storeId', req.storeId),
        ('payment.cardLast4', req.cardNumber[-4:] if req.cardNumber else 'N/A')
    ])
    
    # デモシナリオ1: コードエラー
    if code_error_mode:
        logger.error(f"[CODE ERROR] Division by zero in payment calculation - Amount: ¥{req.amount}, Store: {req.storeId}")
        newrelic.agent.add_custom_attributes([('error.scenario', 'code_error'), ('error.severity', 'critical')])
        try:
            result = req.amount / 0
        except ZeroDivisionError as e:
            newrelic.agent.notice_error()
            raise HTTPException(status_code=500, detail={
                "error": "ArithmeticError",
                "message": "決済金額の計算処理中に算術エラーが発生しました",
                "errorCode": "PAYMENT_CALCULATION_ERROR",
                "errorClass": "ZeroDivisionError"
            })
    
    # デモシナリオ2: DBエラー
    if db_error_mode:
        logger.error(f"[DB ERROR] Transaction table access failed - Amount: ¥{req.amount}, Store: {req.storeId}")
        newrelic.agent.add_custom_attributes([('error.scenario', 'database_error'), ('error.severity', 'high'), ('error.table', 'transactions')])
        try:
            async with db_pool.acquire() as conn:
                await conn.execute("SELECT * FROM non_existent_table")
        except Exception as e:
            newrelic.agent.notice_error()
            raise HTTPException(status_code=500, detail={
                "error": "DatabaseConnectionError",
                "message": "トランザクションテーブルへのアクセス中にデータベースエラーが発生しました",
                "errorCode": "DB_TABLE_ACCESS_ERROR",
                "errorClass": "PostgresError"
            })
    
    # デモシナリオ3: リソース不足
    if resource_error_mode:
        logger.error(f"[RESOURCE] Memory allocation failed - Amount: ¥{req.amount}, Store: {req.storeId}")
        newrelic.agent.add_custom_attributes([('error.scenario', 'resource_exhaustion'), ('error.severity', 'critical'), ('resource.type', 'memory'), ('resource.requested_mb', 100)])
        newrelic.agent.record_custom_event('ResourceWarning', {'type': 'MemoryExhaustion', 'amount': req.amount})
        try:
            data = [0] * (100 * 1024 * 1024)
            await asyncio.sleep(5)
        except MemoryError as e:
            newrelic.agent.notice_error()
            raise HTTPException(status_code=503, detail={
                "error": "ResourceExhaustedError",
                "message": "サーバーリソース不足により決済処理を完了できませんでした",
                "errorCode": "MEMORY_ALLOCATION_ERROR",
                "errorClass": "MemoryError"
            })
    
    if backend_only_failure_mode:
        logger.error(f"[BACKEND ONLY] Internal processing error - Amount: ¥{req.amount}, Store: {req.storeId}")
        newrelic.agent.add_custom_attributes([('error.scenario', 'backend_only'), ('error.severity', 'high'), ('error.visibility', 'backend_only')])
        newrelic.agent.notice_error()
        raise HTTPException(status_code=500, detail={
            "error": "InternalProcessingError",
            "message": "決済処理中に内部エラーが発生しました（バックエンドのみ検知）",
            "errorCode": "INTERNAL_PROCESSING_ERROR",
            "errorClass": "BackendProcessingException",
            "backendOnly": True
        })
    
    if failure_mode:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                await client.get("https://httpstat.us/524?sleep=3000")
        except Exception as e:
            logger.error(f"[FAILURE MODE] Payment gateway timeout - Amount: ¥{req.amount}, Store: {req.storeId}, Error: {str(e)}")
            newrelic.agent.add_custom_attributes([
                ('error.scenario', 'external_timeout'),
                ('error.severity', 'high'),
                ('external.service', 'payment_gateway'),
                ('external.endpoint', 'httpstat.us'),
                ('external.timeout_seconds', 3)
            ])
            newrelic.agent.notice_error()
            raise HTTPException(status_code=504, detail={
                "error": "GatewayTimeoutError",
                "errorCode": "EXTERNAL_GATEWAY_TIMEOUT",
                "errorClass": "TimeoutException",
                "service": "External Payment Gateway",
                "message": "外部決済ゲートウェイとの通信がタイムアウトしました（3秒）"
            })
    
    if req.amount <= 0:
        raise HTTPException(status_code=400, detail={"error": "Invalid amount", "message": "決済金額が無効です"})
    
    await simulate_payment_gateway(req.amount)
    transaction_id = await save_transaction(req.amount, req.cardNumber, req.storeId)
    
    processing_time = int((time.time() - start_time) * 1000)
    logger.info(f"Payment successful: {transaction_id} ({processing_time}ms), Store: {req.storeId}")
    newrelic.agent.add_custom_attributes([
        ('transaction.id', transaction_id),
        ('transaction.processingTime', processing_time)
    ])
    
    return {
        "success": True,
        "transactionId": transaction_id,
        "amount": req.amount,
        "storeId": req.storeId,
        "processingTime": processing_time
    }

@app.get("/api/transactions")
async def get_transactions():
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM transactions ORDER BY created_at DESC LIMIT 50")
        return {"transactions": [dict(row) for row in rows]}

@app.delete("/api/transactions/clear")
async def clear_transactions():
    try:
        async with db_pool.acquire() as conn:
            result = await conn.execute("DELETE FROM transactions")
            deleted_count = int(result.split()[-1])
            return {"success": True, "deleted": deleted_count, "message": "全トランザクションを削除しました"}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})

@app.get("/api/db-test")
async def db_test():
    try:
        async with db_pool.acquire() as conn:
            result = await conn.fetchrow("SELECT NOW() as current_time, version() as db_version")
            count = await conn.fetchval("SELECT COUNT(*) FROM transactions")
            return {
                "status": "connected",
                "currentTime": result["current_time"],
                "dbVersion": result["db_version"],
                "totalTransactions": count,
                "connectionInfo": {
                    "host": os.getenv("DB_HOST"),
                    "database": os.getenv("DB_NAME"),
                    "user": os.getenv("DB_USER")
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail={"status": "error", "error": str(e)})

@app.post("/admin/failure")
async def admin_failure(req: AdminRequest):
    global failure_mode
    failure_mode = req.enable
    print(f"Failure mode {'enabled' if failure_mode else 'disabled'}")
    return {"failureMode": failure_mode, "message": f"決済エラーモードが{'有効' if failure_mode else '無効'}になりました"}

@app.post("/admin/slow")
async def admin_slow(req: AdminRequest):
    global slow_mode
    slow_mode = req.enable
    return {"slowMode": slow_mode, "message": f"Slow mode {'enabled' if slow_mode else 'disabled'}"}

@app.post("/admin/backend-only-failure")
async def admin_backend_only_failure(req: AdminRequest):
    global backend_only_failure_mode
    backend_only_failure_mode = req.enable
    return {"backendOnlyFailureMode": backend_only_failure_mode, "message": f"バックエンドのみエラーモードが{'有効' if backend_only_failure_mode else '無効'}になりました"}

@app.post("/admin/code-error")
async def admin_code_error(req: AdminRequest):
    global code_error_mode
    code_error_mode = req.enable
    logger.info(f"Code error mode {'enabled' if code_error_mode else 'disabled'}")
    return {"codeErrorMode": code_error_mode, "message": f"コードエラーモードが{'有効' if code_error_mode else '無効'}になりました"}

@app.post("/admin/db-error")
async def admin_db_error(req: AdminRequest):
    global db_error_mode
    db_error_mode = req.enable
    logger.info(f"DB error mode {'enabled' if db_error_mode else 'disabled'}")
    return {"dbErrorMode": db_error_mode, "message": f"DBエラーモードが{'有効' if db_error_mode else '無効'}になりました"}

@app.post("/admin/resource-error")
async def admin_resource_error(req: AdminRequest):
    global resource_error_mode
    resource_error_mode = req.enable
    logger.info(f"Resource error mode {'enabled' if resource_error_mode else 'disabled'}")
    return {"resourceErrorMode": resource_error_mode, "message": f"リソースエラーモードが{'有効' if resource_error_mode else '無効'}になりました"}

@app.get("/admin/status")
async def admin_status():
    db_status = "connected"
    transaction_count = 0
    try:
        async with db_pool.acquire() as conn:
            transaction_count = await conn.fetchval("SELECT COUNT(*) FROM transactions")
    except:
        db_status = "disconnected"
    
    return {
        "failureMode": failure_mode,
        "slowMode": slow_mode,
        "codeErrorMode": code_error_mode,
        "dbErrorMode": db_error_mode,
        "resourceErrorMode": resource_error_mode,
        "database": db_status,
        "transactionCount": transaction_count,
        "uptime": time.process_time()
    }

@app.post("/api/bedrock-agent")
async def invoke_bedrock_agent(request: dict):
    """Bedrock Agentを呼び出してトレース情報を記録"""
    agent_id = os.getenv("BEDROCK_AGENT_ID")
    agent_alias_id = os.getenv("BEDROCK_AGENT_ALIAS_ID")
    region = os.getenv("BEDROCK_REGION", "ap-northeast-1")
    
    if not agent_id or not agent_alias_id:
        raise HTTPException(status_code=500, detail="Bedrock Agentが設定されていません")
    
    # X-Rayセグメントを作成
    segment = xray_recorder.begin_segment('bedrock-agent-invocation')
    
    try:
        bedrock_client = boto3.client('bedrock-agent-runtime', region_name=region)
        
        # Bedrock Agent呼び出し
        response = bedrock_client.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=f"session-{int(time.time())}",
            inputText=request.get("prompt", "デフォルトプロンプト")
        )
        
        # レスポンスを処理
        result_text = ""
        for event in response.get('completion', []):
            if 'chunk' in event:
                result_text += event['chunk'].get('bytes', b'').decode('utf-8')
        
        # X-Rayにカスタムメタデータを追加
        segment.put_metadata('agent_id', agent_id)
        segment.put_metadata('prompt', request.get("prompt", ""))
        segment.put_metadata('response_length', len(result_text))
        
        # New Relicにも記録
        newrelic.agent.add_custom_attributes([
            ('bedrock.agent_id', agent_id),
            ('bedrock.prompt_length', len(request.get("prompt", ""))),
            ('bedrock.response_length', len(result_text))
        ])
        
        logger.info(f"Bedrock Agent invoked: {agent_id}, Response length: {len(result_text)}")
        
        return {
            "success": True,
            "agentId": agent_id,
            "response": result_text,
            "responseLength": len(result_text)
        }
        
    except Exception as e:
        logger.error(f"Bedrock Agent error: {str(e)}")
        segment.put_metadata('error', str(e))
        newrelic.agent.notice_error()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        xray_recorder.end_segment()

async def simulate_payment_gateway(amount: float):
    delay = random.uniform(0.1, 0.5)
    if slow_mode:
        delay += 1.5
    await asyncio.sleep(delay)
    
    error_rate = 1.0 if failure_mode else 0.05
    if random.random() < error_rate:
        raise Exception("External payment gateway timeout")

async def save_transaction(amount: float, card_number: Optional[str], store_id: str):
    transaction_id = f"TXN{int(time.time() * 1000)}{random.randint(0, 999)}"
    masked_card = f"****{card_number[-4:]}" if card_number else "****0000"
    
    try:
        async with db_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO transactions (transaction_id, amount, card_number, store_id, status, created_at) VALUES ($1, $2, $3, $4, $5, NOW())",
                transaction_id, amount, masked_card, store_id, "completed"
            )
    except Exception as e:
        logger.error(f"Database insert error: {e}, TransactionID: {transaction_id}")
        newrelic.agent.notice_error()
    
    return transaction_id

async def init_database():
    try:
        async with db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id SERIAL PRIMARY KEY,
                    transaction_id VARCHAR(50) UNIQUE NOT NULL,
                    amount DECIMAL(10, 2) NOT NULL,
                    card_number VARCHAR(20),
                    store_id VARCHAR(20),
                    status VARCHAR(20),
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
