import os
from app import create_app

# 创建应用实例
app = create_app(os.getenv('FLASK_CONFIG') or 'default')

if __name__ == '__main__':
    # 运行应用
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000))) 