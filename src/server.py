from mcp.server.mcpserver import MCPServer
import os

mcp = MCPServer("nikblog-image-mcp")

@mcp.tool()
def list_projects() -> str:
    """List every project in Nik-Blog, with its id, title, and whether it
    already has a cover image. Call this before uploading an image, to
    find the right project_id."""
    response = session.get(f"{os.environ['NIKBLOG_API_URL']}/admin/projects")
    return response.text