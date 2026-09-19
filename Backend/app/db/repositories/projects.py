from bson.objectid import ObjectId
from app.db.mongodb import mongo

def create_project(data: dict) -> dict:
    db = mongo.get_db()
    result = db.projects.insert_one(data)
    data["project_id"] = str(result.inserted_id)
    return data

def get_projects_by_uid(uid: str) -> list[dict]:
    db = mongo.get_db()
    projects = list(db.projects.find({"uid": uid}).sort("created_at", -1))
    for p in projects:
        p["project_id"] = str(p.pop("_id"))
    return projects

def get_project_by_id(project_id: str) -> dict:
    db = mongo.get_db()
    try:
        project = db.projects.find_one({"_id": ObjectId(project_id)})
        if project:
            project["project_id"] = str(project.pop("_id"))
            return project
    except Exception:
        pass
    return None


def set_latest_generation(project_id: str, uid: str, generation_id: str, updated_at) -> None:
    mongo.get_db().projects.update_one(
        {"_id": ObjectId(project_id), "uid": uid},
        {"$set": {"latest_generation_id": generation_id, "updated_at": updated_at}},
    )
