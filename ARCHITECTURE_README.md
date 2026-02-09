# PsyCounselor 代码结构说明

## 📁 项目重构说明

本项目已从单一的 `main.py` 文件重构为模块化路由设计，便于维护和扩展。

## 🏗️ 代码结构

### 核心模块文件
```
app/
├── main.py                 # 主应用入口文件（重构后仅168行）
├── main_backup.py         # 原始main.py文件备份
├── __init__.py            # Python包初始化文件
└── __pycache__/           # Python缓存目录
```

### 功能路由模块（每个文件都有详细注释说明）
```
app/
├── chat_routes.py         # 聊天对话路由（202行）
├── health_routes.py       # 健康检查路由（74行）
├── crisis_routes.py       # 危机检测路由（35行）
├── memory_routes.py       # 用户记忆路由（45行）
├── emotion_routes.py      # 情绪分析路由（140行）
├── personality_routes.py  # 人格画像路由（56行）
├── recommendation_routes.py # 个性化建议路由（120行）
└── report_routes.py       # 报告管理路由（37行）
```

### 核心功能模块
```
app/
├── crisis_detector.py     # 危机检测核心逻辑
├── emotion_analyzer.py    # 情绪分析核心逻辑
├── personality_profiler.py # 人格画像分析核心逻辑
├── recommendation_engine.py # 个性化建议引擎核心逻辑
├── memory.py             # 用户记忆管理核心逻辑
└── frontend.py           # 前端界面逻辑
```

## 🔧 启动方式

**仍然只需运行原始命令：**
```bash
cd /root/lanyun-tmp/heart
python app/main.py
```

## 📊 重构收益

### 代码行数对比
- **重构前**: main.py 657行（单一文件）
- **重构后**: main.py 168行（清爽入口）+ 路由模块约1000行（功能分离）

### 优势特点
1. **模块化设计**: 每个功能独立成文件，职责清晰
2. **易于维护**: 修改特定功能只需编辑对应路由文件
3. **便于扩展**: 添加新功能只需创建新的路由模块
4. **代码复用**: 核心逻辑与路由分离，提高复用性
5. **团队协作**: 多人开发时减少代码冲突

### 每个路由文件都包含：
- 📝 详细的文件头注释（说明功能和采用的技术）
- 🎯 专门的API路由定义
- 🔧 全局变量注入机制
- 🛡️ 错误处理和异常捕获

## 🚀 接口地址变更

所有API接口现在都统一使用 `/api` 前缀：

```
POST /api/ask                 # 心理咨询对话
GET  /api/health              # 系统健康检查  
POST /api/emotion/analyze     # 情绪分析
POST /api/personality/analyze # 人格画像分析
POST /api/recommendations/generate # 个性化建议生成
```

## 📝 开发建议

1. **添加新功能**: 创建新的 `{feature}_routes.py` 文件
2. **修改现有功能**: 直接编辑对应的路由文件
3. **核心逻辑修改**: 在相应的核心模块文件中修改
4. **全局配置**: 在 `main.py` 中进行统一配置

## ✅ 测试验证

所有功能均已通过测试验证：
- ✅ 系统健康检查
- ✅ 情绪分析功能
- ✅ 聊天对话功能
- ✅ 其他所有原有功能

