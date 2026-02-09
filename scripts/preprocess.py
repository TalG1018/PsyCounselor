#数据预处理
import json
import os

def main():
    # JSON 文件路径
    input_path = r"/root/lanyun-tmp/heart/dataset/PsyDTCorpus/PsyDTCorpus_train_mulit_turn_packing.json"
    output_path = r"/root/lanyun-tmp/heart/data/chunks.txt"
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"找不到数据文件: {input_path}")
    
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    chunks = []
    
    for item in data:
        messages = item.get("messages", [])
        dialog_lines = []
        
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "").strip()
            
            if not content:
                continue
            
            # 映射角色名称
            speaker = "客户" if role == "user" else "咨询师" if role == "assistant" else "系统"
            dialog_lines.append(f"{speaker}:{content}")
        
        if dialog_lines:
            # 拼接成完整对话
            chunk = "\n".join(dialog_lines)
            chunks.append(chunk)
    
    # 写入文件，用分隔符分隔
    with open(output_path, "w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(chunk + "\n" + "="*60 + "\n")
    
    print(f"✅ 成功生成 {len(chunks)} 个对话块，保存至 {output_path}")

if __name__ == "__main__":
    main()