# Installation

## Prerequisites
- Python 3.11 or newer
- pip (Python package installer)

## Install via pip
```bash
pip install datashield-mcp
```

## Install via pipx (recommended)
```bash
pipx install datashield-mcp
```

## Verify Installation
```bash
datashield-mcp --help
```
Should show the help message and version.

## Using with MCP Clients

### Claude Desktop
1. Open `claude_desktop_config.json` (location varies by OS).
2. Add the following entry:
   ```json
   {
     "mcpServers": {
       "datashield": {
         "command": "datashield-mcp",
         "args": []
       }
     }
   }
   ```
3. Restart Claude Desktop.
4. The DataShield tools should appear in the tool list.

### Claude Code
Add to your MCP configuration or launch via:
```bash
npx -y @modelcontextprotocol/cli datashield-mcp
```

### Cursor
1. Open Cursor Settings → MCP Servers.
2. Add a new server:
   - Name: datashield
   - Command: datashield-mcp
   - Args: (empty)
3. Save and restart Cursor.

## From Source
```bash
git clone https://github.com/yourusername/datashield-mcp.git
cd datashield-mcp
pip install -e .
```