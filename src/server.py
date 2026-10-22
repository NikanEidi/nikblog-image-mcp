from pathlib import Path
from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer
import os
import nikblog_client
from nikblog_client import session, login
import s3_uploader

SERVER_DIR = Path(__file__).resolve().parent
load_dotenv(SERVER_DIR.parent / ".env")

mcp = MCPServer("nikblog-image-mcp")

@mcp.tool()
def list_projects() -> str:
    """List every project in Nik-Blog, with its id, title, and whether it
    already has a cover image. Call this before uploading an image, to
    find the right project_id."""
    response = session.get(f"{os.environ['NIKBLOG_API_URL']}/admin/projects")
    return response.text

@mcp.tool()
def list_notes() -> str:
    """List every note in Nik-Blog, with its id, title, and whether it
    already has a cover image. Call this before uploading an image, to
    find the right note_id."""
    response = session.get(f"{os.environ['NIKBLOG_API_URL']}/admin/notes")
    return response.text

@mcp.tool()
def upload_project_image(
    project_id: int,
    local_image_path: str,
    overwrite: bool = False,
    confirmed: bool = False,
) -> str:
    """Upload a local image file as the cover image for a Nik-Blog project.
    This is a two-step tool: call it once with confirmed left as False to
    get a preview of exactly what would happen -- nothing is uploaded or
    changed yet. Only call it again with confirmed=True, after Nikan has
    seen the generated image and said yes, to actually perform the upload.
    Refuses to replace an existing image unless overwrite is explicitly
    True -- call list_projects first to check whether the project already
    has one."""
    project = nikblog_client.get_project(project_id)

    if project["image_url"] and not overwrite:
        return (
            f"Project {project_id} already has an image "
            f"({project['image_url']}). Pass overwrite=True to replace it."
        )

    if not confirmed:
        return (
            f"Preview only, nothing uploaded yet: would upload "
            f"{local_image_path} as the new cover image for project "
            f"{project_id} ('{project['title']}'). Ask Nikan to confirm, "
            f"then call this again with confirmed=True."
        )

    image_url = s3_uploader.upload_image(Path(local_image_path))
    nikblog_client.update_project_image(project_id, image_url)
    return f"Uploaded and set as project {project_id}'s image: {image_url}"

@mcp.tool()
def upload_note_image(
    note_id: int,
    local_image_path: str,
    overwrite: bool = False,
    confirmed: bool = False,
) -> str:
    """Upload a local image file as the cover image for a Nik-Blog note.
    Same two-step confirmation rule as upload_project_image: call it first
    with confirmed=False to preview, nothing happens until Nikan approves
    and it's called again with confirmed=True. Refuses to replace an
    existing image unless overwrite is explicitly True."""
    note = nikblog_client.get_note(note_id)

    if note["image_url"] and not overwrite:
        return (
            f"Note {note_id} already has an image "
            f"({note['image_url']}). Pass overwrite=True to replace it."
        )

    if not confirmed:
        return (
            f"Preview only, nothing uploaded yet: would upload "
            f"{local_image_path} as the new cover image for note "
            f"{note_id} ('{note['title']}'). Ask Nikan to confirm, "
            f"then call this again with confirmed=True."
        )

    image_url = s3_uploader.upload_image(Path(local_image_path))
    nikblog_client.update_note_image(note_id, image_url)
    return f"Uploaded and set as note {note_id}'s image: {image_url}"

if __name__ == "__main__":
    login()
    mcp.run()