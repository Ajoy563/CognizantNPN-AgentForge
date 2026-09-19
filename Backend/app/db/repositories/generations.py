from bson.objectid import ObjectId
from app.db.mongodb import mongo

def create_generation(data: dict) -> dict:
    db = mongo.get_db()
    result = db.generations.insert_one(data)
    data["generation_id"] = str(result.inserted_id)
    return data

def list_generations(project_id: str, uid: str) -> list[dict]:
    db = mongo.get_db()
    generations = list(db.generations.find({"project_id": project_id, "uid": uid}).sort("created_at", -1))
    for g in generations:
        g["generation_id"] = str(g.pop("_id"))
    return generations

def get_generation(generation_id: str, uid: str) -> dict:
    db = mongo.get_db()
    try:
        gen = db.generations.find_one({"_id": ObjectId(generation_id), "uid": uid})
        if gen:
            gen["generation_id"] = str(gen.pop("_id"))
            return gen
    except Exception:
        pass
    return None
