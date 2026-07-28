from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ReviewRecord(Base):
    __tablename__ = "review_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    provider: Mapped[str] = mapped_column(String(50))
    diff: Mapped[str] = mapped_column(Text)
    summary: Mapped[str] = mapped_column(Text)
    issues: Mapped[list] = mapped_column(JSON)
    overall_assessment: Mapped[str] = mapped_column(String(50))
