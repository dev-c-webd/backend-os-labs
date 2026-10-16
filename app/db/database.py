from sqlalchemy import create_engine
from app.core.config import settings

from sqlalchemy.orm import sessionmaker

engine = create_engine(settings.database_url)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

# Session = sessionmaker()

# with Session(engine) as session:
#     session.add()
#     session.add()
#     session.commit()



# it is to test the connection with the database
'''
uv run python - <<'PY'
from sqlalchemy import text
from app.db.database import engine

with engine.connect() as connection:
    result = connection.execute(text("SELECT 1"))
    print("Database connection successful:", result.scalar_one())
PY
'''

# from sqlalchemy import text
# from app.db.database import engine

# with engine.connect() as connection:
#     result = connection.execute(text("SELECT 1"))
#     print("Database connection successful:", result.scalar_one())