"""
个性化心理咨询建议生成引擎
基于用户情绪轨迹、人格特征、对话历史生成定制化建议
"""

import json
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import re

class RecommendationEngine:
    """个性化建议生成引擎"""
    
    def __init__(self):
        # 建议模板库
        self.recommendation_templates = {
            'stress_management': {
                'high_neuroticism': [
                    "建议尝试正念冥想，每天10-15分钟，有助于缓解焦虑情绪",
                    "建立规律的作息时间，充足睡眠对情绪稳定很重要",
                    "学习深呼吸放松技巧，在感到压力时及时使用"
                ],
                'low_conscientiousness': [
                    "制定简单的日常计划，从小目标开始培养自律习惯",
                    "使用任务清单管理每日事务，减少遗忘带来的压力",
                    "设置合理的截止时间，避免临时抱佛脚"
                ],
                'high_extraversion': [
                    "增加体育运动时间，将社交能量转化为积极行动",
                    "寻找志同道合的朋友一起参与兴趣活动",
                    "参加团体心理辅导课程，获得更多支持"
                ]
            },
            'relationship_improvement': {
                'low_agreeableness': [
                    "练习主动倾听技巧，关注他人感受而非急于表达自己",
                    "学习换位思考，在冲突中寻找双赢解决方案",
                    "定期表达对他人的感谢和认可"
                ],
                'high_neuroticism': [
                    "学会识别自己的情绪触发点，提前做好心理准备",
                    "在关系中保持适当的边界感，避免过度依赖",
                    "寻求专业帮助处理深层的情感创伤"
                ]
            },
            'career_development': {
                'high_openness': [
                    "探索跨领域学习机会，发挥创造力优势",
                    "考虑创新型工作岗位，充分利用开放性特质",
                    "参与头脑风暴会议，贡献独特见解"
                ],
                'high_conscientiousness': [
                    "担任项目管理角色，发挥组织协调能力",
                    "制定长期职业规划，稳步实现目标",
                    "成为团队中的可靠执行者"
                ]
            },
            'emotional_regulation': {
                'general': [
                    "建立情绪日记习惯，记录触发因素和应对方式",
                    "学习认知重构技巧，改变消极思维模式",
                    "培养兴趣爱好，为生活增添积极体验"
                ]
            }
        }
        
        # 干预策略库
        self.intervention_strategies = {
            'immediate_relief': [
                "立即进行5分钟深呼吸练习",
                "离开当前环境，到户外走动10分钟",
                "听一首喜欢的音乐放松心情"
            ],
            'short_term_goals': [
                "本周内完成一项让自己感到成就感的小任务",
                "主动联系一位朋友进行积极互动",
                "尝试一种新的放松方式（如瑜伽、绘画等）"
            ],
            'long_term_development': [
                "制定3个月的情绪管理提升计划",
                "寻找专业的心理咨询师进行定期咨询",
                "加入相关的自助小组或在线社区"
            ]
        }
    
    def generate_personalized_recommendations(self, user_id: str, 
                                            emotion_history: List[Dict],
                                            personality_profile: Dict[str, Any],
                                            recent_conversations: List[Dict]) -> Dict[str, Any]:
        """
        生成个性化建议报告
        
        Args:
            user_id: 用户ID
            emotion_history: 情绪历史数据
            personality_profile: 人格画像数据
            recent_conversations: 最近对话记录
            
        Returns:
            dict: 包含个性化建议的完整报告
        """
        
        # 分析用户当前状态
        current_state = self._analyze_current_state(emotion_history, recent_conversations)
        
        # 基于人格特征选择建议
        personality_based_suggestions = self._generate_personality_suggestions(personality_profile)
        
        # 基于情绪模式生成针对性建议
        emotion_based_suggestions = self._generate_emotion_suggestions(current_state)
        
        # 生成行动计划
        action_plan = self._create_action_plan(current_state, personality_profile)
        
        # 组装完整报告
        recommendation_report = {
            'user_id': user_id,
            'generated_at': datetime.now().isoformat(),
            'current_assessment': current_state,
            'personality_insights': personality_based_suggestions,
            'targeted_recommendations': emotion_based_suggestions,
            'action_plan': action_plan,
            'immediate_interventions': self._get_immediate_interventions(current_state),
            'resources': self._compile_resources(current_state)
        }
        
        return recommendation_report
    
    def _analyze_current_state(self, emotion_history: List[Dict], 
                              conversations: List[Dict]) -> Dict[str, Any]:
        """分析用户当前心理状态"""
        state_analysis = {
            'emotion_trend': 'stable',
            'stress_level': 'moderate',
            'primary_concerns': [],
            'recent_patterns': []
        }
        
        if not emotion_history:
            return state_analysis
            
        # 情绪趋势分析
        recent_emotions = emotion_history[-10:] if len(emotion_history) >= 10 else emotion_history
        emotion_values = [record.get('emotion_score', 0) for record in recent_emotions]
        
        if len(emotion_values) >= 3:
            # 计算情绪变化趋势
            recent_avg = np.mean(emotion_values[-3:])
            overall_avg = np.mean(emotion_values)
            
            if recent_avg > overall_avg + 0.2:
                state_analysis['emotion_trend'] = 'improving'
            elif recent_avg < overall_avg - 0.2:
                state_analysis['emotion_trend'] = 'declining'
            
            # 压力水平评估
            high_stress_threshold = 0.7
            if recent_avg > high_stress_threshold:
                state_analysis['stress_level'] = 'high'
            elif recent_avg < 0.3:
                state_analysis['stress_level'] = 'low'
        
        # 识别主要关注领域
        concern_keywords = {
            'work': ['工作', '职场', '压力', '加班', '绩效'],
            'relationship': ['感情', '恋爱', '家庭', '父母', '朋友'],
            'health': ['身体', '疾病', '健康', '失眠', '疲劳'],
            'future': ['前途', '未来', '迷茫', '不确定', '焦虑']
        }
        
        all_text = ' '.join([msg.get('content', '') for msg in conversations[-5:] if isinstance(msg, dict)])
        
        for concern, keywords in concern_keywords.items():
            if any(keyword in all_text for keyword in keywords):
                state_analysis['primary_concerns'].append(concern)
        
        return state_analysis
    
    def _generate_personality_suggestions(self, personality_profile: Dict[str, Any]) -> List[str]:
        """基于人格特征生成建议"""
        suggestions = []
        
        if 'personality_traits' not in personality_profile:
            return ["建议进行完整的人格测评以获得更精准的建议"]
        
        traits = personality_profile['personality_traits']
        
        # 针对高神经质的建议
        if traits.get('neuroticism', {}).get('score', 50) > 70:
            suggestions.extend([
                "您的情绪敏感度较高，建议建立稳定的情绪管理routine",
                "学习接纳不确定性，减少对完美的过度追求",
                "培养安全感来源，如固定的社交圈子或兴趣爱好"
            ])
        
        # 针对低宜人性的建议
        if traits.get('agreeableness', {}).get('score', 50) < 30:
            suggestions.extend([
                "尝试在人际交往中多关注他人需求和感受",
                "练习表达感激和认可，增强人际关系质量",
                "学习妥协和协商技巧，在冲突中寻求平衡"
            ])
        
        # 针对高开放性的建议
        if traits.get('openness', {}).get('score', 50) > 70:
            suggestions.extend([
                "充分利用您的创造力，在工作中寻找创新机会",
                "探索多元化的兴趣爱好，丰富人生体验",
                "考虑从事需要创造性思维的职业领域"
            ])
        
        return suggestions
    
    def _generate_emotion_suggestions(self, current_state: Dict[str, Any]) -> List[str]:
        """基于情绪状态生成建议"""
        suggestions = []
        
        stress_level = current_state.get('stress_level', 'moderate')
        emotion_trend = current_state.get('emotion_trend', 'stable')
        
        if stress_level == 'high':
            suggestions.extend([
                "当前压力水平较高，建议优先处理最紧迫的问题",
                "建立紧急减压机制，如深呼吸、短暂休息等",
                "考虑寻求专业心理支持，不要独自承担所有压力"
            ])
        elif stress_level == 'low':
            suggestions.extend([
                "目前情绪状态相对平稳，是进行自我提升的好时机",
                "可以尝试设定一些有挑战性的个人目标",
                "主动扩展社交圈，增加积极的人际互动"
            ])
        
        if emotion_trend == 'declining':
            suggestions.extend([
                "注意情绪下滑的趋势，及时调整生活节奏",
                "回顾最近的变化，识别可能的负面影响因素",
                "增加积极活动的频率，如运动、社交等"
            ])
        elif emotion_trend == 'improving':
            suggestions.extend([
                "继续保持当前的良好势头",
                "总结有效的应对策略，形成个人经验库",
                "可以适当提高对自己的期望和挑战"
            ])
        
        return suggestions
    
    def _create_action_plan(self, current_state: Dict[str, Any], 
                           personality_profile: Dict[str, Any]) -> Dict[str, Any]:
        """创建个性化行动计划"""
        action_plan = {
            'immediate_actions': [],  # 1-3天内
            'short_term_goals': [],   # 1-4周内
            'long_term_objectives': []  # 1-3个月内
        }
        
        stress_level = current_state.get('stress_level', 'moderate')
        concerns = current_state.get('primary_concerns', [])
        
        # 立即行动（应急措施）
        if stress_level == 'high':
            action_plan['immediate_actions'] = [
                "今天进行15分钟冥想或深呼吸练习",
                "联系一位信任的朋友倾诉当前困扰",
                "整理今日必须完成的任务清单，优先处理"
            ]
        else:
            action_plan['immediate_actions'] = [
                "记录今天的三个感恩时刻",
                "进行30分钟喜欢的运动",
                "阅读15分钟有益心理健康的书籍或文章"
            ]
        
        # 短期目标
        if 'work' in concerns:
            action_plan['short_term_goals'].append("本周内与上级沟通工作压力问题")
        if 'relationship' in concerns:
            action_plan['short_term_goals'].append("安排一次深度的朋友或家人交流")
        
        action_plan['short_term_goals'].extend([
            "建立每周固定的情绪记录习惯",
            "尝试两种新的放松技巧并评估效果"
        ])
        
        # 长期目标
        action_plan['long_term_objectives'] = [
            "培养稳定的运动习惯（每周3-4次）",
            "发展一项创造性爱好",
            "建立可靠的社交支持网络"
        ]
        
        return action_plan
    
    def _get_immediate_interventions(self, current_state: Dict[str, Any]) -> List[str]:
        """获取紧急干预措施"""
        interventions = []
        
        stress_level = current_state.get('stress_level', 'moderate')
        
        if stress_level == 'high':
            interventions = self.intervention_strategies['immediate_relief'][:2]
        else:
            interventions = ["继续保持当前的良好状态", "适时进行放松调节"]
        
        return interventions
    
    def _compile_resources(self, current_state: Dict[str, Any]) -> Dict[str, List[str]]:
        """整理相关资源推荐"""
        resources = {
            'apps_tools': [],
            'books_articles': [],
            'professional_help': [],
            'online_communities': []
        }
        
        concerns = current_state.get('primary_concerns', [])
        stress_level = current_state.get('stress_level', 'moderate')
        
        # 根据关注领域推荐资源
        if 'work' in concerns:
            resources['apps_tools'].append("番茄工作法时间管理工具")
            resources['books_articles'].append("《深度工作》- Cal Newport")
        
        if 'relationship' in concerns:
            resources['books_articles'].append("《亲密关系》- 罗兰·米勒")
            resources['online_communities'].append("豆瓣情感互助小组")
        
        # 根据压力水平推荐
        if stress_level == 'high':
            resources['professional_help'].append("建议预约心理咨询师")
            resources['apps_tools'].append("Headspace冥想APP")
        
        resources['apps_tools'].append("情绪追踪日记APP")
        resources['books_articles'].append("《情绪急救》- Guy Winch")
        
        return resources

# 使用示例
if __name__ == "__main__":
    engine = RecommendationEngine()
    
    # 模拟用户数据
    sample_emotion_history = [
        {'timestamp': '2024-01-01T10:00:00', 'emotion_score': 0.8},
        {'timestamp': '2024-01-02T10:00:00', 'emotion_score': 0.6},
        {'timestamp': '2024-01-03T10:00:00', 'emotion_score': 0.4}
    ]
    
    sample_personality = {
        'personality_traits': {
            'neuroticism': {'score': 75},
            'openness': {'score': 80},
            'agreeableness': {'score': 45}
        }
    }
    
    sample_conversations = [
        {'content': '最近工作压力很大，经常失眠'},
        {'content': '和同事关系有点紧张'}
    ]
    
    # 生成建议报告
    report = engine.generate_personalized_recommendations(
        'user_001', 
        sample_emotion_history, 
        sample_personality, 
        sample_conversations
    )
    
    print("个性化建议报告生成完成")
    print(json.dumps(report, ensure_ascii=False, indent=2))