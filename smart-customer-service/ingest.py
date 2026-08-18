"""
将 data/ 目录下的文档读取、切片、向量化，写入 Milvus
使用 pymilvus MilvusClient 原生API写入（稳定），检索时可用 langchain-milvus
运行前提：Milvus 服务已启动（localhost:19530）
"""
import os
import time
import json
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import DashScopeEmbeddings
from pymilvus import MilvusClient, DataType
from dotenv import load_dotenv

load_dotenv()

# Milvus 连接参数
MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"
COLLECTION_NAME = "product_knowledge"
EMBEDDING_DIM = 1024  # text-embedding-v4 的维度


def get_milvus_client(max_retries=10, retry_interval=3):
    """获取 MilvusClient，带重试机制"""
    uri = f"http://{MILVUS_HOST}:{MILVUS_PORT}"
    for attempt in range(1, max_retries + 1):
        try:
            client = MilvusClient(uri=uri, timeout=10)
            # 验证连接
            client.list_collections()
            print(f" Milvus 连接成功！")
            return client
        except Exception as e:
            print(f" 第{attempt}次连接失败: {e}")
            if attempt < max_retries:
                print(f"   {retry_interval}秒后重试...")
                time.sleep(retry_interval)
    return None


def create_collection(client):
    """创建集合（如果不存在）"""
    # 先删除旧集合
    if client.has_collection(COLLECTION_NAME):
        client.drop_collection(COLLECTION_NAME)
        print(f"   已删除旧的 {COLLECTION_NAME} 集合")

    # 创建新集合 - 使用自动schema
    client.create_collection(
        collection_name=COLLECTION_NAME,
        dimension=EMBEDDING_DIM,
        metric_type="COSINE",
        auto_id=True,
    )
    print(f"   集合 {COLLECTION_NAME} 创建成功（维度={EMBEDDING_DIM}，度量=COSINE）")


def embed_texts(texts, embed_fn, batch_size=10):
    """批量向量化文本"""
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        print(f"   向量化第 {i+1}-{min(i+batch_size, len(texts))} 条...")
        embeddings = embed_fn.embed_documents(batch)
        all_embeddings.extend(embeddings)
    return all_embeddings


def ingest_documents():
    # ========== 0. 连接 Milvus ==========
    print(" 正在连接 Milvus...")
    client = get_milvus_client()
    if client is None:
        print(" 无法连接 Milvus，请确认服务已启动！")
        print("   提示：运行 docker-compose up -d 启动 Milvus")
        return

    # ========== 1. 加载文档 ==========
    print("\n 正在加载文档...")
    loader = DirectoryLoader(
        path="./data",
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    docs = loader.load()
    print(f"   加载了 {len(docs)} 个文档")

    # ========== 2. 切片 ==========
    print(" 正在切片...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50,
        separators=["\n## ", "\n### ", "\n\n", "\n", "。", "，", " "],
    )
    chunks = text_splitter.split_documents(docs)
    print(f"   切片为 {len(chunks)} 个文本块")

    # ========== 3. 创建集合 ==========
    print("\n 正在创建 Milvus 集合...")
    create_collection(client)

    # ========== 4. 向量化 ==========
    print("\n 正在向量化文本...")
    embed_fn = DashScopeEmbeddings(model="text-embedding-v4")
    texts = [chunk.page_content for chunk in chunks]
    metadatas = [chunk.metadata for chunk in chunks]
    embeddings = embed_texts(texts, embed_fn)

    # ========== 5. 写入 Milvus ==========
    print("\n 正在写入 Milvus...")
    data = []
    for i, (text, embedding, metadata) in enumerate(zip(texts, embeddings, metadatas)):
        data.append({
            "text": text,
            "vector": embedding,
            "source": metadata.get("source", ""),
        })

    client.insert(collection_name=COLLECTION_NAME, data=data)
    print(f" 入库完成！共写入 {len(data)} 个文本块")

    # ========== 6. 验证 ==========
    print("\n 验证检索效果...")
    query = "学习机怎么退货"
    query_embedding = embed_fn.embed_query(query)
    results = client.search(
        collection_name=COLLECTION_NAME,
        data=[query_embedding],
        limit=3,
        output_fields=["text", "source"],
    )
    for i, hits in enumerate(results):
        for j, hit in enumerate(hits):
            print(f"  结果{j+1} (score={hit['distance']:.4f}): {hit['entity']['text'][:80]}...")

    print("\n 向量化入库完成！可以启动客服系统了。")


if __name__ == "__main__":
    ingest_documents()