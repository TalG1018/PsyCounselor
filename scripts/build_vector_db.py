import os
import torch
import numpy as np
from transformers import AutoTokenizer, AutoModel
import faiss

def get_embeddings(texts, model, tokenizer, device):
    """使用 BGE 原生方式编码文本"""
    inputs = tokenizer(
        texts,
        padding=True,
        truncation=True,
        return_tensors="pt",
        max_length=512
    ).to(device)
    
    with torch.no_grad():
        outputs = model(**inputs)
        embeddings = outputs.last_hidden_state[:, 0]
        embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
    
    return embeddings.cpu().numpy()

def main():
    # 绝对路径配置
    model_path = "/root/lanyun-tmp/heart/models/bge_large_zh_v1.5"
    chunk_file = "/root/lanyun-tmp/heart/data/chunks.txt"
    index_save_path = "/root/lanyun-tmp/heart/data/psydt_index"
    
    # 加载模型
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"使用设备: {device}")
    
    print("正在加载 BGE 嵌入模型...")
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    model = AutoModel.from_pretrained(model_path, trust_remote_code=True).to(device)
    model.eval()
    print("✅ 模型加载完成")
    
    # 读取 chunks
    print(f"正在读取 {chunk_file}...")
    with open(chunk_file, "r", encoding="utf-8") as f:
        raw_texts = f.read().split("="*60)
    
    texts = [t.strip() for t in raw_texts if t.strip()]
    print(f"共加载 {len(texts)} 个文本块")
    
    # 分批编码
    batch_size = 32
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        emb = get_embeddings(batch, model, tokenizer, device)
        all_embeddings.append(emb)
        print(f"已处理 {min(i+batch_size, len(texts))}/{len(texts)}")
    
    # 合并所有向量
    embeddings_np = np.vstack(all_embeddings).astype('float32')
    print(f"✅ 编码完成，向量维度: {embeddings_np.shape}")
    
    # 使用原生 FAISS 构建索引
    dimension = embeddings_np.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings_np)
    print(f"✅ FAISS 索引构建完成，包含 {index.ntotal} 个向量")
    
    # 保存索引和文本
    os.makedirs(index_save_path, exist_ok=True)
    faiss.write_index(index, os.path.join(index_save_path, "index.faiss"))
    
    # 保存文本数据
    import pickle
    with open(os.path.join(index_save_path, "texts.pkl"), "wb") as f:
        pickle.dump(texts, f)
    
    print(f"✅ 向量数据库已保存至 {index_save_path}")

if __name__ == "__main__":
    main()