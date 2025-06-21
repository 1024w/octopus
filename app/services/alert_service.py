import datetime
import json
from app.models import db
from app.models.alert import Alert
from app.models.token import Token
from app.models.user import User
from app.utils.logging import get_logger
from app.utils.notification import send_email, send_telegram_message

logger = get_logger("services.alert")

class AlertService:
    """警报服务，处理与监控和警报相关的业务逻辑"""
    
    def __init__(self):
        """初始化警报服务"""
        logger.info("Alert service initialized")
    
    def get_alerts(self, user_id=None, is_active=None, page=1, per_page=20):
        """
        获取警报列表
        
        Args:
            user_id: 用户ID，可选，如果提供则只返回该用户的警报
            is_active: 是否激活，可选，如果提供则只返回激活/未激活的警报
            page: 页码，默认1
            per_page: 每页数量，默认20
            
        Returns:
            警报列表
        """
        query = Alert.query
        
        if user_id is not None:
            query = query.filter_by(user_id=user_id)
        
        if is_active is not None:
            query = query.filter_by(is_active=is_active)
        
        # 分页
        paginated = query.order_by(Alert.created_at.desc()).paginate(page=page, per_page=per_page)
        
        return paginated.items
    
    def get_alert_by_id(self, alert_id):
        """
        根据ID获取警报
        
        Args:
            alert_id: 警报ID
            
        Returns:
            警报对象，如果不存在则返回None
        """
        return Alert.query.get(alert_id)
    
    def create_alert(self, user_id, token_id, alert_type, threshold, notification_type, notification_target):
        """
        创建新警报
        
        Args:
            user_id: 用户ID
            token_id: 代币ID
            alert_type: 警报类型，'price', 'sentiment', 'mention'
            threshold: 阈值
            notification_type: 通知类型，'email', 'telegram'
            notification_target: 通知目标，邮箱或Telegram ID
            
        Returns:
            新创建的警报对象
            
        Raises:
            ValueError: 如果参数无效
        """
        # 验证用户
        user = User.query.get(user_id)
        if not user:
            logger.error(f"User {user_id} not found")
            raise ValueError(f"User {user_id} not found")
        
        # 验证代币
        token = Token.query.get(token_id)
        if not token:
            logger.error(f"Token {token_id} not found")
            raise ValueError(f"Token {token_id} not found")
        
        # 验证警报类型
        valid_alert_types = ['price', 'sentiment', 'mention']
        if alert_type not in valid_alert_types:
            logger.error(f"Invalid alert type: {alert_type}")
            raise ValueError(f"Invalid alert type. Must be one of: {', '.join(valid_alert_types)}")
        
        # 验证通知类型
        valid_notification_types = ['email', 'telegram']
        if notification_type not in valid_notification_types:
            logger.error(f"Invalid notification type: {notification_type}")
            raise ValueError(f"Invalid notification type. Must be one of: {', '.join(valid_notification_types)}")
        
        # 创建警报
        alert = Alert(
            user_id=user_id,
            token_id=token_id,
            alert_type=alert_type,
            threshold=threshold,
            notification_type=notification_type,
            notification_target=notification_target,
            is_active=True,
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow()
        )
        
        db.session.add(alert)
        db.session.commit()
        
        logger.info(f"Created alert for user {user_id}, token {token.symbol}, type {alert_type}")
        return alert
    
    def update_alert(self, alert_id, threshold=None, notification_type=None, notification_target=None, is_active=None):
        """
        更新警报
        
        Args:
            alert_id: 警报ID
            threshold: 新阈值，可选
            notification_type: 新通知类型，可选
            notification_target: 新通知目标，可选
            is_active: 是否激活，可选
            
        Returns:
            更新后的警报对象
            
        Raises:
            ValueError: 如果警报不存在或参数无效
        """
        alert = Alert.query.get(alert_id)
        if not alert:
            logger.error(f"Alert {alert_id} not found")
            raise ValueError(f"Alert {alert_id} not found")
        
        if threshold is not None:
            alert.threshold = threshold
        
        if notification_type is not None:
            # 验证通知类型
            valid_notification_types = ['email', 'telegram']
            if notification_type not in valid_notification_types:
                logger.error(f"Invalid notification type: {notification_type}")
                raise ValueError(f"Invalid notification type. Must be one of: {', '.join(valid_notification_types)}")
            alert.notification_type = notification_type
        
        if notification_target is not None:
            alert.notification_target = notification_target
        
        if is_active is not None:
            alert.is_active = is_active
        
        alert.updated_at = datetime.datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Updated alert {alert_id}")
        return alert
    
    def delete_alert(self, alert_id):
        """
        删除警报
        
        Args:
            alert_id: 警报ID
            
        Returns:
            是否成功删除
            
        Raises:
            ValueError: 如果警报不存在
        """
        alert = Alert.query.get(alert_id)
        if not alert:
            logger.error(f"Alert {alert_id} not found")
            raise ValueError(f"Alert {alert_id} not found")
        
        db.session.delete(alert)
        db.session.commit()
        
        logger.info(f"Deleted alert {alert_id}")
        return True
    
    def check_price_alerts(self):
        """
        检查价格警报
        
        Returns:
            触发的警报数量
        """
        # 获取所有激活的价格警报
        price_alerts = Alert.query.filter_by(alert_type='price', is_active=True).all()
        
        triggered_count = 0
        
        for alert in price_alerts:
            token = Token.query.get(alert.token_id)
            if not token or not token.price:
                continue
            
            # 解析阈值
            try:
                threshold = float(alert.threshold)
            except:
                logger.warning(f"Invalid threshold for alert {alert.id}: {alert.threshold}")
                continue
            
            # 检查价格是否达到阈值
            if token.price >= threshold:
                # 触发警报
                self._trigger_alert(alert, {
                    'token_symbol': token.symbol,
                    'token_name': token.name,
                    'current_price': token.price,
                    'threshold': threshold
                })
                
                # 更新警报状态
                alert.last_triggered_at = datetime.datetime.utcnow()
                db.session.commit()
                
                triggered_count += 1
        
        logger.info(f"Checked {len(price_alerts)} price alerts, triggered {triggered_count}")
        return triggered_count
    
    def check_sentiment_alerts(self):
        """
        检查情感警报
        
        Returns:
            触发的警报数量
        """
        # 获取所有激活的情感警报
        sentiment_alerts = Alert.query.filter_by(alert_type='sentiment', is_active=True).all()
        
        triggered_count = 0
        
        for alert in sentiment_alerts:
            token = Token.query.get(alert.token_id)
            if not token:
                continue
            
            # 获取代币情感数据
            from app.services.sentiment_service import SentimentService
            sentiment_service = SentimentService()
            sentiment_data = sentiment_service.analyze_token_mentions(token.id, days=1)
            
            if not sentiment_data or 'average_sentiment' not in sentiment_data:
                continue
            
            # 解析阈值
            try:
                threshold = float(alert.threshold)
            except:
                logger.warning(f"Invalid threshold for alert {alert.id}: {alert.threshold}")
                continue
            
            # 检查情感是否达到阈值
            current_sentiment = sentiment_data['average_sentiment']
            if current_sentiment >= threshold:
                # 触发警报
                self._trigger_alert(alert, {
                    'token_symbol': token.symbol,
                    'token_name': token.name,
                    'current_sentiment': current_sentiment,
                    'threshold': threshold
                })
                
                # 更新警报状态
                alert.last_triggered_at = datetime.datetime.utcnow()
                db.session.commit()
                
                triggered_count += 1
        
        logger.info(f"Checked {len(sentiment_alerts)} sentiment alerts, triggered {triggered_count}")
        return triggered_count
    
    def check_mention_alerts(self):
        """
        检查提及警报
        
        Returns:
            触发的警报数量
        """
        # 获取所有激活的提及警报
        mention_alerts = Alert.query.filter_by(alert_type='mention', is_active=True).all()
        
        triggered_count = 0
        
        for alert in mention_alerts:
            token = Token.query.get(alert.token_id)
            if not token:
                continue
            
            # 获取代币提及数据
            from app.services.trend_service import TrendService
            trend_service = TrendService()
            trend_data = trend_service.get_mention_trends(token.id, days=1)
            
            if not trend_data or 'mention_count' not in trend_data:
                continue
            
            # 解析阈值
            try:
                threshold = int(alert.threshold)
            except:
                logger.warning(f"Invalid threshold for alert {alert.id}: {alert.threshold}")
                continue
            
            # 检查提及数量是否达到阈值
            current_mentions = trend_data['mention_count']
            if current_mentions >= threshold:
                # 触发警报
                self._trigger_alert(alert, {
                    'token_symbol': token.symbol,
                    'token_name': token.name,
                    'current_mentions': current_mentions,
                    'threshold': threshold
                })
                
                # 更新警报状态
                alert.last_triggered_at = datetime.datetime.utcnow()
                db.session.commit()
                
                triggered_count += 1
        
        logger.info(f"Checked {len(mention_alerts)} mention alerts, triggered {triggered_count}")
        return triggered_count
    
    def _trigger_alert(self, alert, data):
        """
        触发警报
        
        Args:
            alert: 警报对象
            data: 警报数据
        """
        try:
            # 根据警报类型生成消息
            if alert.alert_type == 'price':
                subject = f"价格警报: {data['token_symbol']} 已达到 {data['current_price']} USD"
                message = f"您关注的代币 {data['token_symbol']} ({data['token_name']}) 价格已达到 {data['current_price']} USD，超过您设置的阈值 {data['threshold']} USD。"
            
            elif alert.alert_type == 'sentiment':
                subject = f"情感警报: {data['token_symbol']} 情感分数已达到 {data['current_sentiment']}"
                message = f"您关注的代币 {data['token_symbol']} ({data['token_name']}) 情感分数已达到 {data['current_sentiment']}，超过您设置的阈值 {data['threshold']}。"
            
            elif alert.alert_type == 'mention':
                subject = f"提及警报: {data['token_symbol']} 提及数量已达到 {data['current_mentions']}"
                message = f"您关注的代币 {data['token_symbol']} ({data['token_name']}) 提及数量已达到 {data['current_mentions']}，超过您设置的阈值 {data['threshold']}。"
            
            else:
                subject = f"警报: {data['token_symbol']}"
                message = f"您关注的代币 {data['token_symbol']} ({data['token_name']}) 触发了警报。"
            
            # 根据通知类型发送通知
            if alert.notification_type == 'email':
                send_email(alert.notification_target, subject, message)
                logger.info(f"Sent email alert to {alert.notification_target}")
            
            elif alert.notification_type == 'telegram':
                send_telegram_message(alert.notification_target, message)
                logger.info(f"Sent telegram alert to {alert.notification_target}")
            
            # 记录警报历史
            alert.last_triggered_at = datetime.datetime.utcnow()
            alert.trigger_count = (alert.trigger_count or 0) + 1
            
            # 更新警报数据
            alert_data = json.loads(alert.alert_data) if alert.alert_data else []
            alert_data.append({
                'timestamp': datetime.datetime.utcnow().isoformat(),
                'data': data
            })
            # 只保留最近10条记录
            if len(alert_data) > 10:
                alert_data = alert_data[-10:]
            alert.alert_data = json.dumps(alert_data)
            
            db.session.commit()
        
        except Exception as e:
            logger.error(f"Error triggering alert {alert.id}: {str(e)}")
    
    def check_all_alerts(self):
        """
        检查所有警报
        
        Returns:
            触发的警报数量
        """
        price_count = self.check_price_alerts()
        sentiment_count = self.check_sentiment_alerts()
        mention_count = self.check_mention_alerts()
        
        total_count = price_count + sentiment_count + mention_count
        logger.info(f"Checked all alerts, triggered {total_count} in total")
        
        return total_count 