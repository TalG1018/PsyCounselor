# 📁 PsyCounselor 项目文件清单

## 📋 项目结构概览

```
heart/
├── 📄 README.md                 # 项目主文档
├── 📄 INSTALL.md                # 安装指南
├── 📄 .gitignore                # Git忽略文件配置
├── 📄 requirements_core.txt     # 核心依赖清单
├── 📄 PROJECT_HIGHLIGHTS.md     # 项目亮点展示
├── 📄 PROJECT_SHOWCASE.md       # 项目展示文档
├── 📄 ARCHITECTURE_README.md    # 架构说明文档
├── 📄 FUNCTIONS_GUIDE.md        # 功能使用指南
├── 📄 FRONTEND_OPTIMIZATION_SUMMARY.md  # 前端优化总结
├── 📄 REDIS_MIGRATION_COMPLETION.md     # Redis迁移完成文档
├── 📄 REALTIME_CHAT_GUIDE.md    # 实时聊天指南
├── 📁 app/                      # 后端核心代码
│   ├── main.py                 # FastAPI主应用
│   ├── frontend.py             # Gradio前端界面
│   ├── chat_routes.py          # 聊天路由
│   ├── emotion_routes.py       # 情绪分析路由
│   ├── personality_routes.py   # 人格分析路由
│   ├── crisis_routes.py        # 危机检测路由
│   ├── memory_routes.py        # 记忆管理路由
│   ├── recommendation_routes.py # 建议生成路由
│   ├── report_routes.py        # 报告管理路由
│   ├── crisis_detector.py      # 危机检测核心
│   ├── emotion_analyzer.py     # 情绪分析引擎
│   ├── personality_profiler.py # 人格画像分析器
│   ├── recommendation_engine.py # 个性化建议引擎
│   ├── memory.py               # 用户记忆管理
│   ├── redis_client.py         # Redis客户端
│   ├── redis_memory.py         # Redis记忆存储
│   ├── storage_config.py       # 存储配置
│   └── health_routes.py        # 健康检查路由
├── 📁 models/                   # AI模型文件（需单独下载）
│   ├── qwen3_32b_awq/          # Qwen3-32B大模型
│   ├── crisis_bert/            # 危机检测模型
│   └── bge_large_zh_v1.5/      # 向量编码器
├── 📁 dataset/                  # 训练数据集
│   └── PsyDTCorpus/            # 心理咨询对话语料库
├── 📁 data/                     # 用户数据存储
│   └── emotion_history.json    # 情绪历史记录
├── 📁 scripts/                  # 辅助脚本
│   ├── preprocess.py           # 数据预处理
│   └── build_vector_db.py      # 向量库构建
├── 📄 emotion_dashboard.html    # 情绪分析仪表板
├── 📄 personality_dashboard.html # 人格画像仪表板
└── 📄 recommendation_dashboard.html # 建议生成仪表板
```

## 📦 GitHub上传说明

### ✅ 将上传的文件
- 所有 `.md` 文档文件
- `app/` 目录下所有Python代码文件
- `scripts/` 目录下脚本文件
- `dataset/` 目录下数据文件
- `data/` 目录下配置文件
- HTML仪表板文件
- `.gitignore` 配置文件

### ❌ 不上传的文件/目录
- `models/` 目录（大型模型文件）
- `__pycache__/` 目录
- `.env` 环境配置文件
- 日志文件
- 临时文件

### 📥 模型文件获取地址

用户需要自行下载以下模型文件：

1. **Qwen3-32B-AWQ 大语言模型**
   - 地址: https://www.modelscope.cn/models/Qwen/Qwen3-32B-AWQ
   - 放置: `./models/qwen3_32b_awq/`

2. **CrisisBERT 危机检测模型**
   - 地址: https://huggingface.co/liiinn/crisis-bert/tree/main
   - 放置: `./models/crisis_bert/`

3. **BGE-large-zh-v1.5 向量编码器**
   - 地址: https://huggingface.co/BAAI/bge-large-zh-v1.5
   - 放置: `./models/bge_large_zh_v1.5/`

## 🚀 快速开始步骤

1. 克隆GitHub仓库
2. 按照INSTALL.md安装依赖
3. 下载必需的模型文件
4. 启动服务并开始使用

## 📞 技术支持

如遇问题，请查阅：
- 📖 INSTALL.md - 安装和配置指南
- 📊 FUNCTIONS_GUIDE.md - 功能使用说明
- 🏗️ ARCHITECTURE_README.md - 技术架构文档
- 🌟 PROJECT_HIGHLIGHTS.md - 项目优势介绍