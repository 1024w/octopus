import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app
from app.utils.logging import get_logger

logger = get_logger("utils.notification")

def send_email(recipient, subject, message):
    """
    发送电子邮件
    
    Args:
        recipient: 收件人邮箱
        subject: 邮件主题
        message: 邮件内容
        
    Returns:
        是否发送成功
    """
    try:
        # 获取SMTP配置
        smtp_host = current_app.config.get('SMTP_HOST')
        smtp_port = current_app.config.get('SMTP_PORT')
        smtp_user = current_app.config.get('SMTP_USER')
        smtp_password = current_app.config.get('SMTP_PASSWORD')
        sender = current_app.config.get('SMTP_SENDER', smtp_user)
        
        if not all([smtp_host, smtp_port, smtp_user, smtp_password]):
            logger.error("SMTP configuration is incomplete")
            return False
        
        # 创建邮件
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = recipient
        msg['Subject'] = subject
        
        # 添加邮件内容
        msg.attach(MIMEText(message, 'plain'))
        
        # 连接SMTP服务器并发送邮件
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        logger.info(f"Email sent to {recipient}: {subject}")
        return True
    
    except Exception as e:
        logger.error(f"Error sending email to {recipient}: {str(e)}")
        return False

def send_telegram_message(chat_id, message):
    """
    发送Telegram消息
    
    Args:
        chat_id: 聊天ID
        message: 消息内容
        
    Returns:
        是否发送成功
    """
    try:
        # 获取Telegram Bot配置
        bot_token = current_app.config.get('TELEGRAM_BOT_TOKEN')
        
        if not bot_token:
            logger.error("Telegram Bot token is not configured")
            return False
        
        # 发送消息
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, data=data)
        
        if response.status_code == 200:
            logger.info(f"Telegram message sent to {chat_id}")
            return True
        else:
            logger.error(f"Error sending Telegram message: {response.text}")
            return False
    
    except Exception as e:
        logger.error(f"Error sending Telegram message: {str(e)}")
        return False

def send_webhook_notification(webhook_url, data):
    """
    发送Webhook通知
    
    Args:
        webhook_url: Webhook URL
        data: 通知数据
        
    Returns:
        是否发送成功
    """
    try:
        # 发送Webhook通知
        response = requests.post(webhook_url, json=data)
        
        if response.status_code in [200, 201, 202, 204]:
            logger.info(f"Webhook notification sent to {webhook_url}")
            return True
        else:
            logger.error(f"Error sending webhook notification: {response.text}")
            return False
    
    except Exception as e:
        logger.error(f"Error sending webhook notification: {str(e)}")
        return False 