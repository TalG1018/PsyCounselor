# 📚 上下文长度管理使用指南

## 🎯 功能概述

本项目现已集成智能上下文长度管理功能，支持128K token的智能压缩和管理，解决了长对话场景下的上下文长度限制问题。

## 🔧 核心特性

### 1. 智能Token管理
- **128K Token限制**：支持最大128,000个token的上下文窗口
- **动态压缩**：当接近限制时自动压缩历史对话
- **重要性评分**：基于时间、情绪强度、关键词等因素评估对话重要性

### 2. 多层次压缩策略
- **滑动窗口**：自动移除最不重要的历史对话
- **智能摘要**：将多轮对话压缩为精炼的摘要信息
- **优先级保留**：始终保持最近和最重要的对话内容

### 3. 情绪感知优化
- **情绪强度权重**：高情绪强度的对话获得更多保留权重
- **危机关键词保护**：包含"危机"、"自杀"等关键词的对话优先保留
- **个性化压缩**：根据不同用户的情绪模式调整压缩策略

## 🚀 使用方法

### 基本使用

```python
from app.context_manager import ContextManager

# 创建上下文管理器（默认128K限制）
cm = ContextManager(max_tokens=128000)

# 添加对话轮次
cm.add_turn(
    user_message="我最近感觉很焦虑",
    ai_response="理解您的感受，焦虑是很常见的情绪反应。",
    emotion_score=0.8,  # 情绪强度(0-1)
    keywords=["焦虑", "情绪"]  # 关键词列表
)

# 获取格式化上下文
context = cm.get_formatted_context(max_turns=5)
print(context)

# 查看统计信息
stats = cm.get_statistics()
print(f"当前token数: {stats['total_tokens']}")
print(f"利用率: {stats['utilization_rate']}%")
```

### 在聊天路由中的集成

系统已自动集成到聊天路由中，无需额外配置：

```python
# 系统会自动为每个用户创建独立的上下文管理器
# 在 /api/ask 接口中自动处理上下文长度管理
```

## 📊 管理策略详解

### 重要性评分算法

```python
重要性分数 = 时间因子 × 情绪因子 × 关键词因子 × 长度因子

- 时间因子：越新的对话越重要（默认1.0）
- 情绪因子：情绪强度加权（1.0 + 情绪分数×0.5）
- 关键词因子：包含危机关键词时为2.0，否则1.0
- 长度因子：避免过短对话占位（最小1.0，最大2.0）
```

### 压缩触发条件

1. **Token超限检测**：当前token数超过设定限制
2. **分层压缩策略**：
   - 优先移除低重要性轮次
   - 必要时创建历史摘要
   - 始终保留最近几轮对话

### 摘要生成机制

当需要大幅压缩时，系统会：
1. 合并早期对话轮次
2. 提取关键主题和情绪趋势
3. 生成简洁的历史摘要
4. 用摘要替换原始对话内容

## 📈 监控和调试

### 统计信息查看

```python
stats = cm.get_statistics()
# 返回字典包含：
{
    "total_turns": 15,          # 总对话轮次
    "total_tokens": 45200,      # 当前token总数
    "compressed_turns": 2,      # 已压缩轮次数
    "available_tokens": 82800,  # 可用token数
    "utilization_rate": 35.3,   # 利用率百分比
    "max_limit": 128000         # 最大限制
}
```

### 日志监控

系统会在以下情况下输出日志：
- 上下文超出限制时
- 执行压缩操作时
- 创建摘要时
- 清空上下文时

## ⚙️ 配置选项

### 初始化参数

```python
ContextManager(
    max_tokens=128000,        # 最大token限制
    avg_chars_per_token=4,    # 平均字符/token比率（中文建议3-4）
    preserve_system_prompt=True  # 是否为系统提示词预留空间
)
```

### 系统提示词预留

默认为系统提示词预留200个token空间，可通过修改`system_prompt_tokens`属性调整。

## 🔍 最佳实践

### 1. 合理设置限制
```python
# 根据实际需求调整token限制
cm = ContextManager(max_tokens=64000)  # 64K限制
```

### 2. 定期监控使用情况
```python
# 在关键节点检查上下文状态
if stats['utilization_rate'] > 80:
    print("上下文接近限制，考虑优化对话长度")
```

### 3. 情绪数据充分利用
```python
# 提供准确的情绪分数以优化压缩策略
cm.add_turn(
    user_message=user_input,
    ai_response=ai_output,
    emotion_score=get_emotion_score(user_input),  # 从情绪分析器获取
    keywords=extract_keywords(user_input)         # 提取关键词
)
```

## 🚨 注意事项

1. **字符-token转换**：中文平均3-4字符/token，英文约4-5字符/token
2. **压缩不可逆**：被压缩的内容无法完全恢复原始细节
3. **实时性优先**：系统优先保证最近对话的完整性
4. **内存管理**：长时间对话建议定期清理不必要的历史记录

## 🧪 测试验证

项目包含完整的测试用例，在`context_manager.py`末尾：

```bash
# 运行测试
python app/context_manager.py
```

测试会模拟长对话场景，验证各种压缩策略的有效性。

## 📞 技术支持

如遇到上下文管理相关问题，请检查：
1. 日志输出中的压缩操作记录
2. 统计信息中的token使用情况
3. 配置参数是否合理设置

这个智能上下文管理系统能够有效解决长对话场景下的token限制问题，同时保持对话质量和用户体验。