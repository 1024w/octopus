import praw
import datetime
import hashlib
import json
from app.collectors.base_collector import BaseCollector
from app.models import db
from app.models.message import Message
from app.utils.logging import get_logger

logger = get_logger("collectors.reddit")

class RedditCollector(BaseCollector):
    """Reddit数据采集器"""
    
    def __init__(self, client_id=None, client_secret=None, user_agent=None):
        """
        初始化Reddit采集器
        
        Args:
            client_id: Reddit API客户端ID，可选
            client_secret: Reddit API客户端密钥，可选
            user_agent: 用户代理，可选
        """
        super().__init__()
        
        from flask import current_app
        
        self.client_id = client_id or current_app.config.get('REDDIT_CLIENT_ID')
        self.client_secret = client_secret or current_app.config.get('REDDIT_CLIENT_SECRET')
        self.user_agent = user_agent or current_app.config.get('REDDIT_USER_AGENT', 'octopus:v1.0')
        
        # 初始化API客户端
        self.reddit = praw.Reddit(
            client_id=self.client_id,
            client_secret=self.client_secret,
            user_agent=self.user_agent
        )
        
        logger.info("Reddit collector initialized")
    
    def _get_collector_type(self):
        """获取采集器类型"""
        return 'reddit'
    
    def collect_subreddit_posts(self, subreddit_name, limit=100, time_filter='day'):
        """
        采集子版块帖子
        
        Args:
            subreddit_name: 子版块名称
            limit: 采集数量限制
            time_filter: 时间过滤器，'hour', 'day', 'week', 'month', 'year', 'all'
            
        Returns:
            采集的帖子列表和子版块信息
        """
        logger.info(f"Collecting posts from subreddit: {subreddit_name}, limit: {limit}")
        
        try:
            # 获取子版块
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # 获取热门帖子
            posts = list(subreddit.hot(limit=limit))
            
            logger.info(f"Collected {len(posts)} posts from subreddit {subreddit_name}")
            return {
                'posts': posts, 
                'subreddit': subreddit, 
                'source_name': f"r/{subreddit_name}", 
                'type': 'subreddit'
            }
        
        except Exception as e:
            logger.error(f"Error collecting posts from subreddit {subreddit_name}: {str(e)}")
            return {
                'posts': [], 
                'subreddit': None, 
                'source_name': f"r/{subreddit_name}", 
                'type': 'subreddit'
            }
    
    def collect_search_posts(self, query, limit=100, sort='relevance', time_filter='all'):
        """
        采集搜索结果
        
        Args:
            query: 搜索关键词
            limit: 采集数量限制
            sort: 排序方式，'relevance', 'hot', 'top', 'new', 'comments'
            time_filter: 时间过滤器，'hour', 'day', 'week', 'month', 'year', 'all'
            
        Returns:
            采集的帖子列表
        """
        logger.info(f"Collecting posts for search: {query}, limit: {limit}")
        
        try:
            # 搜索帖子
            posts = list(self.reddit.subreddit('all').search(
                query=query,
                sort=sort,
                time_filter=time_filter,
                limit=limit
            ))
            
            logger.info(f"Collected {len(posts)} posts for search '{query}'")
            return {
                'posts': posts, 
                'source_name': f"search:{query}", 
                'type': 'search', 
                'query': query
            }
        
        except Exception as e:
            logger.error(f"Error collecting posts for search '{query}': {str(e)}")
            return {
                'posts': [], 
                'source_name': f"search:{query}", 
                'type': 'search', 
                'query': query
            }
    
    def collect_data(self, config):
        """
        采集数据
        
        Args:
            config: 采集配置
            
        Returns:
            采集的原始数据
        """
        results = []
        
        # 处理子版块采集
        if 'subreddits' in config:
            for subreddit in config['subreddits']:
                result = self.collect_subreddit_posts(
                    subreddit_name=subreddit.get('name'),
                    limit=subreddit.get('limit', 100),
                    time_filter=subreddit.get('time_filter', 'day')
                )
                results.append(result)
        
        # 处理搜索采集
        if 'searches' in config:
            for search in config['searches']:
                result = self.collect_search_posts(
                    query=search.get('query'),
                    limit=search.get('limit', 100),
                    sort=search.get('sort', 'relevance'),
                    time_filter=search.get('time_filter', 'all')
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
            posts = data.get('posts', [])
            data_source_name = data.get('source_name') or source_name
            
            for post in posts:
                # 跳过空内容
                if not post.selftext and not post.title:
                    continue
                
                # 组合内容
                content = f"{post.title}\n\n{post.selftext}"
                
                # 生成内容哈希，用于去重
                content_hash = hashlib.md5(content.encode()).hexdigest()
                
                # 创建消息对象
                message = Message(
                    platform='reddit',
                    source_id=post.id,
                    source_name=data_source_name,
                    content=content,
                    content_hash=content_hash,
                    timestamp=datetime.datetime.fromtimestamp(post.created_utc),
                    author_id=post.author.name if post.author else '[deleted]',
                    author_name=post.author.name if post.author else '[deleted]',
                    author_followers=0,  # Reddit不直接提供关注者数量
                    metadata=json.dumps({
                        'score': post.score,
                        'upvote_ratio': post.upvote_ratio,
                        'num_comments': post.num_comments,
                        'is_self': post.is_self,
                        'url': post.url,
                        'permalink': post.permalink,
                        'subreddit': post.subreddit.display_name,
                        'collection_type': data.get('type'),
                        'query': data.get('query') if data.get('type') == 'search' else None
                    }),
                    collector_id=collector_id
                )
                
                messages.append(message)
                
                # 如果配置了采集评论，还可以处理帖子的评论
                
        return messages 