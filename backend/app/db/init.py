from app.db.base import Base
from app.db.session import engine


def init_db() -> None:
    # Import all models before calling create_all
    Base.metadata.create_all(bind=engine)
