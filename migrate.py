# migrate.py
from sqlalchemy import text
from extend.db import LOCSESSION

def run_migrations():
    """运行所有迁移"""
    with LOCSESSION() as session:
        try:
            # 删除旧表（如果存在）
            session.execute(text("DROP TABLE IF EXISTS user_lv_next;"))
            
            # 创建新表
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
            print("成功创建用户等级表")
        except Exception as e:
            print(f"创建失败: {str(e)}")
            session.rollback()

if __name__ == "__main__":
    run_migrations()
