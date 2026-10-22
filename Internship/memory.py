sessions = {}


def get_session(session_id):
    if session_id not in sessions:
        sessions[session_id] = []

    return sessions[session_id]


def add_message(session_id, role, content):
    session = get_session(session_id)

    session.append({
        "role": role,
        "content": content
    })