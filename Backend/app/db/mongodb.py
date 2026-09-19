from pymongo import MongoClient
from pymongo.database import Database
from app.core.config import settings

class MongoDB:
    def __init__(self):
        self.client: MongoClient | None = None
        self.db: Database | None = None
        self._indexes_ensured = False

    def connect(self):
        if not self.client:
            self.client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=5_000)
            self.db = self.client.get_default_database(default=settings.mongodb_db_name)
        if not self._indexes_ensured:
            self.ensure_indexes()

    def get_db(self):
        self.connect()
        assert self.db is not None
        return self.db

    def ensure_indexes(self) -> None:
        """Create indexes needed for user-scoped lookups and history sorting.
        Safe to call repeatedly: create_index is a no-op when an equivalent
        index already exists.
        """
        assert self.db is not None
        self.db.users.create_index("uid", unique=True)
        self.db.projects.create_index([("uid", 1), ("created_at", -1)])
        self.db.generations.create_index([("project_id", 1), ("uid", 1), ("created_at", -1)])
        self.db.generations.create_index([("uid", 1), ("created_at", -1)])
        self._indexes_ensured = True

    def health_check(self) -> bool:
        try:
            self.get_db().command("ping")
            return True
        except Exception:
            return False

mongo = MongoDB()
