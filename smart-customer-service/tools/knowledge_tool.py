"""RAG知识库检索工具 - 使用 pymilvus MilvusClient（稳定版）"""
from langchain.tools import tool
from langchain_community.embeddings import DashScopeEmbeddings
from pymilvus import MilvusClient


COLLECTION_NAME = "product_knowledge"


def _search_milvus(query: str, top_k: int = 3, score_threshold: float = 0.3):
    """使用 MilvusClient 进行向量检索"""
    client = MilvusClient(uri="http://localhost:19530")
    embed_fn = DashScopeEmbeddings(model="text-embedding-v4")
    query_embedding = embed_fn.embed_query(query)

    results = client.search(
        collection_name=COLLECTION_NAME,
        data=[query_embedding],
        limit=top_k,
        output_fields=["text", "source"],
    )

    context = ""
    for hits in results:
        for hit in hits:
            distance = hit["distance"]
            if distance >= score_threshold:
                text = hit["entity"]["text"]
                context += text + "\n\n"

    return context if context else ""


@tool()
def search_product_knowledge(query: str) -> str:
    """
    根据用户问题检索产品知识库，包括产品功能介绍、常见问题FAQ、退换货政策、保修政策等
    入参：
        query: 字符串类型，用户的咨询问题
    """
    context = _search_milvus(query, top_k=3, score_threshold=0.3)

    if context:
        return f"检索到以下相关信息：\n{context}"
    else:
        return "知识库中未找到与该问题相关的信息，请建议用户联系人工客服 400-888-0000"


# ========== 测试 ==========
if __name__ == "__main__":
    print("=== 测试 search_product_knowledge ===")
    print(search_product_knowledge.invoke({"query": "学习机怎么退货"}))
    print()
    print(search_product_knowledge.invoke({"query": "AI学习机Pro有什么功能"}))