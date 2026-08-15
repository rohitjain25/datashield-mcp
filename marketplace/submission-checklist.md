# MCP Market Submission Checklist

Based on the current documentation (docs.mcpmarket.com):

## Before You Begin
- [ ] Have a public GitHub repository with the MCP server code.
- [ ] Ensure the repository includes a clear license (MIT recommended).
- [ ] Add a `README.md` with setup instructions for Claude Desktop, Claude Code, and Cursor.
- [ ] Version your package (semantic versioning) and publish to PyPI (optional but recommended).
- [ ] Prepare marketing materials: title, short description, long description, features, keywords, categories, example prompts, screenshots.

## Submission Steps
1. **Log in to MCP Market** (create an account if needed).
2. **Navigate to “Submit a new MCP”** (or “Deploy a custom MCP server”).
3. **Provide the GitHub repository URL** (public read‑only).
4. **Select the appropriate category** (e.g., Data, Productivity, Developer Tools).
5. **Enter the title** (see `marketplace/title.md`).
6. **Enter the short description** (see `marketplace/short-description.md`).
7. **Enter the long description** (see `marketplace/long-description.md`).
8. **Upload or link screenshots** (see `marketplace/screenshots/` — create placeholder images if needed).
9. **Add keywords** (one per line or comma‑separated as per market UI; see `marketplace/keywords.txt`).
10. **Add categories** (see `marketplace/categories.txt`).
11. **Provide example prompts** (see `marketplace/example-prompts.md`).
12. **Set pricing model**:
    - Core MCP: Free listing.
    - Agent Skill (DataShield Pro): Set price to $2.00 USD, one‑time.
    - Indicate that the Skill provides premium resources (rules, recipes, prompts, workflows).
13. **Upload the Agent Skill package** (zip of the `premium/` directory) if the market accepts direct upload; otherwise, provide a link to a hosted release.
14. **Agree to terms of service** and confirm that the MCP is local‑first and does not require external APIs.
15. **Submit for review**.
16. **Wait for approval** (typically a few business days).
17. **Once approved**, verify the listing appears in the marketplace and that the Skill can be purchased.
18. **Announce the launch** via your channels.

## Post‑Submission
- [ ] Monitor the marketplace for reviews and questions.
- [ ] Keep the GitHub repository updated with bug fixes and improvements.
- [ ] Update the Agent Skill when premium content is enhanced (maintain versioning).
- [ ] Renew any required accounts or subscriptions (none required for core).