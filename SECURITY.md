# Security

DataShield MCP is designed to be run locally and does not communicate with external services.

## Reporting a Vulnerability

Please report security vulnerabilities privately via email to security@datashield.example (or through GitHub private vulnerability reporting). Do not open a public issue.

## Supported Versions

We provide security updates for the latest stable version.

## Safe by Design

- No network requests are made unless explicitly required for optional features (none in core).
- All file operations are confined to user‑provided paths.
- Original files are never overwritten without explicit user request and a copy is created.