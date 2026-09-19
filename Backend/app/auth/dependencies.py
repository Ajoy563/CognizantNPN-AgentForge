from datetime import datetime, timezone
from typing import Any, Optional
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.auth.firebase import verify_id_token
from app.db.mongodb import mongo

bearer_scheme = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> dict[str, Any]:
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    decoded_token = verify_id_token(credentials.credentials)
    uid = decoded_token["uid"]
    email = decoded_token.get("email", "")
    name_from_token = decoded_token.get("name") or ""

    now = datetime.now(timezone.utc)
    on_insert = {"created_at": now}
    if name_from_token:
        # Only seeds the name on first sight; a user's own profile edit
        # (POST /api/users/me) must not be overwritten by the identity
        # provider's name on every subsequent login.
        on_insert["name"] = name_from_token

    db = mongo.get_db()
    db.users.update_one(
        {"uid": uid},
        {"$set": {"uid": uid, "email": email, "updated_at": now}, "$setOnInsert": on_insert},
        upsert=True
    )

    return decoded_token
