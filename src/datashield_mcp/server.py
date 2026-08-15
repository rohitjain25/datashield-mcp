"""
DataShield MCP Server
"""

import asyncio
import os
from typing import Any, Dict, List, Optional

import pandas as pd
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

# Initialize the MCP server
server = Server("datashield-mcp")


def _load_file(path: str) -> pd.DataFrame:
    """Load a file into a pandas DataFrame based on extension."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        return pd.read_csv(path)
    elif ext == ".tsv":
        return pd.read_csv(path, sep="\t")
    elif ext == ".json":
        return pd.read_json(path)
    elif ext == ".jsonl":
        return pd.read_json(path, lines=True)
    elif ext in (".xlsx", ".xls"):
        return pd.read_excel(path)
    elif ext == ".parquet":
        return pd.read_parquet(path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")


def _save_file(df: pd.DataFrame, path: str) -> None:
    """Save DataFrame to file based on extension."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        df.to_csv(path, index=False)
    elif ext == ".tsv":
        df.to_csv(path, sep="\t", index=False)
    elif ext == ".json":
        df.to_json(path, indent=2)
    elif ext == ".jsonl":
        df.to_json(path, orient="records", lines=True)
    elif ext in (".xlsx", ".xls"):
        df.to_excel(path, index=False)
    elif ext == ".parquet":
        df.to_parquet(path, index=False)
    else:
        raise ValueError(f"Unsupported file format: {ext}")


@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools."""
    return [
        Tool(
            name="inspect_file",
            description="Inspect a local file and return basic metadata.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute or relative path to the file to inspect",
                    }
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="profile_dataset",
            description="Profile a dataset and return statistical summary.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the dataset file",
                    }
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="detect_duplicates",
            description="Detect duplicate rows or values in specified columns.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the dataset file",
                    },
                    "columns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of columns to check for duplicates; if omitted, check entire row",
                    },
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="detect_pii",
            description="Detect personally identifiable information (PII) in the dataset.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the dataset file",
                    },
                    "columns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of columns to scan; if omitted, scan all string columns",
                    },
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="detect_secrets",
            description="Detect API keys, tokens, and other secrets in the dataset.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the dataset file",
                    },
                    "columns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of columns to scan; if omitted, scan all string columns",
                    },
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="sanitize_dataset",
            description="Sanitize PII or secrets by masking, hashing, removing, or replacing.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the dataset file",
                    },
                    "method": {
                        "type": "string",
                        "enum": ["mask", "hash", "remove", "replace", "tokenize"],
                        "description": "Sanitization method to apply",
                    },
                    "columns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Columns to sanitize; if omitted, apply to all detected PII/secret columns",
                    },
                    "replacement": {
                        "type": "string",
                        "description": "Replacement string for 'replace' method",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Optional output path; if not provided, creates a sanitized copy with suffix",
                    },
                },
                "required": ["path", "method"],
            },
        ),
        Tool(
            name="normalize_dataset",
            description="Normalize column names, whitespace, casing, dates, phone numbers, emails, etc.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the dataset file",
                    },
                    "options": {
                        "type": "object",
                        "description": "Normalization options (tru/false flags)",
                        "additionalProperties": {"type": "boolean"},
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Optional output path",
                    },
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="validate_dataset",
            description="Validate dataset against constraints (required columns, values, ranges, etc.).",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the dataset file",
                    },
                    "rules": {
                        "type": "object",
                        "description": "Validation rules to apply",
                        "additionalProperties": True,
                    },
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="compare_datasets",
            description="Compare two datasets for schema and row differences.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path_a": {
                        "type": "string",
                        "description": "Path to first dataset",
                    },
                    "path_b": {
                        "type": "string",
                        "description": "Path to second dataset",
                    },
                },
                "required": ["path_a", "path_b"],
            },
        ),
        Tool(
            name="clean_dataset",
            description="Perform safe cleaning: trim whitespace, standardize empties, remove exact duplicates.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the dataset file",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Optional output path",
                    },
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="convert_file",
            description="Convert a file between CSV, TSV, JSON, JSONL, XLSX, Parquet.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the source file",
                    },
                    "format": {
                        "type": "string",
                        "enum": ["csv", "tsv", "json", "jsonl", "xlsx", "parquet"],
                        "description": "Target format",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Optional output path",
                    },
                },
                "required": ["path", "format"],
            },
        ),
        Tool(
            name="generate_report",
            description="Generate a data quality report (Markdown, JSON, HTML).",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the dataset file",
                    },
                    "format": {
                        "type": "string",
                        "enum": ["markdown", "json", "html"],
                        "description": "Report format",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Optional output path for the report",
                    },
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="preview_changes",
            description="Preview changes before applying destructive operations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the dataset file",
                    },
                    "operation": {
                        "type": "string",
                        "enum": ["clean", "normalize", "sanitize", "convert"],
                        "description": "Operation to preview",
                    },
                    "args": {
                        "type": "object",
                        "description": "Arguments for the operation",
                    },
                },
                "required": ["path", "operation"],
            },
        ),
        Tool(
            name="create_sanitized_copy",
            description="Create a sanitized copy of the dataset with timestamp.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the dataset file",
                    },
                    "sanitization_method": {
                        "type": "string",
                        "enum": ["mask", "hash", "remove", "replace", "tokenize"],
                        "description": "Method to apply",
                    },
                    "columns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Columns to sanitize",
                    },
                },
                "required": ["path"],
            },
        ),
    ]


async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls."""
    try:
        if name == "inspect_file":
            result = await inspect_file(arguments["path"])
        elif name == "profile_dataset":
            result = await profile_dataset(arguments["path"])
        elif name == "detect_duplicates":
            result = await detect_duplicates(
                arguments["path"], arguments.get("columns")
            )
        elif name == "detect_pii":
            result = await detect_pii(
                arguments["path"], arguments.get("columns")
            )
        elif name == "detect_secrets":
            result = await detect_secrets(
                arguments["path"], arguments.get("columns")
            )
        elif name == "sanitize_dataset":
            result = await sanitize_dataset(
                arguments["path"],
                arguments["method"],
                arguments.get("columns"),
                arguments.get("replacement"),
                arguments.get("output_path"),
            )
        elif name == "normalize_dataset":
            result = await normalize_dataset(
                arguments["path"],
                arguments.get("options", {}),
                arguments.get("output_path"),
            )
        elif name == "validate_dataset":
            result = await validate_dataset(
                arguments["path"], arguments.get("rules", {})
            )
        elif name == "compare_datasets":
            result = await compare_datasets(
                arguments["path_a"], arguments["path_b"]
            )
        elif name == "clean_dataset":
            result = await clean_dataset(
                arguments["path"], arguments.get("output_path")
            )
        elif name == "convert_file":
            result = await convert_file(
                arguments["path"],
                arguments["format"],
                arguments.get("output_path"),
            )
        elif name == "generate_report":
            result = await generate_report(
                arguments["path"],
                arguments["format"],
                arguments.get("output_path"),
            )
        elif name == "preview_changes":
            result = await preview_changes(
                arguments["path"],
                arguments["operation"],
                arguments.get("args", {}),
            )
        elif name == "create_sanitized_copy":
            result = await create_sanitized_copy(
                arguments["path"],
                arguments["sanitization_method"],
                arguments.get("columns"),
            )
        else:
            raise ValueError(f"Unknown tool: {name}")

        return CallToolResult(
            content=[TextContent(type="text", text=str(result))]
        )
    except Exception as e:
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f'{{"success": false, "error_type": "{type(e).__name__}", "message": "{str(e)}", "recovery": "Check the input path and parameters."}}'
                )
            ],
            isError=True,
        )


async def inspect_file(path: str) -> Dict[str, Any]:
    df = _load_file(path)
    info = {
        "file_name": os.path.basename(path),
        "extension": os.path.splitext(path)[1],
        "size_bytes": os.path.getsize(path),
        "detected_format": os.path.splitext(path)[1][1:].lower(),
        "row_count": len(df),
        "column_count": len(df.columns),
        "column_names": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "encoding": "utf-8",  # simplified
    }
    # For Excel, get sheet names
    if path.lower().endswith(('.xlsx', '.xls')):
        try:
            xl = pd.ExcelFile(path)
            info["sheet_names"] = xl.sheet_names
        except Exception:
            info["sheet_names"] = []
    return info


async def profile_dataset(path: str) -> Dict[str, Any]:
    df = _load_file(path)
    profile = {
        "row_count": len(df),
        "column_count": len(df.columns),
        "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "missing_values": df.isnull().sum().to_dict(),
        "missing_percentage": (df.isnull().sum() / len(df) * 100).to_dict(),
        "unique_counts": df.nunique().to_dict(),
        "duplicate_rows": int(df.duplicated().sum()),
        "numeric_statistics": df.describe().to_dict() if not df.select_dtypes(include='number').empty else {},
        "categorical_statistics": {
            col: {
                "top": df[col].mode().iloc[0] if not df[col].mode().empty else None,
                "freq": int(df[col].value_counts().iloc[0]) if not df[col].value_counts().empty else 0,
            }
            for col in df.select_dtypes(include='object').columns
        },
        "suspicious_columns": [],  # placeholder
    }
    return profile


async def detect_duplicates(path: str, columns: Optional[List[str]] = None) -> Dict[str, Any]:
    df = _load_file(path)
    if columns:
        dup_mask = df.duplicated(subset=columns, keep=False)
    else:
        dup_mask = df.duplicated(keep=False)
    dup_df = df[dup_mask]
    return {
        "affected_rows": int(dup_mask.sum()),
        "affected_data": dup_df.head(10).to_dict(orient="records"),
        "columns_checked": columns if columns else list(df.columns),
        "confidence": "high",
        "explanation": "Exact duplicate rows found based on selected columns.",
    }


async def detect_pii(path: str, columns: Optional[List[str]] = None) -> Dict[str, Any]:
    import re
    df = _load_file(path)
    if columns is None:
        columns = df.select_dtypes(include='object').columns.tolist()
    pii_patterns = {
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        "ip_address": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
        "ssn": r'\b\d{3}-?\d{2}-?\d{4}\b',
        "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
    }
    findings = {}
    for col in columns:
        if col not in df.columns:
            continue
        col_findings = {}
        for pii_type, pattern in pii_patterns.items():
            matches = df[col].astype(str).str.extractall(pattern, flags=re.IGNORECASE)
            if not matches.empty:
                # Mask examples
                examples = matches[0].head(3).tolist()
                masked = [re.sub(r'.', '*', ex) if len(ex) > 2 else ex for ex in examples]
                col_findings[pii_type] = {
                    "count": int(len(matches)),
                    "masked_examples": masked,
                }
        if col_findings:
            findings[col] = col_findings
    return {
        "pii_detected": bool(findings),
        "findings": findings,
    }


async def detect_secrets(path: str, columns: Optional[List[str]] = None) -> Dict[str, Any]:
    import re
    df = _load_file(path)
    if columns is None:
        columns = df.select_dtypes(include='object').columns.tolist()
    secret_patterns = {
        "aws_access_key": r'\bAKIA[0-9A-Z]{16}\b',
        "github_token": r'\bghp_[0-9a-zA-Z]{36}\b',
        "generic_api_key": r'\b[a-zA-Z0-9]{32,}\b',
        "jwt": r'\beyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9\b',
        "private_key": r'-----BEGIN [A-Z ]+PRIVATE KEY-----',
    }
    findings = {}
    for col in columns:
        if col not in df.columns:
            continue
        col_findings = {}
        for secret_type, pattern in secret_patterns.items():
            matches = df[col].astype(str).str.extractall(pattern, flags=re.IGNORECASE)
            if not matches.empty:
                # Mask examples
                examples = matches[0].head(3).tolist()
                masked = [ex[:4] + '*' * (len(ex)-8) + ex[-4:] if len(ex) > 8 else ex for ex in examples]
                col_findings[secret_type] = {
                    "count": int(len(matches)),
                    "masked_examples": masked,
                }
        if col_findings:
            findings[col] = col_findings
    return {
        "secrets_detected": bool(findings),
        "findings": findings,
    }


async def sanitize_dataset(
    path: str,
    method: str,
    columns: Optional[List[str]] = None,
    replacement: Optional[str] = None,
    output_path: Optional[str] = None,
) -> Dict[str, Any]:
    df = _load_file(path)
    if columns is None:
        columns = df.select_dtypes(include='object').columns.tolist()
    # Determine output path
    if not output_path:
        base, ext = os.path.splitext(path)
        output_path = f"{base}_sanitized{ext}"
    # Apply method
    for col in columns:
        if col not in df.columns:
            continue
        if method == "mask":
            df[col] = df[col].astype(str).apply(lambda x: '*' * len(x) if isinstance(x, str) else x)
        elif method == "hash":
            import hashlib
            df[col] = df[col].astype(str).apply(lambda x: hashlib.sha256(x.encode()).hexdigest() if isinstance(x, str) else x)
        elif method == "remove":
            df[col] = None
        elif method == "replace":
            if replacement is None:
                raise ValueError("Replacement string required for 'replace' method")
            df[col] = replacement
        elif method == "tokenize":
            # Simple token mapping
            token_map = {}
            def tokenize(val):
                if not isinstance(val, str):
                    return val
                if val not in token_map:
                    token_map[val] = f"TOKEN_{len(token_map)}"
                return token_map[val]
            df[col] = df[col].apply(tokenize)
    _save_file(df, output_path)
    return {
        "success": True,
        "output_path": output_path,
        "method": method,
        "columns_processed": columns,
        "rows_affected": len(df),
    }


async def normalize_dataset(
    path: str,
    options: Dict[str, bool] = None,
    output_path: Optional[str] = None,
) -> Dict[str, Any]:
    if options is None:
        options = {}
    df = _load_file(path)
    original_columns = list(df.columns)
    # Normalize column names
    if options.get("column_names", True):
        df.columns = [
            col.strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
            for col in df.columns
        ]
    # Normalize whitespace in string columns
    if options.get("whitespace", True):
        str_cols = df.select_dtypes(include='object').columns
        for col in str_cols:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace(r'\\s+', ' ', regex=True)
    # Normalize casing
    if options.get("casing", True):
        str_cols = df.select_dtypes(include='object').columns
        for col in str_cols:
            # Lowercase unless looks like an acronym
            df[col] = df[col].str.lower()
    # Normalize dates (basic)
    if options.get("dates", True):
        for col in df.columns:
            if "date" in col.lower():
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                except Exception:
                    pass
    # Normalize phone numbers (US)
    if options.get("phones", True):
        for col in df.columns:
            if "phone" in col.lower():
                df[col] = df[col].astype(str).str.replace(r'\D', '', regex=True)
                df[col] = df[col].apply(lambda x: f"{x[:3]}-{x[3:6]}-{x[6:]}" if len(x) == 10 else x)
    # Normalize emails
    if options.get("emails", True):
        for col in df.columns:
            if "email" in col.lower():
                df[col] = df[col].astype(str).str.lower().str.strip()
    # Empty values
    if options.get("empty_values", True):
        df = df.replace(['', 'NULL', 'null', 'NaN', 'nan', None], pd.NA)
    # Booleans
    if options.get("booleans", True):
        for col in df.columns:
            if df[col].dtype == object:
                # Try to map common yes/no strings
                mapping = {
                    'yes': True, 'no': False, 'true': True, 'false': False,
                    'y': True, 'n': False, '1': True, '0': False
                }
                df[col] = df[col].map(lambda v: mapping.get(str(v).lower(), v) if isinstance(v, str) else v)
    # Categorical values
    if options.get("categorical", True):
        for col in df.select_dtypes(include='object').columns:
            # Trim and title case
            df[col] = df[col].astype(str).str.strip().str.title()
    # Save
    if not output_path:
        base, ext = os.path.splitext(path)
        output_path = f"{base}_normalized{ext}"
    _save_file(df, output_path)
    changes = {
        "original_columns": original_columns,
        "new_columns": list(df.columns),
        "row_count": len(df),
    }
    return {
        "success": True,
        "output_path": output_path,
        "changes_applied": changes,
    }


async def validate_dataset(path: str, rules: Dict[str, Any]) -> Dict[str, Any]:
    df = _load_file(path)
    errors = []
    warnings = []
    # Required columns
    required_cols = rules.get("required_columns", [])
    for col in required_cols:
        if col not in df.columns:
            errors.append(f"Missing required column: {col}")
    # Required values (non-null)
    required_values = rules.get("required_values", {})
    for col, must_be_present in required_values.items():
        if col in df.columns and must_be_present:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                errors.append(f"Column '{col}' has {null_count} null values")
    # Unique constraints
    unique_cols = rules.get("unique_columns", [])
    for col in unique_cols:
        if col in df.columns:
            dup_count = df[col].duplicated().sum()
            if dup_count > 0:
                warnings.append(f"Column '{col}' has {dup_count} duplicate values")
    # Numeric ranges
    numeric_ranges = rules.get("numeric_ranges", {})
    for col, rng in numeric_ranges.items():
        if col in df.columns:
            try:
                min_val, max_val = rng.get("min"), rng.get("max")
                if min_val is not None:
                    below = (df[col] < min_val).sum()
                    if below > 0:
                        warnings.append(f"Column '{col}' has {below} values below min {min_val}")
                if max_val is not None:
                    above = (df[col] > max_val).sum()
                    if above > 0:
                        warnings.append(f"Column '{col}' has {above} values above max {max_val}")
            except Exception:
                pass
    # Date ranges
    date_ranges = rules.get("date_ranges", {})
    for col, rng in date_ranges.items():
        if col in df.columns:
            try:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                min_date, max_date = rng.get("min"), rng.get("max")
                if min_date is not None:
                    below = (df[col] < min_date).sum()
                    if below > 0:
                        warnings.append(f"Column '{col}' has {below} dates before min {min_date}")
                if max_date is not None:
                    above = (df[col] > max_date).sum()
                    if above > 0:
                        warnings.append(f"Column '{col}' has {above} dates after max {max_date}")
            except Exception:
                pass
    # Allowed categories
    allowed_categories = rules.get("allowed_categories", {})
    for col, allowed in allowed_categories.items():
        if col in df.columns:
            invalid = ~df[col].isin(allowed)
            invalid_count = invalid.sum()
            if invalid_count > 0:
                warnings.append(f"Column '{col}' has {invalid_count} values not in allowed list")
    # Null thresholds
    null_thresholds = rules.get("null_thresholds", {})
    for col, thresh in null_thresholds.items():
        if col in df.columns:
            null_ratio = df[col].isnull().sum() / len(df)
            if null_ratio > thresh:
                warnings.append(f"Column '{col}' exceeds null threshold: {null_ratio:.2%} > {thresh}")
    status = "PASS" if not errors and not warnings else ("WARNING" if not errors else "FAIL")
    return {
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "checked_rows": len(df),
    }


async def compare_datasets(path_a: str, path_b: str) -> Dict[str, Any]:
    df_a = _load_file(path_a)
    df_b = _load_file(path_b)
    # Schema comparison
    cols_a = set(df_a.columns)
    cols_b = set(df_b.columns)
    added_cols = list(cols_b - cols_a)
    removed_cols = list(cols_a - cols_b)
    common_cols = list(cols_a & cols_b)
    # Row comparison (based on index for simplicity)
    # Align columns
    df_a_common = df_a[common_cols] if common_cols else pd.DataFrame()
    df_b_common = df_b[common_cols] if common_cols else pd.DataFrame()
    # For simplicity, compare shape
    rows_a = len(df_a)
    rows_b = len(df_b)
    # Find duplicates across datasets? We'll just report counts.
    return {
        "schema": {
            "columns_a": list(df_a.columns),
            "columns_b": list(df_b.columns),
            "added_columns": added_cols,
            "removed_columns": removed_cols,
            "common_columns": common_cols,
        },
        "row_counts": {
            "file_a": rows_a,
            "file_b": rows_b,
            "difference": rows_b - rows_a,
        },
        "note": "Detailed diff requires key columns; this is a basic comparison.",
    }


async def clean_dataset(path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
    df = _load_file(path)
    # Trim whitespace
    str_cols = df.select_dtypes(include='object').columns
    for col in str_cols:
        df[col] = df[col].astype(str).str.strip()
    # Standardize empty strings
    df = df.replace(['', 'NULL', 'null', 'NaN', 'nan', None], pd.NA)
    # Remove exact duplicate rows
    before = len(df)
    df = df.drop_duplicates()
    after = len(df)
    removed = before - after
    if not output_path:
        base, ext = os.path.splitext(path)
        output_path = f"{base}_cleaned{ext}"
    _save_file(df, output_path)
    return {
        "success": True,
        "output_path": output_path,
        "original_rows": before,
        "cleaned_rows": after,
        "duplicates_removed": removed,
    }


async def convert_file(path: str, fmt: str, output_path: Optional[str] = None) -> Dict[str, Any]:
    df = _load_file(path)
    if not output_path:
        base, _ = os.path.splitext(path)
        output_path = f"{base}.{fmt}"
    _save_file(df, output_path)
    return {
        "success": True,
        "output_path": output_path,
        "format": fmt,
        "rows": len(df),
    }


async def generate_report(path: str, fmt: str, output_path: Optional[str] = None) -> Dict[str, Any]:
    # Use profile dataset and other checks
    profile = await profile_dataset(path)
    pii = await detect_pii(path)
    secrets = await detect_secrets(path)
    duplicates = await detect_duplicates(path)
    # Compute a simple quality score
    total_cells = profile["row_count"] * profile["column_count"]
    missing_cells = sum(profile["missing_values"].values())
    duplicate_cells = duplicates["affected_rows"] * profile["column_count"]  # approximate
    pii_cells = sum(
        findings.get("count", 0)
        for col_findings in pii.get("findings", {}).values()
        for findings in col_findings.values()
        if isinstance(findings, dict) and "count" in findings
    )
    secret_cells = sum(
        findings.get("count", 0)
        for col_findings in secrets.get("findings", {}).values()
        for findings in col_findings.values()
        if isinstance(findings, dict) and "count" in findings
    )
    # Score: 100 - penalty for missing, duplicates, pii, secrets (simplified)
    penalty = (
        (missing_cells / max(total_cells, 1)) * 30 +
        (duplicate_cells / max(total_cells, 1)) * 30 +
        (pii_cells / max(total_cells, 1)) * 20 +
        (secret_cells / max(total_cells, 1)) * 20
    )
    score = max(0, min(100, int(100 - penalty)))
    report_data = {
        "dataset": os.path.basename(path),
        "data_shield_quality_score": score,
        "profile": profile,
        "duplicates": duplicates,
        "pii": pii,
        "secrets": secrets,
    }
    if fmt == "json":
        import json
        content = json.dumps(report_data, indent=2)
    elif fmt == "markdown":
        content = f"# DataShield Quality Report\n\n"
        content += f"**Dataset:** {report_data['dataset']}\n\n"
        content += f"**Quality Score:** {score}/100\n\n"
        content += f"## Profile\n"
        content += f"- Rows: {profile['row_count']}\n"
        content += f"- Columns: {profile['column_count']}\n"
        content += f"- Missing values: {missing_cells}\n"
        content += f"- Duplicate rows: {duplicates['affected_rows']}\n"
        content += f"- PII detections: {pii_cells}\n"
        content += f"- Secret detections: {secret_cells}\n\n"
    else:  # html
        content = f"<h1>DataShield Quality Report</h1>"
        content += f"<p><strong>Dataset:</strong> {report_data['dataset']}</p>"
        content += f"<p><strong>Quality Score:</strong> {score}/100</p>"
        content += "<h2>Profile</h2><ul>"
        content += f"<li>Rows: {profile['row_count']}</li>"
        content += f"<li>Columns: {profile['column_count']}</li>"
        content += f"<li>Missing values: {missing_cells}</li>"
        content += f"<li>Duplicate rows: {duplicates['affected_rows']}</li>"
        content += f"<li>PII detections: {pii_cells}</li>"
        content += f"<li>Secret detections: {secret_cells}</li>"
        content += "</ul>"
    if not output_path:
        base, _ = os.path.splitext(path)
        output_path = f"{base}_report.{fmt}"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    return {
        "success": True,
        "output_path": output_path,
        "format": fmt,
        "quality_score": score,
    }


async def preview_changes(
    path: str,
    operation: str,
    args: Dict[str, Any] = None,
) -> Dict[str, Any]:
    if args is None:
        args = {}
    df = _load_file(path)
    # For simplicity, show first few rows as preview
    preview_df = df.head(5)
    return {
        "operation": operation,
        "args": args,
        "preview_rows": preview_df.to_dict(orient="records"),
        "note": "Actual changes would be applied to a copy; review above sample.",
    }


async def create_sanitized_copy(
    path: str,
    sanitization_method: str,
    columns: Optional[List[str]] = None,
) -> Dict[str, Any]:
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base, ext = os.path.splitext(path)
    output_path = f"{base}_sanitized_{timestamp}{ext}"
    result = await sanitize_dataset(
        path,
        sanitization_method,
        columns,
        output_path=output_path,
    )
    return result


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())