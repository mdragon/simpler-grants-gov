"""fix column type and add version number

Revision ID: c6878bae0c60
Revises: b26ea0f40066
Create Date: 2024-04-19 13:41:34.017203

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c6878bae0c60"
down_revision = "b26ea0f40066"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "opportunity",
        "revision_number",
        existing_type=sa.TEXT(),
        type_=sa.Integer(),
        existing_nullable=True,
        postgresql_using="revision_number::integer",
        schema="api",
    )
    op.add_column(
        "opportunity_summary",
        sa.Column("version_number", sa.Integer(), nullable=True),
        schema="api",
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("opportunity_summary", "version_number", schema="api")
    op.alter_column(
        "opportunity",
        "revision_number",
        existing_type=sa.Integer(),
        type_=sa.TEXT(),
        existing_nullable=True,
        postgresql_using="revision_number::TEXT",
        schema="api",
    )
    # ### end Alembic commands ###
