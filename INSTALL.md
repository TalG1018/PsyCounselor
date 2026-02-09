# 🚀 快速安装指南

## 系统要求
- **操作系统**: Linux/macOS/Windows
- **Python版本**: 3.8+
- **内存**: 至少16GB RAM（推荐32GB+）
- **存储空间**: 至少50GB可用空间

## 安装步骤

### 1. 克隆项目
```bash
git clone <your-repository-url>
cd heart
```

### 2. 创建虚拟环境
```bash
# 使用conda（推荐）
conda create -n psycounselor python=3.9
conda activate psycounselor

# 或使用venv
python -m venv psycounselor_env
source psycounselor_env/bin/activate  # Linux/macOS
# 或 psycounselor_env\Scripts\activate  # Windows
```

### 3. 安装依赖
```bash
# 安装核心依赖
pip install -r requirements_core.txt

# 如果需要GPU支持
pip install faiss-gpu
```

### 4. 下载模型文件
请从以下链接下载必需的模型文件并放置到对应目录：

#### 必需模型：
1. **Qwen3-32B-AWQ** → `./models/qwen3_32b_awq/`
   - 下载地址: https://www.modelscope.cn/models/Qwen/Qwen3-32B-AWQ

2. **CrisisBERT** → `./models/crisis_bert/`
   - 下载地址: https://huggingface.co/liiinn/crisis-bert/tree/main

3. **BGE-large-zh-v1.5** → `./models/bge_large_zh_v1.5/`
   - 下载地址: https://huggingface.co/BAAI/bge-large-zh-v1.5

### 5. 启动服务
```bash
# 启动后端API（终端1）
python app/main.py

# 启动前端界面（终端2）
python app/frontend.py
```

### 6. 访问应用
- **主界面**: http://localhost:7861
- **API文档**: http://localhost:8001/docs
- **情绪仪表板**: http://localhost:8001/emotion_dashboard.html

## 故障排除

### 常见问题：

1. **模块导入错误**
   ```bash
   pip install --upgrade pip
   pip install -r requirements_core.txt --force-reinstall
   ```

2. **CUDA相关错误**
   ```bash
   # CPU-only版本
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
   ```

3. **内存不足**
   - 减少批量大小
   - 使用模型量化版本
   - 增加swap空间

4. **端口占用**
   ```bash
   # 查找占用端口的进程
   lsof -i :8001
   # 杀死进程
   kill -9 <PID>
   ```

## 性能优化建议

1. **使用GPU加速**：安装CUDA版本的PyTorch
2. **模型量化**：使用AWQ/GPTQ量化版本
3. **批处理优化**：调整批处理大小
4. **缓存机制**：启用模型和数据缓存

## 开发环境配置

```bash
# 安装开发依赖
pip install pytest black flake8 pre-commit

# 代码格式化
black .
flake8 .

# 运行测试
pytest tests/
```