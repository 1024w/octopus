import datetime
import pandas as pd
import numpy as np
from textblob import TextBlob
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from app.models import db
from app.models.message import Message
from app.models.token import Token
from app.models.mention import Mention
from app.utils.logging import get_logger

logger = get_logger("services.sentiment")

class SentimentService:
    """情感分析服务，处理与情感分析相关的业务逻辑"""
    
    def __init__(self):
        """初始化情感分析服务"""
        try:
            import nltk
            nltk.download('vader_lexicon', quiet=True)
            self.vader = SentimentIntensityAnalyzer()
            logger.info("VADER sentiment analyzer initialized")
        except Exception as e:
            logger.error(f"Error initializing VADER sentiment analyzer: {str(e)}")
            self.vader = None
        
        logger.info("Sentiment service initialized")
    
    def analyze_text(self, text, lang='en'):
        """
        分析文本情感
        
        Args:
            text: 待分析文本
            lang: 语言，'en'或'zh'
            
        Returns:
            情感分析结果，包含极性和主观性
        """
        if not text:
            return {'polarity': 0, 'subjectivity': 0, 'compound': 0}
        
        result = {}
        
        # 使用TextBlob进行情感分析
        blob = TextBlob(text)
        result['polarity'] = blob.sentiment.polarity
        result['subjectivity'] = blob.sentiment.subjectivity
        
        # 使用VADER进行情感分析（仅英文）
        if lang == 'en' and self.vader:
            vader_scores = self.vader.polarity_scores(text)
            result.update(vader_scores)
        
        return result
    
    def analyze_message(self, message_id):
        """
        分析消息情感
        
        Args:
            message_id: 消息ID
            
        Returns:
            情感分析结果
        """
        message = Message.query.get(message_id)
        if not message:
            logger.warning(f"Message {message_id} not found")
            return None
        
        # 检测语言
        lang = 'en'  # 默认英文
        if any('\u4e00' <= c <= '\u9fff' for c in message.content):
            lang = 'zh'  # 简单检测中文
        
        # 分析情感
        sentiment = self.analyze_text(message.content, lang)
        
        # 更新消息元数据
        import json
        metadata = json.loads(message.metadata) if message.metadata else {}
        metadata['sentiment'] = sentiment
        message.metadata = json.dumps(metadata)
        
        db.session.commit()
        
        logger.info(f"Analyzed sentiment for message {message_id}: {sentiment['polarity']}")
        return sentiment
    
    def analyze_token_mentions(self, token_id, days=7):
        """
        分析代币提及的情感
        
        Args:
            token_id: 代币ID
            days: 分析的天数范围
            
        Returns:
            情感分析结果
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
                'average_sentiment': 0,
                'sentiment_distribution': {'positive': 0, 'neutral': 0, 'negative': 0}
            }
        
        # 分析每个提及的情感
        sentiments = []
        for mention in mentions:
            message = mention.message
            
            # 检查消息元数据中是否已有情感分析结果
            import json
            metadata = json.loads(message.metadata) if message.metadata else {}
            
            if 'sentiment' in metadata:
                sentiment = metadata['sentiment']
            else:
                # 分析情感
                sentiment = self.analyze_message(message.id)
            
            if sentiment:
                sentiments.append({
                    'message_id': message.id,
                    'timestamp': message.timestamp,
                    'polarity': sentiment.get('polarity', 0),
                    'compound': sentiment.get('compound', sentiment.get('polarity', 0)),
                    'author_followers': message.author_followers or 0
                })
        
        # 计算加权平均情感
        if sentiments:
            df = pd.DataFrame(sentiments)
            
            # 使用作者粉丝数作为权重
            weights = df['author_followers'] + 1  # 加1避免0权重
            average_sentiment = np.average(df['compound'], weights=weights)
            
            # 情感分布
            positive = len(df[df['compound'] > 0.05])
            neutral = len(df[(df['compound'] >= -0.05) & (df['compound'] <= 0.05)])
            negative = len(df[df['compound'] < -0.05])
            
            # 按日期分组计算每日情感
            df['date'] = df['timestamp'].dt.date
            daily_sentiment = df.groupby('date')['compound'].mean().to_dict()
            
            result = {
                'token_id': token_id,
                'symbol': token.symbol,
                'mention_count': len(mentions),
                'average_sentiment': float(average_sentiment),
                'sentiment_distribution': {
                    'positive': positive,
                    'neutral': neutral,
                    'negative': negative
                },
                'daily_sentiment': daily_sentiment
            }
            
            logger.info(f"Analyzed sentiment for token {token.symbol}: {average_sentiment}")
            return result
        
        return None
    
    def get_token_sentiment_trends(self, token_id, days=30):
        """
        获取代币情感趋势
        
        Args:
            token_id: 代币ID
            days: 分析的天数范围
            
        Returns:
            情感趋势数据
        """
        token = Token.query.get(token_id)
        if not token:
            logger.warning(f"Token {token_id} not found")
            return None
        
        # 计算起始时间
        start_date = datetime.datetime.utcnow() - datetime.timedelta(days=days)
        
        # 获取代币提及的消息
        messages = db.session.query(Message).join(Mention).filter(
            Mention.token_id == token_id,
            Message.timestamp >= start_date
        ).all()
        
        if not messages:
            logger.warning(f"No messages found for token {token.symbol} in the last {days} days")
            return {
                'token_id': token_id,
                'symbol': token.symbol,
                'message_count': 0,
                'trends': []
            }
        
        # 分析每个消息的情感
        message_data = []
        for message in messages:
            # 检查消息元数据中是否已有情感分析结果
            import json
            metadata = json.loads(message.metadata) if message.metadata else {}
            
            if 'sentiment' in metadata:
                sentiment = metadata['sentiment']
            else:
                # 分析情感
                sentiment = self.analyze_message(message.id)
            
            if sentiment:
                message_data.append({
                    'message_id': message.id,
                    'timestamp': message.timestamp,
                    'date': message.timestamp.date(),
                    'polarity': sentiment.get('polarity', 0),
                    'compound': sentiment.get('compound', sentiment.get('polarity', 0)),
                    'platform': message.platform,
                    'author_followers': message.author_followers or 0
                })
        
        # 转换为DataFrame进行分析
        df = pd.DataFrame(message_data)
        
        # 按日期分组
        daily_data = df.groupby('date').agg({
            'message_id': 'count',
            'compound': 'mean',
            'author_followers': 'sum'
        }).reset_index()
        
        # 重命名列
        daily_data.columns = ['date', 'message_count', 'sentiment', 'total_followers']
        
        # 计算移动平均
        if len(daily_data) > 3:
            daily_data['sentiment_ma3'] = daily_data['sentiment'].rolling(window=3).mean()
        else:
            daily_data['sentiment_ma3'] = daily_data['sentiment']
        
        # 转换为列表
        trends = daily_data.to_dict('records')
        
        # 计算总体情感
        weighted_sentiment = np.average(df['compound'], weights=df['author_followers'] + 1)
        
        result = {
            'token_id': token_id,
            'symbol': token.symbol,
            'message_count': len(messages),
            'overall_sentiment': float(weighted_sentiment),
            'trends': trends
        }
        
        logger.info(f"Generated sentiment trends for token {token.symbol}")
        return result
    
    def get_top_sentiment_tokens(self, limit=10, days=7):
        """
        获取情感最积极的代币
        
        Args:
            limit: 返回的代币数量
            days: 分析的天数范围
            
        Returns:
            情感最积极的代币列表
        """
        # 计算起始时间
        start_date = datetime.datetime.utcnow() - datetime.timedelta(days=days)
        
        # 获取所有有提及的代币
        token_ids = db.session.query(Mention.token_id).join(Message).filter(
            Message.timestamp >= start_date
        ).group_by(Mention.token_id).having(db.func.count(Mention.id) > 5).all()
        
        token_ids = [t[0] for t in token_ids]
        
        # 分析每个代币的情感
        token_sentiments = []
        for token_id in token_ids:
            sentiment_data = self.analyze_token_mentions(token_id, days)
            if sentiment_data and sentiment_data['mention_count'] > 0:
                token_sentiments.append({
                    'token_id': token_id,
                    'symbol': sentiment_data['symbol'],
                    'mention_count': sentiment_data['mention_count'],
                    'sentiment': sentiment_data['average_sentiment']
                })
        
        # 按情感排序
        token_sentiments.sort(key=lambda x: x['sentiment'], reverse=True)
        
        # 返回前N个
        top_tokens = token_sentiments[:limit]
        
        logger.info(f"Generated top {len(top_tokens)} sentiment tokens")
        return top_tokens 