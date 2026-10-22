import os
import requests


session = requests.Session()

def login() -> None:
    response = session.post(
        f"{os.environ['NIKBLOG_API_URL']}/auth/login",
        json={"email": os.environ["NIKBLOG_ADMIN_EMAIL"], "password": os.environ["NIKBLOG_ADMIN_PASSWORD"]},
    )
    response.raise_for_status()


def get_project(project_id: int) -> dict:
    response = session.get(f"{os.environ['NIKBLOG_API_URL']}/admin/projects/{project_id}")
    response.raise_for_status()
    return response.json()["project"]


# PUT /projects/:id fully replaces the row (title, description, tech_stack,
# etc. all get overwritten with whatever is in the request body) -- it is
# not a partial update. So this reads the project first and sends every
# field back unchanged except image_url, instead of sending only imageUrl
# and silently wiping out the project's title/description/tech stack.
def update_project_image(project_id: int, image_url: str) -> None:
    project = get_project(project_id)
    response = session.put(
        f"{os.environ['NIKBLOG_API_URL']}/projects/{project_id}",
        json={
            "title": project["title"],
            "description": project["description"],
            "techStack": project["tech_stack"],
            "githubUrl": project["github_url"],
            "liveUrl": project["live_url"],
            "imageUrl": image_url,
        },
    )
    response.raise_for_status()


def get_note(note_id: int) -> dict:
    response = session.get(f"{os.environ['NIKBLOG_API_URL']}/admin/notes/{note_id}")
    response.raise_for_status()
    return response.json()["note"]


# Same reasoning as update_project_image: PUT /notes/:id is a full replace,
# so the current note is read first and sent back unchanged except image_url.
def update_note_image(note_id: int, image_url: str) -> None:
    note = get_note(note_id)
    response = session.put(
        f"{os.environ['NIKBLOG_API_URL']}/notes/{note_id}",
        json={
            "title": note["title"],
            "category": note["category"],
            "content": note["content"],
            "projectId": note["project_id"],
            "status": note["status"],
            "imageUrl": image_url,
        },
    )
    response.raise_for_status()