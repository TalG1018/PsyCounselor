import gradio as gr
import requests
import os
import re
import json
import shutil
import time
import webbrowser
from datetime import datetime

# 移除了matplotlib相关导入，因为我们不再需要图表功能

# 解决中文字体问题
try:
    available_fonts = matplotlib.font_manager.get_font_names()
    en_fonts = ['DejaVu Sans', 'Arial', 'Helvetica', 'Times New Roman', 'Courier New']
    plt.rcParams['font.sans-serif'] = [font for font in en_fonts if font in available_fonts] + ['sans-serif']
    plt.rcParams['axes.unicode_minus'] = False
except:
    pass

API_URL = "http://localhost:8001/ask"
# 移除了TREND_URL，因为我们不再需要图表功能
# REPORT_URL = "http://localhost:8001/report/generate"  # 已移除报告功能

def chat(message, history, user_id):
    """发送消息并获取回复"""
    try:
        response = requests.post(
            API_URL,
            json={"query": message, "user_id": user_id},
            timeout=120
        )
        response.raise_for_status()
        result = response.json()
        
        answer = result["answer"]
        risk_level = result.get("risk_level", "low")
        
        # 根据风险等级添加视觉提示
        if risk_level == "high":
            warning = "🚨 **系统检测到高危心理状态，已启动安全干预机制**\n\n"
            return warning + answer
        elif risk_level == "medium":
            notice = "💛 **系统检测到您情绪较低落，请多关心自己**\n\n"
            return notice + answer
        else:
            return answer
            
    except Exception as e:
        return f"抱歉，系统暂时无法响应：{str(e)}"

def open_emotion_dashboard(user_id):
    """
    打开情绪分析仪表板
    """
    try:
        # HTML文件路径
        html_path = "/root/lanyun-tmp/heart/emotion_dashboard.html"
        
        if not os.path.exists(html_path):
            return f"❌ 未找到情绪分析仪表板文件: {html_path}"
        
        # 启动一个简单的HTTP服务器来提供HTML文件
        import threading
        import http.server
        import socketserver
        
        # 检查端口是否可用
        def is_port_available(port):
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(('localhost', port)) != 0
        
        # 寻找可用端口
        dashboard_port = 8080
        while not is_port_available(dashboard_port) and dashboard_port < 8100:
            dashboard_port += 1
        
        if dashboard_port >= 8100:
            return f"❌ 无法找到可用端口启动仪表板服务"
        
        # 创建HTTP服务器
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory="/root/lanyun-tmp/heart", **kwargs)
            
            def log_message(self, format, *args):
                # 静默日志
                pass
        
        def start_server():
            try:
                with socketserver.TCPServer(("localhost", dashboard_port), Handler) as httpd:
                    print(f"仪表板服务器启动在端口 {dashboard_port}")
                    httpd.serve_forever()
            except Exception as e:
                print(f"服务器启动失败: {e}")
        
        # 在后台线程启动服务器
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        
        # 等待服务器启动
        import time
        time.sleep(1)
        
        # 构造HTTP URL
        http_url = f"http://localhost:{dashboard_port}/emotion_dashboard.html?user_id={user_id}"
        
        # 在浏览器中打开
        webbrowser.open(http_url)
        
        return f"✅ 已在浏览器中打开情绪分析仪表板\n用户ID: {user_id}\n访问地址: {http_url}\n\n如果浏览器未自动打开，请手动访问上述地址"
            
    except Exception as e:
        return f"❌ 打开情绪分析仪表板失败: {str(e)}"

# 移除了on_user_change函数，因为我们不再需要自动更新图表

def generate_and_download_report(user_id, chat_history):
    """报告功能已移除"""
    return None, "❌ 报告功能已停用"

def update_file_visibility(file_obj):
    """更新文件可见性 - 已移除报告功能"""
    return gr.update(visible=False)

# 创建界面
demo = gr.Blocks(
    title="PsyCounselor - AI心理咨询助手（情绪可视化版）",
    css="""
    /* 全局样式优化 */
    body {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* 主容器样式 */
    .gradio-container {
        max-width: 1400px !important;
        margin: 0 auto !important;
        padding: 20px !important;
        background: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: blur(10px) !important;
        border-radius: 20px !important;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2) !important;
    }
    
    /* 标题样式 */
    h1 {
        background: linear-gradient(90deg, #4b6cb7 0%, #182848 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        font-size: 2.8rem !important;
        text-align: center !important;
        margin-bottom: 10px !important;
        font-weight: 700 !important;
    }
    
    /* 卡片样式 */
    .gr-box {
        background: white !important;
        border-radius: 15px !important;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1) !important;
        border: none !important;
        transition: all 0.3s ease !important;
    }
    
    .gr-box:hover {
        transform: translateY(-5px) !important;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15) !important;
    }
    
    /* 按钮样式优化 */
    .gr-button-primary {
        background: linear-gradient(90deg, #4b6cb7 0%, #182848 100%) !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 12px 25px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(75, 108, 183, 0.3) !important;
    }
    
    .gr-button-primary:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 25px rgba(75, 108, 183, 0.4) !important;
    }
    
    .gr-button-secondary {
        background: linear-gradient(90deg, #6c757d 0%, #495057 100%) !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 12px 25px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    .gr-button-secondary:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 25px rgba(108, 117, 125, 0.3) !important;
    }
    
    /* 文本框样式 */
    .gr-input {
        border: 2px solid #e9ecef !important;
        border-radius: 12px !important;
        padding: 15px !important;
        transition: all 0.3s ease !important;
    }
    
    .gr-input:focus {
        border-color: #4b6cb7 !important;
        box-shadow: 0 0 0 3px rgba(75, 108, 183, 0.1) !important;
    }
    
    /* 聊天容器样式 */
    .chat-container {
        background: #f8f9fa !important;
        border-radius: 15px !important;
        padding: 20px !important;
        border: none !important;
    }
    
    /* 预警框样式 */
    #alert_box {
        background: linear-gradient(90deg, #fff3cd 0%, #ffeaa7 100%) !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 15px !important;
        font-weight: 500 !important;
    }
    
    /* 示例按钮样式 */
    .example-btn {
        background: linear-gradient(90deg, #20bf6b 0%, #0fb9b1 100%) !important;
        border: none !important;
        border-radius: 8px !important;
        margin: 5px !important;
        transition: all 0.3s ease !important;
    }
    
    .example-btn:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 5px 15px rgba(32, 191, 107, 0.3) !important;
    }
    
    /* 侧边栏样式 */
    .sidebar-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important;
        border-radius: 15px !important;
        padding: 25px !important;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08) !important;
    }
    
    /* 响应式设计 */
    @media (max-width: 1200px) {
        .gradio-container {
            max-width: 95% !important;
            padding: 15px !important;
        }
        
        .chat-container {
            height: 600px !important;
        }
    }
    
    @media (max-width: 768px) {
        .gradio-container {
            margin: 10px !important;
            padding: 15px !important;
            border-radius: 15px !important;
        }
        
        h1 {
            font-size: 2rem !important;
        }
        
        .gr-box {
            margin-bottom: 15px !important;
        }
        
        .chat-container {
            height: 500px !important;
            padding: 15px !important;
        }
        
        .gr-button-primary, .gr-button-secondary {
            width: 100% !important;
            margin-bottom: 10px !important;
        }
        
        .example-btn {
            width: 48% !important;
            margin: 2px !important;
            font-size: 0.9rem !important;
        }
    }
    
    @media (max-width: 480px) {
        .gradio-container {
            margin: 5px !important;
            padding: 10px !important;
        }
        
        h1 {
            font-size: 1.5rem !important;
        }
        
        .chat-container {
            height: 400px !important;
        }
        
        .example-btn {
            width: 100% !important;
            font-size: 0.85rem !important;
        }
    }
    
    /* 加载动画 */
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .thinking-animation {
        animation: pulse 1.5s ease-in-out infinite;
    }
    
    /* 主题切换开关样式 */
    .theme-toggle {
        position: absolute;
        top: 20px;
        right: 20px;
        z-index: 1000;
    }
    
    /* 深色模式样式 */
    .dark-mode body {
        background: linear-gradient(135deg, #2c3e50 0%, #4a235a 100%) !important;
    }
    
    .dark-mode .gradio-container {
        background: rgba(30, 30, 46, 0.95) !important;
        color: #e0e0e0 !important;
    }
    
    .dark-mode .gr-box {
        background: #2d2d3a !important;
        color: #e0e0e0 !important;
    }
    
    .dark-mode .chat-container {
        background: #36393f !important;
        color: #e0e0e0 !important;
    }
    
    .dark-mode .gr-input {
        background: #2d2d3a !important;
        border-color: #555 !important;
        color: #e0e0e0 !important;
    }
    
    .dark-mode .gr-input:focus {
        border-color: #4b6cb7 !important;
        box-shadow: 0 0 0 3px rgba(75, 108, 183, 0.3) !important;
    }
    
    .dark-mode h1, .dark-mode h2, .dark-mode h3 {
        color: #ffffff !important;
    }
    
    .dark-mode .gr-markdown {
        color: #e0e0e0 !important;
    }
    
    /* 特殊组件深色模式 */
    .dark-mode .dashboard-output {
        background: #2d2d3a !important;
        color: #e0e0e0 !important;
        border-color: #555 !important;
    }
    
    .dark-mode .sidebar-card {
        background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%) !important;
    }
    """
)

with demo:
    # 添加主题切换组件
    with gr.Row():
        theme_toggle = gr.Checkbox(
            label="🌙 深色模式", 
            value=False,
            elem_classes=["theme-toggle"]
        )
    
    gr.Markdown("""
    # 🧠 PsyCounselor - AI心理咨询助手
    ### 安全增强版：集成自杀危机识别 + 多轮记忆 + 情绪趋势可视化
    
    ⚠️ **安全提示**：本系统具备自杀危机识别功能，高危情况将自动触发干预机制
    """)
    
    with gr.Row():
        with gr.Column(scale=3):
            # 用户ID输入
            user_id_input = gr.Textbox(
                label="用户ID（用于记忆和趋势分析）", 
                placeholder="输入您的用户ID，例如：user_001",
                value="user_default"
            )
            
            # 预警信息
            alert_box = gr.Textbox(
                label="系统预警", 
                value="请输入用户ID开始对话...",
                interactive=False
            )
            
            # 聊天界面
            chatbot = gr.Chatbot(
                height=800,
                autoscroll=True,
                show_label=False,
                elem_classes=["chat-container"]
            )
            msg = gr.Textbox(
                label="输入消息", 
                placeholder="请输入您的问题...", 
                show_label=False
            )
            
            def respond(message, chat_history, user_id):
                """处理用户消息并返回回复"""
                if not message or not message.strip():
                    return chat_history, "", alert_box.value
                
                # 显示用户消息
                chat_history = chat_history + [{"role": "user", "content": message}]
                yield chat_history, "", "🧠 思考中..."
                
                # 获取AI回复
                try:
                    import time
                    max_retries = 2
                    answer = ""
                    
                    for retry in range(max_retries):
                        try:
                            print(f"📡 API调用尝试 {retry + 1}/{max_retries}...")
                            response = requests.post(
                                API_URL,
                                json={"query": message, "user_id": user_id},
                                timeout=180
                            )
                            response.raise_for_status()
                            result = response.json()
                            answer = result["answer"]
                            
                            # 验证回复完整性
                            if len(answer) > 50:
                                print(f"✅ API调用成功，回复长度: {len(answer)} 字符")
                                break
                            elif retry < max_retries - 1:
                                print(f"⚠️ 回复过短({len(answer)}字符)，准备重试...")
                                time.sleep(3)
                                continue
                        except Exception as e:
                            if retry < max_retries - 1:
                                print(f"❌ 第{retry + 1}次调用失败: {str(e)}，准备重试...")
                                time.sleep(5)
                                continue
                            else:
                                print(f"❌ 所有重试失败: {str(e)}")
                                raise e
                    
                    if not answer:
                        raise Exception("无法获取有效回复")
                    
                    risk_level = result.get("risk_level", "low")
                    
                    # 更新预警信息
                    if risk_level == "high":
                        alert = "⚠️ 请立即关注用户心理状态 - 高危"
                    elif risk_level == "medium":
                        alert = "📊 情绪波动，建议关注趋势 - 中危"
                    else:
                        alert = "✅ 情绪平稳"
                    
                    # 添加助手回复
                    chat_history = chat_history + [{"role": "assistant", "content": answer}]
                    yield chat_history, "", alert
                    
                except Exception as e:
                    error_msg = f"系统错误: {str(e)}"
                    chat_history = chat_history + [{"role": "assistant", "content": error_msg}]
                    yield chat_history, "", "❌ 系统错误"
            
            # 按钮区域
            with gr.Row():
                submit_btn = gr.Button("🚀 发送消息", variant="primary", elem_classes=["send-btn"])
                clear_btn = gr.Button("🧹 清空对话", variant="secondary", elem_classes=["clear-btn"])
            
            # 示例按钮
            with gr.Row():
                gr.Markdown("**快速示例:**")
            
            example_buttons = [
                "我最近压力很大，睡不着觉",
                "觉得自己一无是处，想自杀",
                "和家人关系很紧张",
                "看不到希望，很痛苦"
            ]
            
            with gr.Row():
                gr.Markdown("**💡 快速示例:**")
            
            with gr.Row():
                for i, ex in enumerate(example_buttons):
                    btn = gr.Button(ex[:15] + "...", size="sm", elem_classes=["example-btn"])
                    btn.click(lambda x=ex: x, outputs=msg)
            
            # 绑定事件
            submit_btn.click(
                fn=respond,
                inputs=[msg, chatbot, user_id_input],
                outputs=[chatbot, msg, alert_box]
            )
            
            msg.submit(
                fn=respond,
                inputs=[msg, chatbot, user_id_input],
                outputs=[chatbot, msg, alert_box]
            )
            
            def clear_chat():
                return [], "", "对话已清空"
            
            clear_btn.click(
                fn=clear_chat,
                outputs=[chatbot, msg, alert_box]
            )
            
        with gr.Column(scale=2):
            # 情绪分析仪表板区域
            with gr.Group(elem_classes=["sidebar-card"]):
                gr.Markdown("### 📊 情绪分析仪表板")
                
                dashboard_btn = gr.Button("📈 打开情绪分析仪表板", variant="primary", elem_classes=["dashboard-btn"])
                dashboard_output = gr.Textbox(
                    label="操作结果",
                    placeholder="点击按钮打开情绪分析仪表板...",
                    interactive=False,
                    lines=5,
                    elem_classes=["dashboard-output"]
                )

    # 事件绑定 - 打开情绪分析仪表板
    dashboard_btn.click(
        fn=open_emotion_dashboard,
        inputs=user_id_input,
        outputs=[dashboard_output]
    )
    
    # 主题切换功能
    def toggle_theme(is_dark):
        """切换主题模式"""
        if is_dark:
            return gr.update(elem_classes=["dark-mode"])
        else:
            return gr.update(elem_classes=[])
    
    theme_toggle.change(
        fn=toggle_theme,
        inputs=theme_toggle,
        outputs=demo
    )

if __name__ == "__main__":
    print("正在启动AI心理咨询助手...")
    print("访问地址: http://localhost:7861")
    print("功能：心理咨询对话 + 情绪分析仪表板")
    
    demo.launch(
        server_name="0.0.0.0", 
        server_port=7861,
        share=False
    )