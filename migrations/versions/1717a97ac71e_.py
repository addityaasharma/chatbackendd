"""Fix UserChat groupId column

Revision ID: 1717a97ac71e
Revises: d87a91cb3c5f
Create Date: 2025-09-16
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1717a97ac71e'
down_revision = 'd87a91cb3c5f'
branch_labels = None
depends_on = None


def upgrade():
    # Make ChatGroup.chatId nullable
    with op.batch_alter_table('ChatGroup', schema=None) as batch_op:
        batch_op.alter_column('chatId',
               existing_type=sa.INTEGER(),
               nullable=True)

    # Add groupId to UserChat as nullable and add FK
    with op.batch_alter_table('UserChat', schema=None) as batch_op:
        batch_op.add_column(sa.Column('groupId', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_userchat_group', 'ChatGroup', ['groupId'], ['id'])


def downgrade():
    # Remove groupId from UserChat
    with op.batch_alter_table('UserChat', schema=None) as batch_op:
        batch_op.drop_constraint('fk_userchat_group', type_='foreignkey')
        batch_op.drop_column('groupId')

    # Revert ChatGroup.chatId to NOT NULL
    with op.batch_alter_table('ChatGroup', schema=None) as batch_op:
        batch_op.alter_column('chatId',
               existing_type=sa.INTEGER(),
               nullable=False)
