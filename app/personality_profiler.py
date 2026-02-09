"""
个性化心理画像系统
基于大五人格理论(OCEAN模型)构建用户心理特征画像
"""

import json
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict
import re

class PersonalityProfiler:
    """个性心理画像分析器"""
    
    def __init__(self):
        # 大五人格维度定义
        self.personality_traits = {
            'openness': {  # 开放性
                'keywords': ['想象', '创造', '艺术', '好奇', '探索', '新颖', '创新'],
                'positive_indicators': ['喜欢尝试', '富有创意', '开放思维'],
                'negative_indicators': ['保守', '传统', '抗拒变化']
            },
            'conscientiousness': {  # 尽责性
                'keywords': ['责任', '计划', '组织', '自律', '目标', '效率'],
                'positive_indicators': ['有条理', '负责任', '坚持不懈'],
                'negative_indicators': ['随意', '拖延', '缺乏规划']
            },
            'extraversion': {  # 外向性
                'keywords': ['社交', '活跃', '表达', '热情', '外向', '沟通'],
                'positive_indicators': ['善于交际', '充满活力', '表达力强'],
                'negative_indicators': ['内向', '安静', '独处倾向']
            },
            'agreeableness': {  # 宜人性
                'keywords': ['合作', '同情', '信任', '善良', '理解', '包容'],
                'positive_indicators': ['乐于助人', '善解人意', '团队合作'],
                'negative_indicators': ['竞争性强', '怀疑', '自我中心']
            },
            'neuroticism': {  # 神经质
                'keywords': ['焦虑', '担忧', '敏感', '情绪化', '紧张', '不安'],
                'positive_indicators': ['情绪稳定', '冷静', '抗压'],
                'negative_indicators': ['容易焦虑', '情绪波动', '压力敏感']
            }
        }
        
        # 初始化用户画像存储
        self.user_profiles = {}
        
    def analyze_personality_traits(self, conversation_history: List[Dict]) -> Dict[str, float]:
        """
        分析用户大五人格特征
        
        Args:
            conversation_history: 对话历史记录
            
        Returns:
            dict: 各人格维度得分 (0-100)
        """
        trait_scores = {}
        
        # 收集所有对话文本
        all_text = ""
        for msg in conversation_history:
            if isinstance(msg, dict) and 'content' in msg:
                all_text += str(msg['content']) + " "
            elif isinstance(msg, str):
                all_text += msg + " "
        
        # 清理文本
        cleaned_text = self._clean_text(all_text)
        
        # 分析每个维度
        for trait_name, trait_info in self.personality_traits.items():
            score = self._calculate_trait_score(cleaned_text, trait_info)
            trait_scores[trait_name] = round(score, 2)
            
        return trait_scores
    
    def _clean_text(self, text: str) -> str:
        """清理和标准化文本"""
        # 移除特殊字符，保留中文和基本标点
        cleaned = re.sub(r'[^\u4e00-\u9fff\u3400-\u4dbf\w\s，。！？；：]', '', text)
        return cleaned.lower()
    
    def _calculate_trait_score(self, text: str, trait_info: Dict) -> float:
        """
        计算特定人格特质得分
        
        使用词频统计和语义分析相结合的方法
        """
        score = 50.0  # 基准分
        
        # 关键词匹配计分
        positive_matches = 0
        negative_matches = 0
        
        # 正面指标加分
        for indicator in trait_info['positive_indicators']:
            if indicator in text:
                positive_matches += 1
                
        # 负面指标扣分  
        for indicator in trait_info['negative_indicators']:
            if indicator in text:
                negative_matches += 1
        
        # 计算基础得分调整
        base_adjustment = (positive_matches - negative_matches) * 8
        score += base_adjustment
        
        # 词汇丰富度调整（体现开放性等特质）
        unique_words = len(set(text.split()))
        vocabulary_bonus = min(unique_words * 0.5, 15)  # 词汇丰富度奖励
        score += vocabulary_bonus
        
        # 句子长度分析（体现尽责性和神经质）
        sentences = re.split(r'[。！？]', text)
        avg_sentence_length = np.mean([len(s) for s in sentences if s.strip()])
        
        if trait_info['keywords'][0] in ['责任', '焦虑']:  # 尽责性和神经质
            # 更长的句子可能体现更深思熟虑或更焦虑
            length_adjustment = (avg_sentence_length - 20) * 0.3
            score += length_adjustment
        
        # 限制在合理范围内
        return max(0, min(100, score))
    
    def generate_personality_report(self, user_id: str, trait_scores: Dict[str, float]) -> Dict[str, Any]:
        """
        生成详细的人格分析报告
        
        Args:
            user_id: 用户标识
            trait_scores: 人格特质得分
            
        Returns:
            dict: 完整的人格报告
        """
        report = {
            'user_id': user_id,
            'analysis_timestamp': datetime.now().isoformat(),
            'personality_traits': {},
            'detailed_analysis': {},
            'recommendations': []
        }
        
        # 构建各维度详细分析
        for trait_name, score in trait_scores.items():
            trait_key = trait_name
            trait_info = self.personality_traits[trait_name]
            
            # 确定水平等级
            level = self._get_trait_level(score)
            
            report['personality_traits'][trait_key] = {
                'score': score,
                'level': level,
                'percentile': self._score_to_percentile(score),
                'description': self._get_trait_description(trait_name, level)
            }
            
            # 添加详细解读
            report['detailed_analysis'][trait_key] = {
                'strengths': self._get_trait_strengths(trait_name, score),
                'challenges': self._get_trait_challenges(trait_name, score),
                'development_suggestions': self._get_development_suggestions(trait_name, score)
            }
        
        # 生成个性化建议
        report['recommendations'] = self._generate_recommendations(trait_scores)
        
        return report
    
    def _get_trait_level(self, score: float) -> str:
        """根据得分确定特质水平"""
        if score >= 80:
            return "非常高"
        elif score >= 65:
            return "较高"
        elif score >= 35:
            return "中等"
        elif score >= 20:
            return "较低"
        else:
            return "非常低"
    
    def _score_to_percentile(self, score: float) -> int:
        """将得分转换为百分位数"""
        # 简化的正态分布映射
        return int(min(99, max(1, score)))
    
    def _get_trait_description(self, trait_name: str, level: str) -> str:
        """获取特质描述"""
        descriptions = {
            'openness': {
                '非常高': '具有极强的创造力和想象力，热爱探索新事物',
                '较高': '思维开放，愿意接受新的观点和体验',
                '中等': '在传统与创新之间保持平衡',
                '较低': '偏好熟悉的事物和既定的方式',
                '非常低': '高度传统，抗拒变化'
            },
            'conscientiousness': {
                '非常高': '极其自律和有组织性，目标导向明确',
                '较高': '做事认真负责，有良好的计划性',
                '中等': '在自律和灵活性之间找到平衡',
                '较低': '相对随性，不太注重细节规划',
                '非常低': '缺乏组织性，容易拖延'
            },
            'extraversion': {
                '非常高': '极度外向，充满社交活力',
                '较高': '善于社交，在群体中表现活跃',
                '中等': '适度外向，能适应不同社交场合',
                '较低': '偏内向，更喜欢小群体或独处',
                '非常低': '高度内向，社交需求较少'
            },
            'agreeableness': {
                '非常高': '极具同理心，乐于合作和帮助他人',
                '较高': '友善合作，容易相处',
                '中等': '在坚持己见和配合他人间平衡',
                '较低': '相对独立，有时显得直接',
                '非常低': '竞争性强，较少考虑他人感受'
            },
            'neuroticism': {
                '非常高': '情绪波动较大，容易感到焦虑',
                '较高': '对压力比较敏感，情绪起伏明显',
                '中等': '有一定情绪反应，但总体稳定',
                '较低': '情绪相对稳定，抗压能力较强',
                '非常低': '非常冷静，很少被情绪困扰'
            }
        }
        
        return descriptions.get(trait_name, {}).get(level, "特征描述不可用")
    
    def _get_trait_strengths(self, trait_name: str, score: float) -> List[str]:
        """获取特质优势"""
        strengths_map = {
            'openness': ['创造性思维', '适应能力强', '学习新事物快'],
            'conscientiousness': ['执行力强', '可靠性高', '目标明确'],
            'extraversion': ['社交能力强', '表达力好', '领导潜力'],
            'agreeableness': ['人际关系和谐', '团队合作佳', '善解人意'],
            'neuroticism': ['敏感度高', '风险意识强', '注重细节']
        }
        
        base_strengths = strengths_map.get(trait_name, [])
        
        # 根据得分调整优势列表
        if score > 70:
            return base_strengths + [f'{trait_name}特质突出的优势']
        elif score < 30:
            return [f'在{trait_name}方面的独特优势']
        else:
            return base_strengths[:2]
    
    def _get_trait_challenges(self, trait_name: str, score: float) -> List[str]:
        """获取潜在挑战"""
        challenges_map = {
            'openness': ['可能过于理想化', '注意力分散', '难以坚持常规'],
            'conscientiousness': ['可能过度完美主义', '灵活性不足', '压力较大'],
            'extraversion': ['可能忽视内心需求', '过度依赖外部刺激', '独处困难'],
            'agreeableness': ['可能忽视自身需求', '避免必要冲突', '决策犹豫'],
            'neuroticism': ['情绪管理挑战', '压力应对需要改善', '过度担忧']
        }
        
        return challenges_map.get(trait_name, [])
    
    def _get_development_suggestions(self, trait_name: str, score: float) -> List[str]:
        """获取发展建议"""
        suggestions_map = {
            'openness': ['培养专注力', '平衡创新与实践', '建立稳定的routine'],
            'conscientiousness': ['适当放松标准', '学会授权', '培养灵活性'],
            'extraversion': ['发展内省能力', '享受独处时光', '培养深度思考'],
            'agreeableness': ['练习表达真实想法', '设定合理边界', '培养决断力'],
            'neuroticism': ['学习情绪调节技巧', '建立压力管理体系', '培养积极思维']
        }
        
        return suggestions_map.get(trait_name, [])
    
    def _generate_recommendations(self, trait_scores: Dict[str, float]) -> List[str]:
        """生成综合建议"""
        recommendations = []
        
        # 基于整体模式的建议
        high_traits = [k for k, v in trait_scores.items() if v > 70]
        low_traits = [k for k, v in trait_scores.items() if v < 30]
        
        if len(high_traits) >= 3:
            recommendations.append("您的个性特征较为鲜明，建议发挥优势的同时注意平衡发展")
        
        if len(low_traits) >= 3:
            recommendations.append("您展现出很好的适应性，建议在某些方面适当加强以获得更全面发展")
        
        # 特定组合建议
        if trait_scores.get('openness', 0) > 70 and trait_scores.get('conscientiousness', 0) > 70:
            recommendations.append("您的创新能力和执行力都很强，适合从事需要创造性解决问题的工作")
        
        if trait_scores.get('agreeableness', 0) > 70 and trait_scores.get('neuroticism', 0) < 30:
            recommendations.append("您具备优秀的团队合作能力和情绪稳定性，是理想的团队成员")
        
        return recommendations
    
    def save_profile(self, user_id: str, profile_data: Dict[str, Any]):
        """保存用户画像数据"""
        self.user_profiles[user_id] = {
            'last_updated': datetime.now().isoformat(),
            'profile': profile_data
        }
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户画像"""
        return self.user_profiles.get(user_id)

# 使用示例
if __name__ == "__main__":
    profiler = PersonalityProfiler()
    
    # 示例对话历史
    sample_conversation = [
        {"role": "user", "content": "我最近总是觉得很焦虑，担心工作做不好"},
        {"role": "assistant", "content": "能具体说说是什么让您感到焦虑吗？"},
        {"role": "user", "content": "我喜欢尝试新的方法解决问题，但有时候会担心失败"},
        {"role": "assistant", "content": "您的创新精神很可贵，适度的担心也是正常的"}
    ]
    
    # 分析人格特质
    traits = profiler.analyze_personality_traits(sample_conversation)
    print("人格特质分析结果:")
    for trait, score in traits.items():
        print(f"{trait}: {score}")
    
    # 生成完整报告
    report = profiler.generate_personality_report("user_001", traits)
    print("\n完整人格报告已生成")