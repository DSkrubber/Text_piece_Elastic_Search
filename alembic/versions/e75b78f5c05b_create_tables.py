"""create_tables

Revision ID: e75b78f5c05b
Revises:
Create Date: 2022-05-05 14:04:52.482009

"""
from enum import Enum

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "e75b78f5c05b"
down_revision = None
branch_labels = None
depends_on = None


class TextPieceType(str, Enum):
    title = "title"
    paragraph = "paragraph"


def upgrade():
    op.create_table(
        "documents",
        sa.Column("document_id", sa.INTEGER(), nullable=False),
        sa.Column("name", sa.VARCHAR(), nullable=False),
        sa.Column("author", sa.VARCHAR(), nullable=False),
        sa.PrimaryKeyConstraint("document_id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(
        op.f("ix_documents_author"), "documents", ["author"], unique=False
    )
    op.create_table(
        "text_pieces",
        sa.Column("piece_id", sa.INTEGER(), nullable=False),
        sa.Column(
            "meta_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("indexed", sa.BOOLEAN(), nullable=False),
        sa.Column("document_name", sa.VARCHAR(), nullable=False),
        sa.Column("size", sa.INTEGER(), nullable=False),
        sa.Column("page", sa.INTEGER(), nullable=False),
        sa.Column("text", sa.TEXT(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["document_name"],
            ["documents.name"],
        ),
        sa.PrimaryKeyConstraint("piece_id"),
    )
    piece_type = postgresql.ENUM(TextPieceType, name="piece_type")
    piece_type.create(op.get_bind(), checkfirst=True)
    op.add_column("text_pieces", sa.Column("type", piece_type, nullable=False))
    op.create_index(
        op.f("ix_text_pieces_created_at"),
        "text_pieces",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_text_pieces_document_name"),
        "text_pieces",
        ["document_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_text_pieces_size"), "text_pieces", ["size"], unique=False
    )


def downgrade():
    op.drop_index(op.f("ix_text_pieces_size"), table_name="text_pieces")
    op.drop_index(
        op.f("ix_text_pieces_document_name"), table_name="text_pieces"
    )
    op.drop_index(op.f("ix_text_pieces_created_at"), table_name="text_pieces")
    op.drop_table("text_pieces")
    op.execute("DROP TYPE piece_type;")
    op.drop_index(op.f("ix_documents_author"), table_name="documents")
    op.drop_table("documents")
