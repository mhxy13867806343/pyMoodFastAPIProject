"""将用户登录记录表的 user_id 改为 user_uid

Revision ID: 20250112_user_login_record_uid
Revises: 2b5db0d9b2db
Create Date: 2025-01-12 13:14:51.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '20250112_user_login_record_uid'
down_revision = '2b5db0d9b2db'  # 这里需要填写上一个迁移版本的ID
branch_labels = None
depends_on = None

def upgrade():
    # 1. 添加新的 user_uid 列
    op.add_column('user_login_record',
        sa.Column('user_uid', sa.String(28), nullable=True)
    )

    # 2. 更新 user_uid 列的值
    connection = op.get_bind()
    connection.execute(text("""
        UPDATE user_login_record lr
        JOIN user_inputs u ON lr.user_id = u.id
        SET lr.user_uid = u.uid
    """))

    # 3. 将 user_uid 列设为非空
    op.alter_column('user_login_record', 'user_uid',
        existing_type=sa.String(28),
        nullable=False
    )

    # 4. 添加外键约束
    op.create_foreign_key(
        'fk_user_login_record_user_uid',
        'user_login_record', 'user_inputs',
        ['user_uid'], ['uid']
    )

    # 5. 删除旧的 user_id 列及其外键
    op.drop_constraint('user_login_record_ibfk_1', 'user_login_record', type_='foreignkey')
    op.drop_column('user_login_record', 'user_id')

def downgrade():
    # 1. 添加旧的 user_id 列
    op.add_column('user_login_record',
        sa.Column('user_id', sa.Integer(), nullable=True)
    )

    # 2. 更新 user_id 列的值
    connection = op.get_bind()
    connection.execute(text("""
        UPDATE user_login_record lr
        JOIN user_inputs u ON lr.user_uid = u.uid
        SET lr.user_id = u.id
    """))

    # 3. 将 user_id 列设为非空
    op.alter_column('user_login_record', 'user_id',
        existing_type=sa.Integer(),
        nullable=False
    )

    # 4. 添加旧的外键约束
    op.create_foreign_key(
        'user_login_record_ibfk_1',
        'user_login_record', 'user_inputs',
        ['user_id'], ['id']
    )

    # 5. 删除新的 user_uid 列及其外键
    op.drop_constraint('fk_user_login_record_user_uid', 'user_login_record', type_='foreignkey')
    op.drop_column('user_login_record', 'user_uid')
