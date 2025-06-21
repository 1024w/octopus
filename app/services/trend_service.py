import datetime
import pandas as pd
import numpy as np
from app.models import db
from app.models.message import Message
from app.models.token import Token
from app.models.mention import Mention
from app.utils.logging import get_logger

logger = get_logger("services.trend")

class TrendService:
    """趋势分析服务，处理与趋势分析相关的业务逻辑"""
    
    def __init__(self):
        """初始化趋势分析服务"""
        logger.info("Trend service initialized")
    
    def get_mention_trends(self, token_id, days=30):
        """
        获取代币提及趋势
        
        Args:
            token_id: 代币ID
            days: 分析的天数范围
            
        Returns:
            提及趋势数据
        """
        token = Token.query.get(token_id)
        if not token:
            logger.warning(f"Token {token_id} not found")
            return None
        
        # 计算起始时间
        start_date = datetime.datetime.utcnow() - datetime.timedelta(days=days)
        
        # 获取代币提及
        mentions = db.session.query(Mention).join(Message).filter(
            Mention.token_id == token_id,
            Message.timestamp >= start_date
        ).all()
        
        if not mentions:
            logger.warning(f"No mentions found for token {token.symbol} in the last {days} days")
            return {
                'token_id': token_id,
                'symbol': token.symbol,
                'mention_count': 0,
                'trends': []
            }
        
        # 提取提及数据
        mention_data = []
        for mention in mentions:
            message = mention.message
            mention_data.append({
                'mention_id': mention.id,
                'message_id': message.id,
                'timestamp': message.timestamp,
                'date': message.timestamp.date(),
                'platform': message.platform,
                'author_followers': message.author_followers or 0,
                'confidence': mention.confidence
            })
        
        # 转换为DataFrame进行分析
        df = pd.DataFrame(mention_data)
        
        # 按日期分组
        daily_data = df.groupby('date').agg({
            'mention_id': 'count',
            'author_followers': 'sum'
        }).reset_index()
        
        # 重命名列
        daily_data.columns = ['date', 'mention_count', 'total_followers']
        
        # 计算移动平均
        if len(daily_data) > 3:
            daily_data['mention_ma3'] = daily_data['mention_count'].rolling(window=3).mean()
        else:
            daily_data['mention_ma3'] = daily_data['mention_count']
        
        # 计算平台分布
        platform_distribution = df.groupby('platform').size().to_dict()
        
        # 计算趋势变化率
        if len(daily_data) > 1:
            # 计算前一周和后一周的平均提及数
            half_point = len(daily_data) // 2
            if half_point > 0:
                first_half = daily_data['mention_count'].iloc[:half_point].mean()
                second_half = daily_data['mention_count'].iloc[half_point:].mean()
                
                if first_half > 0:
                    change_rate = (second_half - first_half) / first_half * 100
                else:
                    change_rate = float('inf') if second_half > 0 else 0
            else:
                change_rate = 0
        else:
            change_rate = 0
        
        # 转换为列表
        trends = daily_data.to_dict('records')
        
        result = {
            'token_id': token_id,
            'symbol': token.symbol,
            'mention_count': len(mentions),
            'platform_distribution': platform_distribution,
            'change_rate': float(change_rate),
            'trends': trends
        }
        
        logger.info(f"Generated mention trends for token {token.symbol}")
        return result
    
    def get_trending_tokens(self, limit=10, days=7):
        """
        获取趋势代币
        
        Args:
            limit: 返回的代币数量
            days: 分析的天数范围
            
        Returns:
            趋势代币列表
        """
        # 计算起始时间
        start_date = datetime.datetime.utcnow() - datetime.timedelta(days=days)
        
        # 获取所有有提及的代币
        tokens_with_mentions = db.session.query(
            Mention.token_id,
            db.func.count(Mention.id).label('mention_count')
        ).join(Message).filter(
            Message.timestamp >= start_date
        ).group_by(Mention.token_id).order_by(
            db.desc('mention_count')
        ).limit(limit * 2).all()  # 获取更多，以便后续过滤
        
        # 获取代币详情和趋势数据
        trending_tokens = []
        for token_id, mention_count in tokens_with_mentions:
            token = Token.query.get(token_id)
            if not token:
                continue
            
            # 获取趋势数据
            trend_data = self.get_mention_trends(token_id, days)
            if trend_data:
                trending_tokens.append({
                    'token_id': token_id,
                    'symbol': token.symbol,
                    'name': token.name,
                    'mention_count': mention_count,
                    'change_rate': trend_data['change_rate'],
                    'platform_distribution': trend_data['platform_distribution']
                })
        
        # 按变化率排序
        trending_tokens.sort(key=lambda x: x['change_rate'], reverse=True)
        
        # 返回前N个
        top_tokens = trending_tokens[:limit]
        
        logger.info(f"Generated top {len(top_tokens)} trending tokens")
        return top_tokens
    
    def get_platform_activity(self, days=7):
        """
        获取平台活动数据
        
        Args:
            days: 分析的天数范围
            
        Returns:
            平台活动数据
        """
        # 计算起始时间
        start_date = datetime.datetime.utcnow() - datetime.timedelta(days=days)
        
        # 获取消息数据
        messages = Message.query.filter(
            Message.timestamp >= start_date
        ).all()
        
        if not messages:
            logger.warning(f"No messages found in the last {days} days")
            return {
                'message_count': 0,
                'platform_distribution': {},
                'daily_activity': []
            }
        
        # 提取消息数据
        message_data = []
        for message in messages:
            message_data.append({
                'message_id': message.id,
                'timestamp': message.timestamp,
                'date': message.timestamp.date(),
                'platform': message.platform
            })
        
        # 转换为DataFrame进行分析
        df = pd.DataFrame(message_data)
        
        # 计算平台分布
        platform_distribution = df.groupby('platform').size().to_dict()
        
        # 按日期和平台分组
        daily_platform_data = df.groupby(['date', 'platform']).size().reset_index()
        daily_platform_data.columns = ['date', 'platform', 'message_count']
        
        # 按日期分组
        daily_data = df.groupby('date').size().reset_index()
        daily_data.columns = ['date', 'message_count']
        
        # 转换为列表
        daily_activity = daily_data.to_dict('records')
        platform_activity = daily_platform_data.to_dict('records')
        
        result = {
            'message_count': len(messages),
            'platform_distribution': platform_distribution,
            'daily_activity': daily_activity,
            'platform_activity': platform_activity
        }
        
        logger.info(f"Generated platform activity data for the last {days} days")
        return result
    
    def get_correlation_analysis(self, token_id, days=30):
        """
        获取代币提及与价格的相关性分析
        
        Args:
            token_id: 代币ID
            days: 分析的天数范围
            
        Returns:
            相关性分析数据
        """
        token = Token.query.get(token_id)
        if not token:
            logger.warning(f"Token {token_id} not found")
            return None
        
        # 计算起始时间
        start_date = datetime.datetime.utcnow() - datetime.timedelta(days=days)
        
        # 获取代币提及
        mentions = db.session.query(Mention).join(Message).filter(
            Mention.token_id == token_id,
            Message.timestamp >= start_date
        ).all()
        
        if not mentions:
            logger.warning(f"No mentions found for token {token.symbol} in the last {days} days")
            return {
                'token_id': token_id,
                'symbol': token.symbol,
                'correlation': 0,
                'has_price_data': False
            }
        
        # 提取提及数据
        mention_data = []
        for mention in mentions:
            message = mention.message
            mention_data.append({
                'timestamp': message.timestamp,
                'date': message.timestamp.date()
            })
        
        # 转换为DataFrame进行分析
        df_mentions = pd.DataFrame(mention_data)
        
        # 按日期分组计算提及数量
        daily_mentions = df_mentions.groupby('date').size().reset_index()
        daily_mentions.columns = ['date', 'mention_count']
        
        # 检查是否有价格数据
        if not token.price_history:
            logger.warning(f"No price history found for token {token.symbol}")
            return {
                'token_id': token_id,
                'symbol': token.symbol,
                'correlation': 0,
                'has_price_data': False
            }
        
        # 解析价格历史
        import json
        price_history = json.loads(token.price_history)
        
        # 转换为DataFrame
        price_data = []
        for date_str, price in price_history.items():
            try:
                date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                if date >= start_date.date():
                    price_data.append({
                        'date': date,
                        'price': price
                    })
            except:
                continue
        
        if not price_data:
            logger.warning(f"No valid price data found for token {token.symbol}")
            return {
                'token_id': token_id,
                'symbol': token.symbol,
                'correlation': 0,
                'has_price_data': False
            }
        
        # 转换为DataFrame
        df_prices = pd.DataFrame(price_data)
        
        # 合并提及和价格数据
        df_merged = pd.merge(daily_mentions, df_prices, on='date', how='outer').fillna(0)
        
        # 计算相关性
        correlation = df_merged['mention_count'].corr(df_merged['price'])
        
        # 计算每日变化率
        df_merged['mention_change'] = df_merged['mention_count'].pct_change().fillna(0)
        df_merged['price_change'] = df_merged['price'].pct_change().fillna(0)
        
        # 计算变化率相关性
        change_correlation = df_merged['mention_change'].corr(df_merged['price_change'])
        
        # 转换为列表
        correlation_data = df_merged.to_dict('records')
        
        result = {
            'token_id': token_id,
            'symbol': token.symbol,
            'correlation': float(correlation) if not np.isnan(correlation) else 0,
            'change_correlation': float(change_correlation) if not np.isnan(change_correlation) else 0,
            'has_price_data': True,
            'data': correlation_data
        }
        
        logger.info(f"Generated correlation analysis for token {token.symbol}: {correlation}")
        return result 