from app.models import db
from app.models.user import User
from app.utils.logging import get_logger

logger = get_logger("service.user")

class UserService:
    """用户服务，处理用户管理相关业务逻辑"""
    
    def get_users(self, page=1, per_page=20):
        """
        获取用户列表，支持分页
        
        Args:
            page: 页码，从1开始
            per_page: 每页数量
            
        Returns:
            (users, total) 用户列表和总数
        """
        pagination = User.query.order_by(User.id).paginate(
            page=page, per_page=per_page, error_out=False
        )
        return pagination.items, pagination.total
    
    def get_user_by_id(self, user_id):
        """
        通过ID获取用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户对象或None
        """
        return User.query.get(user_id)
    
    def update_user(self, user_id, username=None, email=None, password=None, role=None):
        """
        更新用户信息
        
        Args:
            user_id: 用户ID
            username: 新用户名，可选
            email: 新邮箱，可选
            password: 新密码，可选
            role: 新角色，可选
            
        Returns:
            更新后的用户对象
            
        Raises:
            ValueError: 如果用户名或邮箱已被其他用户使用
        """
        user = self.get_user_by_id(user_id)
        
        if not user:
            logger.warning(f"Failed to update user: user {user_id} not found")
            raise ValueError(f"User with ID {user_id} not found")
        
        # 更新用户名
        if username and username != user.username:
            existing_user = User.query.filter_by(username=username).first()
            if existing_user and existing_user.id != user_id:
                logger.warning(f"Failed to update user: username {username} already exists")
                raise ValueError(f"Username '{username}' already exists")
            user.username = username
        
        # 更新邮箱
        if email and email != user.email:
            existing_user = User.query.filter_by(email=email).first()
            if existing_user and existing_user.id != user_id:
                logger.warning(f"Failed to update user: email {email} already exists")
                raise ValueError(f"Email '{email}' already exists")
            user.email = email
        
        # 更新密码
        if password:
            user.password = password
        
        # 更新角色
        if role:
            user.role = role
        
        db.session.commit()
        
        logger.info(f"Updated user: {user_id}")
        return user
    
    def delete_user(self, user_id):
        """
        删除用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            成功返回True，失败返回False
        """
        user = self.get_user_by_id(user_id)
        
        if not user:
            logger.warning(f"Failed to delete user: user {user_id} not found")
            return False
        
        db.session.delete(user)
        db.session.commit()
        
        logger.info(f"Deleted user: {user_id}")
        return True
    
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