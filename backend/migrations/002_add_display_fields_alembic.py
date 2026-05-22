"""Alembic revision: add display and AI config fields to cameras table.

This file is a helper Python-format migration for projects using Alembic.
If you use raw SQL migrations, apply the SQL in `001_add_display_fields.sql` instead.
"""

from alembic import op
import sqlalchemy as sa


revision = '002_add_display_fields'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('cameras', sa.Column('display_interval_seconds', sa.Integer(), nullable=True))
    op.add_column('cameras', sa.Column('fallback_seconds', sa.Integer(), nullable=True))
    op.add_column('cameras', sa.Column('ai_processing_fps', sa.Integer(), nullable=True))
    op.add_column('cameras', sa.Column('monitoring_interval_minutes', sa.Integer(), nullable=True))
    op.add_column('cameras', sa.Column('ai_region_json', sa.Text(), nullable=True))
    op.add_column('cameras', sa.Column('patrol_region_json', sa.Text(), nullable=True))

    op.alter_column('cameras', 'display_interval_seconds', existing_type=sa.Integer(), nullable=False)
    op.alter_column('cameras', 'fallback_seconds', existing_type=sa.Integer(), nullable=False)
    op.alter_column('cameras', 'ai_processing_fps', existing_type=sa.Integer(), nullable=False)
    op.alter_column('cameras', 'monitoring_interval_minutes', existing_type=sa.Integer(), nullable=False)


def downgrade():
    op.drop_column('cameras', 'ai_region_json')
    op.drop_column('cameras', 'patrol_region_json')
    op.drop_column('cameras', 'monitoring_interval_minutes')
    op.drop_column('cameras', 'ai_processing_fps')
    op.drop_column('cameras', 'fallback_seconds')
    op.drop_column('cameras', 'display_interval_seconds')
