import datetime
from app.models import db
from app.models.user import User
from app.utils.logging import get_logger

logger = get_logger("service.auth")

class AuthService:
    """认证服务，处理用户认证相关业务逻辑"""
    
    def authenticate(self, username, password):
        """
        验证用户凭据
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            成功返回用户对象，失败返回None
        """
        user = self.get_user_by_username(username)
        
        if not user:
            logger.warning(f"Authentication failed: user {username} not found")
            return None
        
        if not user.is_active:
            logger.warning(f"Authentication failed: user {username} is inactive")
            return None
        
        if not user.verify_password(password):
            logger.warning(f"Authentication failed: invalid password for user {username}")
            return None
        
        # 更新最后登录时间
        user.last_login_at = datetime.datetime.utcnow()
        db.session.commit()
        
        logger.info(f"User {username} authenticated successfully")
        return user
    
    def get_user_by_id(self, user_id):
        """
        通过ID获取用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户对象或None
        """
        return User.query.get(user_id)
    
    def get_user_by_username(self, username):
        """
        通过用户名获取用户
        
        Args:
            username: 用户名
            
        Returns:
            用户对象或None
        """
        return User.query.filter_by(username=username).first()
    
    def get_user_by_email(self, email):
        """
        通过邮箱获取用户
        
        Args:
            email: 邮箱
            
        Returns:
            用户对象或None
        """
        return User.query.filter_by(email=email).first()
    
    def create_user(self, username, password, email, role='user'):
        """
        创建新用户
        
        Args:
            username: 用户名
            password: 密码
            email: 邮箱
            role: 角色，默认为'user'
            
        Returns:
            新创建的用户对象
            
        Raises:
            ValueError: 如果用户名或邮箱已存在
        """
        # 检查用户名是否已存在
        if self.get_user_by_username(username):
            logger.warning(f"Failed to create user: username {username} already exists")
            raise ValueError(f"Username '{username}' already exists")
        
        # 检查邮箱是否已存在
        if self.get_user_by_email(email):
            logger.warning(f"Failed to create user: email {email} already exists")
            raise ValueError(f"Email '{email}' already exists")
        
        # 创建新用户
        user = User(
            username=username,
            email=email,
            role=role
        )
        user.password = password  # 使用setter方法加密密码
        
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"Created new user: {username}")
        return user
    
    def change_password(self, user_id, current_password, new_password):
        """
        修改用户密码
        
        Args:
            user_id: 用户ID
            current_password: 当前密码
            new_password: 新密码
            
        Returns:
            成功返回True，失败返回False
            
        Raises:
            ValueError: 如果新密码无效
        """
        user = self.get_user_by_id(user_id)
        
        if not user:
            logger.warning(f"Failed to change password: user {user_id} not found")
            return False
        
        if not user.verify_password(current_password):
            logger.warning(f"Failed to change password: invalid current password for user {user_id}")
            return False
        
        if len(new_password) < 8:
            logger.warning(f"Failed to change password: new password too short for user {user_id}")
            raise ValueError("Password must be at least 8 characters long")
        
        user.password = new_password
        db.session.commit()
        
        logger.info(f"Changed password for user {user_id}")
        return True 