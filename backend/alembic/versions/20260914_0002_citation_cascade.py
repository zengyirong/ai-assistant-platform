"""message_citation: ON DELETE CASCADE for document/chunk FKs.

Revision ID: 20260914_0002
Revises: 20260914_0001
Create Date: 2026-09-14

Allows deleting documents (and their chunks) without manual citation cleanup.
Application-layer citation delete remains as a defensive safeguard.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "20260914_0002"
down_revision: str | None = "20260914_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE message_citation DROP FOREIGN KEY fk_citation_document"
    )
    op.execute(
        """
        ALTER TABLE message_citation
          ADD CONSTRAINT fk_citation_document
          FOREIGN KEY (document_id) REFERENCES document (id) ON DELETE CASCADE
        """
    )
    op.execute("ALTER TABLE message_citation DROP FOREIGN KEY fk_citation_chunk")
    op.execute(
        """
        ALTER TABLE message_citation
          ADD CONSTRAINT fk_citation_chunk
          FOREIGN KEY (chunk_id) REFERENCES document_chunk (id) ON DELETE CASCADE
        """
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE message_citation DROP FOREIGN KEY fk_citation_document"
    )
    op.execute(
        """
        ALTER TABLE message_citation
          ADD CONSTRAINT fk_citation_document
          FOREIGN KEY (document_id) REFERENCES document (id)
        """
    )
    op.execute("ALTER TABLE message_citation DROP FOREIGN KEY fk_citation_chunk")
    op.execute(
        """
        ALTER TABLE message_citation
          ADD CONSTRAINT fk_citation_chunk
          FOREIGN KEY (chunk_id) REFERENCES document_chunk (id)
        """
    )
