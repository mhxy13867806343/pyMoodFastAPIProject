# migrate.py
from sqlalchemy import text
from extend.db import LOCSESSION

def run_migrations():
    """运行所有迁移"""
    with LOCSESSION() as session:
        try:
            # 删除旧表（如果存在）
            session.execute(text("DROP TABLE IF EXISTS user_lv_next;"))
            session.execute(text("DROP TABLE IF EXISTS user_login_record;"))
            session.execute(text("DROP TABLE IF EXISTS user_logout_records;"))
            
            # 创建登录记录表
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS user_login_record (
                    id INT AUTO_INCREMENT,
                    user_uid VARCHAR(28) NOT NULL COMMENT '用户UID',
                    login_date DATE NOT NULL COMMENT '登录日期',
                    login_time INT NOT NULL COMMENT '登录时间戳',
                    continuous_days INT DEFAULT 1 COMMENT '连续登录天数',
                    create_time INT NOT NULL DEFAULT 0 COMMENT '创建时间',
                    last_time INT NOT NULL DEFAULT 0 COMMENT '最后更新时间',
                    PRIMARY KEY (id),
                    INDEX idx_user_uid (user_uid)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """))

            # 创建登出记录表
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS user_logout_records (
                    id INT AUTO_INCREMENT,
                    user_uid VARCHAR(28) NOT NULL COMMENT '用户UID',
                    logout_time BIGINT NOT NULL COMMENT '登出时间戳',
                    logout_date DATE NOT NULL COMMENT '登出日期',
                    create_time INT NOT NULL DEFAULT 0 COMMENT '创建时间',
                    last_time INT NOT NULL DEFAULT 0 COMMENT '最后更新时间',
                    PRIMARY KEY (id),
                    INDEX idx_user_uid (user_uid)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """))
            
            # 创建用户等级表
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS user_lv_next (
                    id INT AUTO_INCREMENT,
                    user_uid VARCHAR(28) NOT NULL COMMENT '用户UID',
                    lv INT NOT NULL DEFAULT 0 COMMENT '用户等级',
                    max_lv INT NOT NULL DEFAULT 10 COMMENT '最大等级',
                    exp INT NOT NULL DEFAULT 0 COMMENT '当前经验值',
                    next_lv INT NOT NULL DEFAULT 0 COMMENT '下一级所需积分',
                    create_time INT NOT NULL DEFAULT 0 COMMENT '创建时间',
                    last_time INT NOT NULL DEFAULT 0 COMMENT '最后更新时间',
                    PRIMARY KEY (id),
                    INDEX idx_user_uid (user_uid)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """))
            
            session.commit()
            print("成功创建所有表")
        except Exception as e:
            print(f"创建失败: {str(e)}")
            session.rollback()

if __name__ == "__main__":
    run_migrations()
