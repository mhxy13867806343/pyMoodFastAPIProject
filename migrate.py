# migrate.py
from sqlalchemy import text
from extend.db import LOCSESSION

def run_migrations():
    # 添加 signature 字段
    with LOCSESSION() as session:
        try:
            session.execute(text("ALTER TABLE user_inputs ADD COLUMN signature VARCHAR(32) NOT NULL DEFAULT ''"))
            session.commit()
            print("成功添加 signature 字段")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("signature 字段已存在")
            else:
                print(f"添加字段失败: {str(e)}")

if __name__ == "__main__":
    run_migrations()
