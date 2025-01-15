"""添加字典相关表

Revision ID: ff58436c9954
Revises: 2b5db0d9b2db
Create Date: 2025-01-15 20:13:40.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ff58436c9954'
down_revision: str = '2b5db0d9b2db'  # 设置为上一个迁移的 revision
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建字典表
    op.create_table(
        'sys_dict',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False, comment='字典编码'),
        sa.Column('name', sa.String(length=50), nullable=False, comment='字典名称'),
        sa.Column('key', sa.String(length=50), nullable=False, comment='字典key'),
        sa.Column('value', sa.String(length=50), nullable=False, comment='字典value'),
        sa.Column('type', sa.String(length=50), nullable=False, comment='字典类型'),
        sa.Column('status', sa.Integer(), nullable=False, comment='状态：0-正常，1-禁用'),
        sa.Column('create_time', sa.Integer(), nullable=False, comment='创建时间'),
        sa.Column('last_time', sa.Integer(), nullable=False, comment='最后修改时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
        sa.UniqueConstraint('key'),
        comment='系统字典表'
    )

    # 创建字典项表
    op.create_table(
        'sys_dict_item',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('item_code', sa.String(length=50), nullable=False, comment='字典项编码'),
        sa.Column('dict_id', sa.Integer(), nullable=False, comment='字典ID'),
        sa.Column('name', sa.String(length=50), nullable=False, comment='字典项名称'),
        sa.Column('key', sa.String(length=50), nullable=False, comment='字典项key'),
        sa.Column('value', sa.String(length=50), nullable=False, comment='字典项value'),
        sa.Column('type', sa.String(length=50), nullable=False, comment='字典项类型'),
        sa.Column('status', sa.Integer(), nullable=False, comment='状态：0-正常，1-禁用'),
        sa.Column('create_time', sa.Integer(), nullable=False, comment='创建时间'),
        sa.Column('last_time', sa.Integer(), nullable=False, comment='最后修改时间'),
        sa.ForeignKeyConstraint(['dict_id'], ['sys_dict.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('item_code'),
        sa.UniqueConstraint('dict_id', 'key', name='uix_dict_item_key'),
        comment='系统字典项表'
    )

    # 创建索引
    op.create_index('ix_sys_dict_type', 'sys_dict', ['type'], unique=False)
    op.create_index('ix_sys_dict_status', 'sys_dict', ['status'], unique=False)
    op.create_index('ix_sys_dict_item_type', 'sys_dict_item', ['type'], unique=False)
    op.create_index('ix_sys_dict_item_status', 'sys_dict_item', ['status'], unique=False)


def downgrade() -> None:
    # 删除索引
    op.drop_index('ix_sys_dict_item_status', table_name='sys_dict_item')
    op.drop_index('ix_sys_dict_item_type', table_name='sys_dict_item')
    op.drop_index('ix_sys_dict_status', table_name='sys_dict')
    op.drop_index('ix_sys_dict_type', table_name='sys_dict')

    # 删除表
    op.drop_table('sys_dict_item')
    op.drop_table('sys_dict')
