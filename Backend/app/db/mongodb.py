from pymongo import MongoClient
from pymongo.database import Database
from app.core.config import settings

class MongoDB:
    def __init__(self):
        self.client: MongoClient | None = None
        self.db: Database | None = None
    
    def connect(self):
        if not self.client:
            self.client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=5_000)
            self.db = self.client.get_default_database(default="solutionforge")
    
    def get_db(self):
        self.connect()
        assert self.db is not None
        return self.db

    def health_check(self) -> bool:
        try:
            self.get_db().command("ping")
            return True
        except Exception:
            return False

mongo = MongoDB()
