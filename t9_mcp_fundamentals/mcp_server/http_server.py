import sys
from pathlib import Path

# Add the project root to sys.path so imports work regardless of cwd
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from t9_mcp_fundamentals.mcp_server._server import mcp

if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
    )