import tweepy
import datetime
import hashlib
import json
from app.collectors.base_collector import BaseCollector
from app.models import db
from app.models.message import Message
from app.utils.logging import get_logger

logger = get_logger("collectors.twitter")

class TwitterCollector(BaseCollector):
    """Twitter数据采集器"""
    
    def __init__(self, api_key=None, api_secret=None, access_token=None, access_secret=None):
        """
        初始化Twitter采集器
        
        Args:
            api_key: Twitter API密钥，可选
            api_secret: Twitter API密钥，可选
            access_token: Twitter访问令牌，可选
            access_secret: Twitter访问密钥，可选
        """
        super().__init__()
        
        from flask import current_app
        
        self.api_key = api_key or current_app.config.get('TWITTER_API_KEY')
        self.api_secret = api_secret or current_app.config.get('TWITTER_API_SECRET')
        self.access_token = access_token or current_app.config.get('TWITTER_ACCESS_TOKEN')
        self.access_secret = access_secret or current_app.config.get('TWITTER_ACCESS_SECRET')
        
        # 初始化API客户端
        auth = tweepy.OAuth1UserHandler(
            self.api_key, self.api_secret,
            self.access_token, self.access_secret
        )
        self.api = tweepy.API(auth)
        
        logger.info("Twitter collector initialized")
    
    def _get_collector_type(self):
        """获取采集器类型"""
        return 'twitter'
    
    def collect_user_tweets(self, username, count=100, since_id=None):
        """
        采集用户推文
        
        Args:
            username: Twitter用户名
            count: 采集数量
            since_id: 起始推文ID
            
        Returns:
            采集的推文列表和用户信息
        """
        logger.info(f"Collecting tweets from user: {username}, count: {count}")
        
        try:
            # 获取用户信息
            user = self.api.get_user(screen_name=username)
            
            # 获取用户推文
            tweets = self.api.user_timeline(
                screen_name=username,
                count=count,
                since_id=since_id,
                tweet_mode='extended'
            )
            
            logger.info(f"Collected {len(tweets)} tweets from user {username}")
            return {'tweets': tweets, 'user': user, 'source_name': username, 'type': 'user'}
        
        except tweepy.TweepyException as e:
            logger.error(f"Error collecting tweets from user {username}: {str(e)}")
            return {'tweets': [], 'user': None, 'source_name': username, 'type': 'user'}
    
    def collect_search_tweets(self, query, count=100, result_type='recent', lang=None):
        """
        采集搜索结果
        
        Args:
            query: 搜索关键词
            count: 采集数量
            result_type: 结果类型，'recent', 'popular', 'mixed'
            lang: 语言过滤
            
        Returns:
            采集的推文列表
        """
        logger.info(f"Collecting tweets for search: {query}, count: {count}")
        
        try:
            # 搜索推文
            tweets = self.api.search_tweets(
                q=query,
                count=count,
                result_type=result_type,
                lang=lang,
                tweet_mode='extended'
            )
            
            logger.info(f"Collected {len(tweets)} tweets for search '{query}'")
            return {'tweets': tweets, 'source_name': f"search:{query}", 'type': 'search', 'query': query}
        
        except tweepy.TweepyException as e:
            logger.error(f"Error collecting tweets for search '{query}': {str(e)}")
            return {'tweets': [], 'source_name': f"search:{query}", 'type': 'search', 'query': query}
    
    def collect_data(self, config):
        """
        采集数据
        
        Args:
            config: 采集配置
            
        Returns:
            采集的原始数据
        """
        results = []
        
        # 处理用户采集
        if 'users' in config:
            for user in config['users']:
                result = self.collect_user_tweets(
                    username=user.get('username'),
                    count=user.get('count', 100),
                    since_id=user.get('since_id')
                )
                
                # 更新since_id
                if result['tweets'] and len(result['tweets']) > 0:
                    for i, u in enumerate(config['users']):
                        if u.get('username') == user.get('username'):
                            config['users'][i]['since_id'] = str(result['tweets'][0].id)
                
                results.append(result)
        
        # 处理搜索采集
        if 'searches' in config:
            for search in config['searches']:
                result = self.collect_search_tweets(
                    query=search.get('query'),
                    count=search.get('count', 100),
                    result_type=search.get('result_type', 'recent'),
                    lang=search.get('lang')
                )
                results.append(result)
        
        return results
    
    def standardize_message(self, raw_data, collector_id=None, source_name=None):
        """
        将原始数据标准化为统一格式
        
        Args:
            raw_data: 原始数据
            collector_id: 采集器ID
            source_name: 来源名称，可选
            
        Returns:
            标准化后的消息对象列表
        """
        messages = []
        
        for data in raw_data:
            tweets = data.get('tweets', [])
            data_source_name = data.get('source_name') or source_name
            
            for tweet in tweets:
                # 生成内容哈希，用于去重
                content_hash = hashlib.md5(tweet.full_text.encode()).hexdigest()
                
                # 创建消息对象
                message = Message(
                    platform='twitter',
                    source_id=str(tweet.id),
                    source_name=data_source_name,
                    content=tweet.full_text,
                    content_hash=content_hash,
                    timestamp=tweet.created_at,
                    author_id=str(tweet.user.id),
                    author_name=tweet.user.screen_name,
                    author_followers=tweet.user.followers_count,
                    metadata=json.dumps({
                        'retweet_count': tweet.retweet_count,
                        'favorite_count': tweet.favorite_count,
                        'is_retweet': hasattr(tweet, 'retweeted_status'),
                        'hashtags': [h['text'] for h in tweet.entities.get('hashtags', [])],
                        'urls': [u['expanded_url'] for u in tweet.entities.get('urls', [])],
                        'user_mentions': [m['screen_name'] for m in tweet.entities.get('user_mentions', [])],
                        'profile_image': tweet.user.profile_image_url_https,
                        'collection_type': data.get('type'),
                        'query': data.get('query') if data.get('type') == 'search' else None
                    }),
                    collector_id=collector_id
                )
                
                messages.append(message)
        
        return messages
    
    def save_tweets_to_db(self, tweets, collector_id=None, source_name=None):
        """
        将推文保存到数据库
        
        Args:
            tweets: 推文列表
            collector_id: 采集器ID
            source_name: 来源名称
            
        Returns:
            保存的消息数量
        """
        saved_count = 0
        
        for tweet in tweets:
            # 生成内容哈希，用于去重
            content_hash = hashlib.md5(tweet.full_text.encode()).hexdigest()
            
            # 检查是否已存在
            existing = Message.query.filter_by(content_hash=content_hash).first()
            if existing:
                continue
            
            # 创建消息对象
            message = Message(
                platform='twitter',
                source_id=str(tweet.id),
                source_name=source_name or tweet.user.screen_name,
                content=tweet.full_text,
                content_hash=content_hash,
                timestamp=tweet.created_at,
                author_id=str(tweet.user.id),
                author_name=tweet.user.screen_name,
                author_followers=tweet.user.followers_count,
                metadata=json.dumps({
                    'retweet_count': tweet.retweet_count,
                    'favorite_count': tweet.favorite_count,
                    'is_retweet': hasattr(tweet, 'retweeted_status'),
                    'hashtags': [h['text'] for h in tweet.entities.get('hashtags', [])],
                    'urls': [u['expanded_url'] for u in tweet.entities.get('urls', [])],
                    'user_mentions': [m['screen_name'] for m in tweet.entities.get('user_mentions', [])],
                    'profile_image': tweet.user.profile_image_url_https
                }),
                collector_id=collector_id
            )
            
            db.session.add(message)
            saved_count += 1
        
        if saved_count > 0:
            db.session.commit()
            logger.info(f"Saved {saved_count} new tweets to database")
        
        return saved_count
    
    def run_collector(self, collector_id):
        """
        运行采集器
        
        Args:
            collector_id: 采集器ID
            
        Returns:
            采集的消息数量
        """
        # 获取采集器配置
        collector = Collector.query.get(collector_id)
        if not collector:
            logger.error(f"Collector {collector_id} not found")
            return 0
        
        if collector.collector_type != 'twitter':
            logger.error(f"Collector {collector_id} is not a Twitter collector")
            return 0
        
        # 解析配置
        try:
            config = json.loads(collector.config)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON config for collector {collector_id}")
            return 0
        
        # 更新采集器状态
        collector.last_run_at = datetime.datetime.utcnow()
        collector.last_run_status = 'running'
        db.session.commit()
        
        total_saved = 0
        
        try:
            # 处理用户采集
            if 'users' in config:
                for user in config['users']:
                    tweets, user_info = self.collect_user_tweets(
                        username=user.get('username'),
                        count=user.get('count', 100),
                        since_id=user.get('since_id')
                    )
                    saved = self.save_tweets_to_db(tweets, collector_id, user.get('username'))
                    total_saved += saved
                    
                    # 更新since_id
                    if tweets and 'users' in config:
                        for i, u in enumerate(config['users']):
                            if u.get('username') == user.get('username'):
                                config['users'][i]['since_id'] = str(tweets[0].id)
            
            # 处理搜索采集
            if 'searches' in config:
                for search in config['searches']:
                    tweets = self.collect_search_tweets(
                        query=search.get('query'),
                        count=search.get('count', 100),
                        result_type=search.get('result_type', 'recent'),
                        lang=search.get('lang')
                    )
                    saved = self.save_tweets_to_db(tweets, collector_id, f"search:{search.get('query')}")
                    total_saved += saved
            
            # 更新采集器配置
            collector.config = json.dumps(config)
            collector.last_run_status = 'success'
            collector.last_run_message = f"Collected {total_saved} new tweets"
            
        except Exception as e:
            logger.exception(f"Error running Twitter collector {collector_id}: {str(e)}")
            collector.last_run_status = 'failure'
            collector.last_run_message = f"Error: {str(e)}"
        
        db.session.commit()
        return total_saved 