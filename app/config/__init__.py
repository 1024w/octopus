from .config import DevelopmentConfig, ProductionConfig, TestingConfig

config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 