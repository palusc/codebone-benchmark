SESSIONS = {}


def create(session_id, user_id):
    SESSIONS[session_id] = user_id
    return {"id": session_id, "user_id": user_id}
