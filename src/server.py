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
def get_prompt_writing_context(project_id: int) -> str:
    """Get everything needed to write a new Gemini cover-image prompt for
    one project: that project's real title and description, plus the full
    text of every existing gemini-prompt-*.md file already written for
    other projects. Use the existing ones to match the exact noir+copper
    style and structure, and to avoid reusing a visual metaphor that's
    already been used for a different project. Call this before writing a
    new prompt; call save_image_prompt once the new prompt is written."""
    project = nikblog_client.get_project(project_id)

    assets_dir = Path(os.environ["NIKBLOG_REPO_PATH"]) / "notes" / "assets"
    existing_prompts = []
    for prompt_file in sorted(assets_dir.glob("gemini-prompt-*.md")):
        existing_prompts.append(f"--- {prompt_file.name} ---\n{prompt_file.read_text()}")

    return (
        f"Project: {project['title']}\n"
        f"Description: {project['description']}\n\n"
        f"=== Existing prompts (for style + to avoid repeating a motif) ===\n\n"
        + "\n\n".join(existing_prompts)
    )


@mcp.tool()
def save_image_prompt(project_id: int, prompt_markdown: str) -> str:
    """Save a newly written Gemini image prompt as a new file, following
    the same naming convention as every existing one:
    notes/assets/gemini-prompt-<project-slug>.md. Call get_prompt_writing_context
    first to write a prompt that matches the existing style."""
    project = nikblog_client.get_project(project_id)
    slug = project["slug"]

    assets_dir = Path(os.environ["NIKBLOG_REPO_PATH"]) / "notes" / "assets"
    prompt_path = assets_dir / f"gemini-prompt-{slug}.md"
    prompt_path.write_text(prompt_markdown)

    return f"Saved prompt to {prompt_path}"

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