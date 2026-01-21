import os
import httpx
from llama_index.core import (
    VectorStoreIndex, 
    SimpleDirectoryReader, 
    StorageContext, 
    load_index_from_storage,
    Settings
)
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

# 1. オンプレミス用のHTTPクライアント設定 (verify=Falseなど)
http_client = httpx.Client(
    verify=False,  # 証明書検証を無効化
    # proxy="http://your-proxy:8080" # 必要ならプロキシも設定可能
)

# 2. LlamaIndexのグローバル設定を更新
# base_url を指定することで、OpenAI本家ではなく自社サーバーへ飛ばします
Settings.llm = OpenAI(
    model="gpt-4", # 自社サーバーのモデル名に合わせる
    api_base="https://your-onpre-server.com/v1", 
    api_key="your-key",
    http_client=http_client
)

# 埋め込みモデル（ベクトル化）も同様に設定
Settings.embed_model = OpenAIEmbedding(
    api_base="https://your-onpre-server.com/v1",
    api_key="your-key",
    http_client=http_client
)

PERSIST_DIR = "./storage"

def get_index():
    if not os.path.exists(PERSIST_DIR):
        print("インデックスを作成中...")
        # 初回作成
        documents = SimpleDirectoryReader("./data").load_data()
        index = VectorStoreIndex.from_documents(documents)
        # ディスクに保存
        index.storage_context.persist(persist_dir=PERSIST_DIR)
    else:
        print("保存されたインデックスを読み込み中...")
        # 保存済みデータの読み込み
        storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
        index = load_index_from_storage(storage_context)
    return index

# 実行
index = get_index()
chat_engine = index.as_chat_engine()
response = chat_engine.chat("この資料の要約を教えて")
print(response)
