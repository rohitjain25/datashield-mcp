# Cost Audit

## Developer Recurring Cost: $0

### Required Hosting
None. The MCP runs locally on the user's machine; no server hosting is needed.

### Required API Keys
None. The core MCP does not call any external LLM APIs or paid services.

### Required LLM API
None. The MCP is a tool that works with any LLM (Claude, local models, etc.) but does not itself require an LLM API key.

### Required Database
None. All data is processed in memory with pandas and saved to files.

### Required Paid OCR
None. No OCR functionality is included.

### Required Paid Storage
None. Storage is the local filesystem.

### Required Paid Analytics
None. No telemetry or analytics collection.

### Required Paid Marketplace Listing
MCP Market may offer free listings; any paid placement is optional.

## How the Application Works Without Developer‑Side Infrastructure

- **Execution Model**: The MCP server is launched via stdio by the MCP client (Claude Desktop, Claude Code, Cursor). It runs as a subprocess on the user's machine.
- **Dependencies**: Pure Python packages (pandas, openpyxl) that are installed locally via pip.
- **File Operations**: All reads and writes are to user‑specified local paths.
- **No Network Calls**: The core code contains no `requests`, `httpx`, `urllib`, or similar libraries. A search of the source tree confirms zero network‑capable imports.
- **Offline‑First**: The machine can be completely offline and the MCP will function normally.

Thus, the developer incurs no ongoing cost to run or maintain the service; the user bears only the trivial cost of installing the Python package.