"""
DataShield MCP Server
"""

import asyncio
import os
from typing import Any, Dict, List, Optional

import pandas as pd
from mcp.server.mcpserver import MCPServer
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
server = MCPServer(
    name="datashield-mcp",
    description="Local data cleaning, validation, deduplication, PII detection, and sanitization MCP server",
    version="0.1.0",
)


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


@server.tool()
async def inspect_file(path: str) -> Dict[str, Any]:
    """Inspect a file and return basic information about its structure and content.

    Args:
        path: Path to the file to inspect

    Returns:
        Dictionary containing file information including shape, columns, data types, and sample data
    """
    try:
        df = _load_file(path)

        # Get basic info
        info = {
            "path": path,
            "shape": {
                "rows": len(df),
                "columns": len(df.columns)
            },
            "columns": list(df.columns),
            "data_types": {col: str(dtype) for col, dtype in df.dtypes.to_dict().items()},
            "memory_usage": df.memory_usage(deep=True).sum(),
            "null_counts": df.isnull().sum().to_dict(),
            "duplicate_rows": df.duplicated().sum(),
            "sample_data": df.head(5).to_dict('records') if len(df) > 0 else []
        }

        return info
    except Exception as e:
        return {"error": str(e)}


@server.tool()
async def profile_dataset(path: str) -> Dict[str, Any]:
    """Generate a comprehensive profile of a dataset including statistics and insights.

    Args:
        path: Path to the dataset file

    Returns:
        Dictionary containing profile information including statistics, distributions, and insights
    """
    try:
        df = _load_file(path)

        # Basic info
        profile = {
            "path": path,
            "shape": {
                "rows": len(df),
                "columns": len(df.columns)
            },
            "column_types": {col: str(dtype) for col, dtype in df.dtypes.to_dict().items()},
        }

        # Numerical columns statistics
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            profile["numerical_statistics"] = df[numeric_cols].describe().to_dict()

        # Categorical columns statistics
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        if len(categorical_cols) > 0:
            categorical_stats = {}
            for col in categorical_cols:
                categorical_stats[col] = {
                    "unique_values": int(df[col].nunique()),
                    "top_values": df[col].value_counts().head(5).to_dict(),
                    "null_count": int(df[col].isnull().sum())
                }
            profile["categorical_statistics"] = categorical_stats

        # Missing values summary
        profile["missing_values"] = {
            "total_missing": int(df.isnull().sum().sum()),
            "missing_by_column": df.isnull().sum().to_dict(),
            "missing_percentage": (df.isnull().sum() / len(df) * 100).to_dict()
        }

        return profile
    except Exception as e:
        return {"error": str(e)}


@server.tool()
async def detect_duplicates(path: str, columns: Optional[List[str]] = None) -> Dict[str, Any]:
    """Detect duplicate rows in a dataset.

    Args:
        path: Path to the dataset file
        columns: Optional list of columns to consider for duplicate detection. If None, all columns are used.

    Returns:
        Dictionary containing duplicate information including count and examples
    """
    try:
        df = _load_file(path)

        if columns is None:
            duplicate_mask = df.duplicated(keep=False)
        else:
            # Validate columns exist
            missing_cols = [col for col in columns if col not in df.columns]
            if missing_cols:
                return {"error": f"Columns not found: {missing_cols}"}
            duplicate_mask = df.duplicated(subset=columns, keep=False)

        duplicate_count = duplicate_mask.sum()
        duplicate_rows = df[duplicate_mask]

        result = {
            "path": path,
            "total_rows": len(df),
            "duplicate_count": int(duplicate_count),
            "duplicate_percentage": (duplicate_count / len(df) * 100) if len(df) > 0 else 0,
            "columns_considered": columns if columns is not None else list(df.columns),
            "duplicate_examples": duplicate_rows.head(10).to_dict('records') if duplicate_count > 0 else []
        }

        return result
    except Exception as e:
        return {"error": str(e)}


@server.tool()
async def detect_pii(path: str, columns: Optional[List[str]] = None) -> Dict[str, Any]:
    """Detect personally identifiable information (PII) in a dataset.

    Args:
        path: Path to the dataset file
        columns: Optional list of columns to scan for PII. If None, all text columns are scanned.

    Returns:
        Dictionary containing PII detection results including counts and locations
    """
    try:
        df = _load_file(path)

        # Common PII patterns
        pii_patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone_us": r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b',
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
            "credit_card": r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
            "zip_code": r'\b\d{5}(?:-\d{4})?\b',
            "ip_address": r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        }

        # Determine columns to scan
        if columns is None:
            # Scan all object/string columns
            columns_to_scan = df.select_dtypes(include=['object']).columns.tolist()
        else:
            # Validate columns exist
            missing_cols = [col for col in columns if col not in df.columns]
            if missing_cols:
                return {"error": f"Columns not found: {missing_cols}"}
            columns_to_scan = columns

        if len(columns_to_scan) == 0:
            return {"error": "No text columns found to scan for PII"}

        # Scan for PII
        pii_results = {}
        total_pii_count = 0

        for col in columns_to_scan:
            col_pii = {}
            col_total = 0

            for pattern_name, pattern in pii_patterns.items():
                # Count matches in this column
                matches = df[col].astype(str).str.contains(pattern, regex=True, na=False)
                count = matches.sum()
                if count > 0:
                    col_pii[pattern_name] = int(count)
                    col_total += count

                    # Get examples (up to 5)
                    if count > 0:
                        examples = df[col][matches].head(5).tolist()
                        col_pii[f"{pattern_name}_examples"] = examples

            if col_total > 0:
                pii_results[col] = col_pii
                total_pii_count += col_total

        result = {
            "path": path,
            "columns_scanned": columns_to_scan,
            "total_pii_instances": int(total_pii_count),
            "columns_with_pii": list(pii_results.keys()),
            "pii_details": pii_results
        }

        return result
    except Exception as e:
        return {"error": str(e)}


@server.tool()
async def detect_secrets(path: str, columns: Optional[List[str]] = None) -> Dict[str, Any]:
    """Detect potential secrets, keys, and tokens in a dataset.

    Args:
        path: Path to the dataset file
        columns: Optional list of columns to scan for secrets. If None, all text columns are scanned.

    Returns:
        Dictionary containing secrets detection results including counts and examples
    """
    try:
        df = _load_file(path)

        # Common secret/key patterns
        secret_patterns = {
            "api_key": r'\b[A-Za-z0-9_-]{32,}\b',
            "aws_access_key": r'\bAKIA[0-9A-Z]{16}\b',
            "aws_secret_key": r'\b[0-9a-zA-Z/+]{40}\b',
            "github_token": r'\bghp_[A-Za-z0-9]{36}\b',
            "slack_token": r'\bxox[baprs]-([0-9a-zA-Z]{10,48})?\b',
            "jwt_token": r'\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b',
            "private_key": r'-----BEGIN [A-Z ]+PRIVATE KEY-----',
            "password": r'(?i)password[=:\s]+[^\s]{8,}',
        }

        # Determine columns to scan
        if columns is None:
            # Scan all object/string columns
            columns_to_scan = df.select_dtypes(include=['object']).columns.tolist()
        else:
            # Validate columns exist
            missing_cols = [col for col in columns if col not in df.columns]
            if missing_cols:
                return {"error": f"Columns not found: {missing_cols}"}
            columns_to_scan = columns

        if len(columns_to_scan) == 0:
            return {"error": "No text columns found to scan for secrets"}

        # Scan for secrets
        secrets_results = {}
        total_secrets_count = 0

        for col in columns_to_scan:
            col_secrets = {}
            col_total = 0

            for pattern_name, pattern in secret_patterns.items():
                # Count matches in this column
                matches = df[col].astype(str).str.contains(pattern, regex=True, na=False)
                count = matches.sum()
                if count > 0:
                    col_secrets[pattern_name] = int(count)
                    col_total += count

                    # Get examples (up to 3 for security)
                    if count > 0:
                        examples = df[col][matches].head(3).tolist()
                        # Mask the examples for security
                        masked_examples = []
                        for example in examples:
                            if len(str(example)) > 8:
                                masked = str(example)[:4] + "*" * (len(str(example)) - 8) + str(example)[-4:]
                            else:
                                masked = "*" * len(str(example))
                            masked_examples.append(masked)
                        col_secrets[f"{pattern_name}_examples"] = masked_examples

            if col_total > 0:
                secrets_results[col] = col_secrets
                total_secrets_count += col_total

        result = {
            "path": path,
            "columns_scanned": columns_to_scan,
            "total_secrets_instances": int(total_secrets_count),
            "columns_with_secrets": list(secrets_results.keys()),
            "secrets_details": secrets_results
        }

        return result
    except Exception as e:
        return {"error": str(e)}


@server.tool()
async def sanitize_dataset(
    path: str,
    sanitization_method: str = "redact",
    columns: Optional[List[str]] = None,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """Sanitize sensitive data in a dataset (PII, secrets, etc.).

    Args:
        path: Path to the dataset file
        sanitization_method: Method to use for sanitization ("redact", "hash", "mask", "remove")
        columns: Optional list of columns to sanitize. If None, all applicable columns are processed.
        output_path: Optional path to save the sanitized dataset. If not provided, overwrites input.

    Returns:
        Dictionary containing sanitization results including statistics and output path
    """
    try:
        df = _load_file(path)

        if output_path is None:
            output_path = path

        # Determine columns to process
        if columns is None:
            # Process all object/string columns by default
            columns_to_process = df.select_dtypes(include=['object']).columns.tolist()
        else:
            # Validate columns exist
            missing_cols = [col for col in columns if col not in df.columns]
            if missing_cols:
                return {"error": f"Columns not found: {missing_cols}"}
            columns_to_process = columns

        if len(columns_to_process) == 0:
            return {"error": "No text columns found to sanitize"}

        # Track changes
        changes_made = {}
        total_changes = 0

        # Process each column
        for col in columns_to_process:
            col_changes = 0
            original_series = df[col].copy()

            # Apply sanitization method
            if sanitization_method == "redact":
                df[col] = df[col].astype(str).apply(
                    lambda x: "[REDACTED]" if pd.notnull(x) and str(x).strip() != "" else x
                )
            elif sanitization_method == "mask":
                df[col] = df[col].astype(str).apply(
                    lambda x: "*" * len(str(x)) if pd.notnull(x) and str(x).strip() != "" else x
                )
            elif sanitization_method == "hash":
                import hashlib
                df[col] = df[col].astype(str).apply(
                    lambda x: hashlib.sha256(str(x).encode()).hexdigest() if pd.notnull(x) and str(x).strip() != "" else x
                )
            elif sanitization_method == "remove":
                # Remove rows that contain sensitive data (simplified approach)
                # In practice, you'd want more sophisticated detection here
                pass
            else:
                return {"error": f"Unsupported sanitization method: {sanitization_method}"}

            # Count changes
            if sanitization_method != "remove":
                col_changes = (original_series != df[col]).sum()
                changes_made[col] = int(col_changes)
                total_changes += col_changes

        # Save the sanitized dataset
        _save_file(df, output_path)

        result = {
            "path": path,
            "output_path": output_path,
            "sanitization_method": sanitization_method,
            "columns_processed": columns_to_process,
            "total_changes_made": int(total_changes),
            "changes_by_column": changes_made,
            "rows_processed": len(df)
        }

        return result
    except Exception as e:
        return {"error": str(e)}


@server.tool()
async def normalize_dataset(
    path: str,
    normalization_rules: Dict[str, Any],
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """Normalize data in a dataset according to specified rules.

    Args:
        path: Path to the dataset file
        normalization_rules: Dictionary defining normalization rules for columns
        output_path: Optional path to save the normalized dataset. If not provided, overwrites input.

    Returns:
        Dictionary containing normalization results including statistics and output path
    """
    try:
        df = _load_file(path)

        if output_path is None:
            output_path = path

        # Track changes
        changes_made = {}
        columns_processed = []

        # Apply normalization rules
        for col, rules in normalization_rules.items():
            if col not in df.columns:
                continue

            columns_processed.append(col)
            original_series = df[col].copy()
            col_changes = 0

            # Apply each rule
            if "trim_whitespace" in rules and rules["trim_whitespace"]:
                if df[col].dtype == 'object':
                    df[col] = df[col].str.strip()

            if "lowercase" in rules and rules["lowercase"]:
                if df[col].dtype == 'object':
                    df[col] = df[col].str.lower()

            if "uppercase" in rules and rules["uppercase"]:
                if df[col].dtype == 'object':
                    df[col] = df[col].str.upper()

            if "date_format" in rules and rules["date_format"]:
                try:
                    df[col] = pd.to_datetime(df[col]).dt.strftime(rules["date_format"])
                except Exception:
                    pass  # Keep original if conversion fails

            if "numeric_scale" in rules and rules["numeric_scale"]:
                try:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    scale = rules["numeric_scale"]
                    df[col] = df[col].round(scale)
                except Exception:
                    pass  # Keep original if conversion fails

            if "fill_missing" in rules:
                fill_value = rules["fill_missing"]
                df[col] = df[col].fillna(fill_value)

            # Count changes
            col_changes = (original_series != df[col]).sum()
            changes_made[col] = int(col_changes)

        # Save the normalized dataset
        _save_file(df, output_path)

        result = {
            "path": path,
            "output_path": output_path,
            "normalization_rules": normalization_rules,
            "columns_processed": columns_processed,
            "changes_by_column": changes_made,
            "total_changes_made": sum(changes_made.values()),
            "rows_processed": len(df)
        }

        return result
    except Exception as e:
        return {"error": str(e)}


@server.tool()
async def validate_dataset(
    path: str,
    validation_rules: Dict[str, Any]
) -> Dict[str, Any]:
    """Validate a dataset against specified rules.

    Args:
        path: Path to the dataset file
        validation_rules: Dictionary defining validation rules for columns

    Returns:
        Dictionary containing validation results including pass/fail status and details
    """
    try:
        df = _load_file(path)

        # Track validation results
        validation_results = {}
        overall_passed = True
        columns_validated = []

        # Apply validation rules
        for col, rules in validation_rules.items():
            if col not in df.columns:
                validation_results[col] = {
                    "passed": False,
                    "error": f"Column '{col}' not found in dataset"
                }
                overall_passed = False
                continue

            columns_validated.append(col)
            col_passed = True
            col_details = {
                "total_rows": len(df),
                "null_count": int(df[col].isnull().sum()),
                "non_null_count": int(df[col].notnull().sum())
            }

            # Apply each validation rule
            if "required" in rules and rules["required"]:
                null_count = df[col].isnull().sum()
                if null_count > 0:
                    col_passed = False
                    col_details["null_values_found"] = int(null_count)

            if "type" in rules:
                expected_type = rules["type"]
                type_matches = 0
                if expected_type == "numeric":
                    type_matches = pd.to_numeric(df[col], errors='coerce').notnull().sum()
                elif expected_type == "integer":
                    type_matches = df[col].apply(lambda x: isinstance(x, (int, np.integer)) if pd.notnull(x) else False).sum()
                elif expected_type == "string":
                    type_matches = df[col].apply(lambda x: isinstance(x, str) if pd.notnull(x) else False).sum()
                elif expected_type == "boolean":
                    type_matches = df[col].apply(lambda x: isinstance(x, bool) if pd.notnull(x) else False).sum()
                elif expected_type == "date":
                    try:
                        type_matches = pd.to_datetime(df[col], errors='coerce').notnull().sum()
                    except Exception:
                        type_matches = 0

                if type_matches < len(df):
                    col_passed = False
                    col_details["type_mismatch_count"] = int(len(df) - type_matches)

            if "min_value" in rules and df[col].dtype in ['int64', 'float64']:
                try:
                    min_val = rules["min_value"]
                    below_min = (df[col] < min_val).sum()
                    if below_min > 0:
                        col_passed = False
                        col_details["below_min_count"] = int(below_min)
                except Exception:
                    pass

            if "max_value" in rules and df[col].dtype in ['int64', 'float64']:
                try:
                    max_val = rules["max_value"]
                    above_max = (df[col] > max_val).sum()
                    if above_max > 0:
                        col_passed = False
                        col_details["above_max_count"] = int(above_max)
                except Exception:
                    pass

            if "min_length" in rules and df[col].dtype == 'object':
                try:
                    min_len = rules["min_length"]
                    too_short = df[col].astype(str).str.len().lt(min_len).sum()
                    if too_short > 0:
                        col_passed = False
                        col_details["below_min_length_count"] = int(too_short)
                except Exception:
                    pass

            if "max_length" in rules and df[col].dtype == 'object':
                try:
                    max_len = rules["max_length"]
                    too_long = df[col].astype(str).str.len().gt(max_len).sum()
                    if too_long > 0:
                        col_passed = False
                        col_details["above_max_length_count"] = int(too_long)
                except Exception:
                    pass

            if "regex_pattern" in rules and df[col].dtype == 'object':
                try:
                    pattern = rules["regex_pattern"]
                    matches = df[col].astype(str).str.match(pattern, na=False).sum()
                    if matches < len(df[col].notnull()):
                        col_passed = False
                        col_details["regex_mismatch_count"] = int(len(df[col].notnull()) - matches)
                except Exception:
                    pass

            if "allowed_values" in rules:
                allowed = rules["allowed_values"]
                if not df[col].isin(allowed).all():
                    col_passed = False
                    invalid_count = (~df[col].isin(allowed)).sum()
                    col_details["invalid_values_count"] = int(invalid_count)
                    col_details["invalid_values_found"] = df[col][~df[col].isin(allowed)].unique().tolist()[:10]

            validation_results[col] = {
                "passed": col_passed,
                "details": col_details
            }

            if not col_passed:
                overall_passed = False

        result = {
            "path": path,
            "overall_passed": overall_passed,
            "columns_validated": columns_validated,
            "validation_results": validation_results,
            "total_columns_validated": len(columns_validated),
            "columns_passed": sum(1 for col in columns_validated if validation_results[col]["passed"]),
            "columns_failed": sum(1 for col in columns_validated if not validation_results[col]["passed"])
        }

        return result
    except Exception as e:
        return {"error": str(e)}


@server.tool()
async def compare_datasets(
    path1: str,
    path2: str,
    comparison_type: str = "schema",
    key_columns: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Compare two datasets for differences in schema, data, or values.

    Args:
        path1: Path to the first dataset file
        path2: Path to the second dataset file
        comparison_type: Type of comparison ("schema", "data", "values")
        key_columns: Optional list of columns to use as keys for row-wise comparison

    Returns:
        Dictionary containing comparison results including differences found
    """
    try:
        df1 = _load_file(path1)
        df2 = _load_file(path2)

        result = {
            "path1": path1,
            "path2": path2,
            "comparison_type": comparison_type,
            "differences_found": False,
            "details": {}
        }

        if comparison_type == "schema":
            # Compare schemas
            cols1 = set(df1.columns)
            cols2 = set(df2.columns)

            only_in_1 = list(cols1 - cols2)
            only_in_2 = list(cols2 - cols1)
            common_cols = list(cols1 & cols2)

            result["details"] = {
                "columns_only_in_first": only_in_1,
                "columns_only_in_second": only_in_2,
                "common_columns": common_cols,
                "schemas_match": len(only_in_1) == 0 and len(only_in_2) == 0
            }

            # Check data types for common columns
            if len(common_cols) > 0:
                type_mismatches = []
                for col in common_cols:
                    if str(df1[col].dtype) != str(df2[col].dtype):
                        type_mismatches.append({
                            "column": col,
                            "path1_type": str(df1[col].dtype),
                            "path2_type": str(df2[col].dtype)
                        })
                result["details"]["type_mismatches"] = type_mismatches
                if len(type_mismatches) > 0:
                    result["differences_found"] = True

            result["differences_found"] = result["differences_found"] or len(only_in_1) > 0 or len(only_in_2) > 0

        elif comparison_type == "data":
            # Compare row counts and basic stats
            result["details"] = {
                "path1_rows": len(df1),
                "path2_rows": len(df2),
                "row_count_difference": len(df1) - len(df2),
                "path1_columns": len(df1.columns),
                "path2_columns": len(df2.columns),
                "column_count_difference": len(df1.columns) - len(df2.columns)
            }

            if len(df1) != len(df2) or len(df1.columns) != len(df2.columns):
                result["differences_found"] = True

        elif comparison_type == "values":
            # For value comparison, we need key columns to join on
            if key_columns is None:
                # Use all common columns as keys if not specified
                common_cols = set(df1.columns) & set(df2.columns)
                if len(common_cols) == 0:
                    return {"error": "No common columns found for comparison and no key_columns specified"}
                key_columns = list(common_cols)
            else:
                # Validate key columns exist in both datasets
                missing_in_1 = [col for col in key_columns if col not in df1.columns]
                missing_in_2 = [col for col in key_columns if col not in df2.columns]
                if missing_in_1 or missing_in_2:
                    return {"error": f"Key columns not found - path1: {missing_in_1}, path2: {missing_in_2}"}

            # Perform merge to find differences
            try:
                # Add suffixes to distinguish columns from each dataset
                df1_keyed = df1.set_index(key_columns) if len(key_columns) == 1 else df1.set_index(key_columns)
                df2_keyed = df2.set_index(key_columns) if len(key_columns) == 1 else df2.set_index(key_columns)

                # Find rows in df1 not in df2
                only_in_1 = df1[~df1.set_index(key_columns).index.isin(df2.set_index(key_columns).index)]
                # Find rows in df2 not in df1
                only_in_2 = df2[~df2.set_index(key_columns).index.isin(df1.set_index(key_columns).index)]

                result["details"] = {
                    "key_columns": key_columns,
                    "rows_only_in_first": len(only_in_1),
                    "rows_only_in_second": len(only_in_2),
                    "rows_only_in_first_details": only_in_1.head(5).to_dict('records') if len(only_in_1) > 0 else [],
                    "rows_only_in_second_details": only_in_2.head(5).to_dict('records') if len(only_in_2) > 0 else []
                }

                if len(only_in_1) > 0 or len(only_in_2) > 0:
                    result["differences_found"] = True

            except Exception as e:
                # Fallback to simple comparison if merge fails
                result["details"] = {
                    "error": f"Value comparison failed: {str(e)}",
                    "path1_shape": df1.shape,
                    "path2_shape": df2.shape
                }
                result["differences_found"] = df1.shape != df2.shape

        return result
    except Exception as e:
        return {"error": str(e)}


@server.tool()
async def clean_dataset(
    path: str,
    cleaning_operations: List[Dict[str, Any]],
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """Apply a series of cleaning operations to a dataset.

    Args:
        path: Path to the dataset file
        cleaning_operations: List of cleaning operations to apply sequentially
        output_path: Optional path to save the cleaned dataset. If not provided, overwrites input.

    Returns:
        Dictionary containing cleaning results including statistics and output path
    """
    try:
        df = _load_file(path)

        if output_path is None:
            output_path = path

        # Track changes through each operation
        operations_applied = []
        total_rows_before = len(df)

        for i, operation in enumerate(cleaning_operations):
            op_type = operation.get("type")
            op_params = operation.get("params", {})
            op_description = operation.get("description", f"Operation {i+1}")

            original_row_count = len(df)
            original_df = df.copy()

            try:
                if op_type == "remove_duplicates":
                    keep = op_params.get("keep", "first")
                    subset = op_params.get("columns")
                    if subset:
                        # Validate columns exist
                        missing_cols = [col for col in subset if col not in df.columns]
                        if missing_cols:
                            return {"error": f"Columns not found for duplicate removal: {missing_cols}"}
                    df = df.drop_duplicates(subset=subset, keep=keep)

                elif op_type == "remove_nulls":
                    subset = op_params.get("columns")
                    if subset:
                        # Validate columns exist
                        missing_cols = [col for col in subset if col not in df.columns]
                        if missing_cols:
                            return {"error": f"Columns not found for null removal: {missing_cols}"}
                    df = df.dropna(subset=subset)

                elif op_type == "fill_nulls":
                    fill_value = op_params.get("value")
                    method = op_params.get("method")
                    subset = op_params.get("columns")

                    if fill_value is not None:
                        if subset:
                            # Validate columns exist
                            missing_cols = [col for col in subset if col not in df.columns]
                            if missing_cols:
                                return {"error": f"Columns not found for null filling: {missing_cols}"}
                        df = df.fillna({col: fill_value for col in (subset if subset else df.columns)} if subset else fill_value)
                    elif method:
                        if subset:
                            # Validate columns exist
                            missing_cols = [col for col in subset if col not in df.columns]
                            if missing_cols:
                                return {"error": f"Columns not found for null filling method: {missing_cols}"}
                        df = df.fillna(method=method, axis=0)
                    else:
                        return {"error": "Either 'value' or 'method' must be specified for fill_nulls operation"}

                elif op_type == "filter_rows":
                    condition = op_params.get("condition")
                    if not condition:
                        return {"error": "Condition must be specified for filter_rows operation"}
                    # Simple query - in production, you'd want to use pd.query() safely
                    try:
                        df = df.query(condition)
                    except Exception:
                        return {"error": f"Invalid filter condition: {condition}"}

                elif op_type == "select_columns":
                    columns = op_params.get("columns")
                    if not columns:
                        return {"error": "Columns must be specified for select_columns operation"}
                    # Validate columns exist
                    missing_cols = [col for col in columns if col not in df.columns]
                    if missing_cols:
                        return {"error": f"Columns not found: {missing_cols}"}
                    df = df[columns]

                elif op_type == "rename_columns":
                    mapping = op_params.get("mapping")
                    if not mapping:
                        return {"error": "Mapping must be specified for rename_columns operation"}
                    # Validate columns exist
                    missing_cols = [col for col in mapping.keys() if col not in df.columns]
                    if missing_cols:
                        return {"error": f"Columns not found for renaming: {missing_cols}"}
                    df = df.rename(columns=mapping)

                else:
                    return {"error": f"Unsupported cleaning operation type: {op_type}"}

                # Track changes
                rows_after = len(df)
                rows_changed = abs(original_row_count - rows_after)

                operations_applied.append({
                    "operation": op_type,
                    "description": op_description,
                    "rows_before": original_row_count,
                    "rows_after": rows_after,
                    "rows_changed": rows_changed
                })

            except Exception as e:
                return {"error": f"Error applying operation '{op_type}': {str(e)}"}

        # Save the cleaned dataset
        _save_file(df, output_path)

        result = {
            "path": path,
            "output_path": output_path,
            "total_operations": len(cleaning_operations),
            "operations_applied": operations_applied,
            "rows_before": total_rows_before,
            "rows_after": len(df),
            "rows_changed": total_rows_before - len(df),
            "columns_before": len(_load_file(path).columns),
            "columns_after": len(df.columns)
        }

        return result
    except Exception as e:
        return {"error": str(e)}


@server.tool()
async def convert_file(
    path: str,
    output_path: str,
    output_format: Optional[str] = None
) -> Dict[str, Any]:
    """Convert a file from one format to another.

    Args:
        path: Path to the input file
        output_path: Path where the converted file should be saved
        output_format: Desired output format. If None, inferred from output_path extension.

    Returns:
        Dictionary containing conversion results including success status and file information
    """
    try:
        # Load the input file
        df = _load_file(path)

        # Determine output format
        if output_format is None:
            output_format = os.path.splitext(output_path)[1].lower()
            if output_format.startswith('.'):
                output_format = output_format[1:]

        # Validate output format
        supported_formats = ['csv', 'tsv', 'json', 'jsonl', 'xlsx', 'xls', 'parquet']
        if output_format not in supported_formats:
            return {"error": f"Unsupported output format: {output_format}. Supported formats: {supported_formats}"}

        # Save in the requested format
        _save_file(df, output_path)

        result = {
            "path": path,
            "output_path": output_path,
            "output_format": output_format,
            "rows_converted": len(df),
            "columns_converted": len(df.columns),
            "success": True
        }

        return result
    except Exception as e:
        return {"error": str(e)}


@server.tool()
async def generate_report(
    path: str,
    report_type: str = "summary",
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """Generate a comprehensive report of a dataset.

    Args:
        path: Path to the dataset file
        report_type: Type of report to generate ("summary", "profile", "quality")
        output_path: Optional path to save the report. If not provided, returns report as dictionary.

    Returns:
        Dictionary containing the report or confirmation of file saved
    """
    try:
        df = _load_file(path)

        if report_type == "summary":
            report = {
                "dataset_overview": {
                    "path": path,
                    "rows": len(df),
                    "columns": len(df.columns),
                    "size_in_bytes": df.memory_usage(deep=True).sum(),
                    "memory_usage": f"{df.memory_usage(deep=True).sum() / 1024:.2f} KB"
                },
                "column_info": {
                    "total_columns": len(df.columns),
                    "column_types": {str(dtype): int(count) for dtype, count in df.dtypes.value_counts().items()},
                    "columns": list(df.columns)
                },
                "data_quality": {
                    "total_cells": df.size,
                    "missing_cells": int(df.isnull().sum().sum()),
                    "missing_percentage": (df.isnull().sum().sum() / df.size * 100) if df.size > 0 else 0,
                    "duplicate_rows": int(df.duplicated().sum()),
                    "duplicate_percentage": (df.duplicated().sum() / len(df) * 100) if len(df) > 0 else 0
                }
            }

        elif report_type == "profile":
            # Reuse profile_dataset logic
            profile_result = await profile_dataset(path)
            if "error" in profile_result:
                return profile_result
            report = {
                "dataset_path": path,
                "profile": profile_result
            }

        elif report_type == "quality":
            # Quality-focused report
            quality_score = 100  # Start with perfect score

            # Penalties for various issues
            missing_penalty = (df.isnull().sum().sum() / df.size * 30) if df.size > 0 else 0  # Max 30 points
            duplicate_penalty = (df.duplicated().sum() / len(df) * 20) if len(df) > 0 else 0  # Max 20 points

            # Check for constant columns (low information value)
            constant_cols = 0
            for col in df.columns:
                if df[col].nunique() <= 1:
                    constant_cols += 1
            constant_penalty = (constant_cols / len(df.columns) * 15) if len(df.columns) > 0 else 0  # Max 15 points

            quality_score = max(0, quality_score - missing_penalty - duplicate_penalty - constant_penalty)

            report = {
                "dataset_path": path,
                "quality_assessment": {
                    "overall_score": round(quality_score, 2),
                    "missing_data_penalty": round(missing_penalty, 2),
                    "duplicate_penalty": round(duplicate_penalty, 2),
                    "constant_columns_penalty": round(constant_penalty, 2),
                    "grade": "A" if quality_score >= 90 else "B" if quality_score >= 80 else "C" if quality_score >= 70 else "D" if quality_score >= 60 else "F"
                },
                "detailed_metrics": {
                    "total_rows": len(df),
                    "total_columns": len(df.columns),
                    "missing_cells": int(df.isnull().sum().sum()),
                    "missing_percentage": round(df.isnull().sum().sum() / df.size * 100, 2) if df.size > 0 else 0,
                    "duplicate_rows": int(df.duplicated().sum()),
                    "duplicate_percentage": round(df.duplicated().sum() / len(df) * 100, 2) if len(df) > 0 else 0,
                    "constant_columns": constant_cols,
                    "constant_columns_percentage": round(constant_cols / len(df.columns) * 100, 2) if len(df.columns) > 0 else 0
                }
            }

        else:
            return {"error": f"Unsupported report type: {report_type}. Supported types: summary, profile, quality"}

        # Save report if output_path provided
        if output_path:
            import json
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)

            return {
                "path": path,
                "report_type": report_type,
                "output_path": output_path,
                "report_saved": True
            }
        else:
            return {
                "path": path,
                "report_type": report_type,
                "report": report
            }
    except Exception as e:
        return {"error": str(e)}


@server.tool()
async def preview_changes(
    path: str,
    changes_preview: List[Dict[str, Any]],
    rows_to_show: int = 5
) -> Dict[str, Any]:
    """Preview what changes would be made to a dataset without actually applying them.

    Args:
        path: Path to the dataset file
        changes_preview: List of changes to preview (same format as cleaning_operations)
        rows_to_show: Number of rows to show in the preview (default: 5)

    Returns:
        Dictionary containing preview of changes including before/after comparisons
    """
    try:
        df = _load_file(path)

        if rows_to_show < 1:
            rows_to_show = 1
        if rows_to_show > len(df):
            rows_to_show = len(df)

        # Get sample rows for preview
        sample_indices = df.head(rows_to_show).index.tolist()
        sample_df = df.loc[sample_indices].copy()

        # Track what would happen to the sample
        preview_results = []
        current_sample = sample_df.copy()

        for i, change in enumerate(changes_preview):
            change_type = change.get("type")
            change_params = change.get("params", {})
            change_description = change.get("description", f"Change {i+1}")

            try:
                if change_type == "remove_duplicates":
                    keep = change_params.get("keep", "first")
                    subset = change_params.get("columns")
                    if subset:
                        # Validate columns exist
                        missing_cols = [col for col in subset if col not in current_sample.columns]
                        if missing_cols:
                            return {"error": f"Columns not found for duplicate removal: {missing_cols}"}
                    preview_df = current_sample.drop_duplicates(subset=subset, keep=keep)

                elif change_type == "remove_nulls":
                    subset = change_params.get("columns")
                    if subset:
                        # Validate columns exist
                        missing_cols = [col for col in subset if col not in current_sample.columns]
                        if missing_cols:
                            return {"error": f"Columns not found for null removal: {missing_cols}"}
                    preview_df = current_sample.dropna(subset=subset)

                elif change_type == "fill_nulls":
                    fill_value = change_params.get("value")
                    method = change_params.get("method")
                    subset = change_params.get("columns")

                    if fill_value is not None:
                        if subset:
                            # Validate columns exist
                            missing_cols = [col for col in subset if col not in current_sample.columns]
                            if missing_cols:
                                return {"error": f"Columns not found for null filling: {missing_cols}"}
                        preview_df = current_sample.fillna({col: fill_value for col in (subset if subset else current_sample.columns)} if subset else fill_value)
                    elif method:
                        if subset:
                            # Validate columns exist
                            missing_cols = [col for col in subset if col not in current_sample.columns]
                            if missing_cols:
                                return {"error": f"Columns not found for null filling method: {missing_cols}"}
                        preview_df = current_sample.fillna(method=method, axis=0)
                    else:
                        return {"error": "Either 'value' or 'method' must be specified for fill_nulls operation"}

                elif change_type == "filter_rows":
                    condition = change_params.get("condition")
                    if not condition:
                        return {"error": "Condition must be specified for filter_rows operation"}
                    try:
                        preview_df = current_sample.query(condition)
                    except Exception:
                        return {"error": f"Invalid filter condition: {condition}"}

                elif change_type == "select_columns":
                    columns = change_params.get("columns")
                    if not columns:
                        return {"error": "Columns must be specified for select_columns operation"}
                    # Validate columns exist
                    missing_cols = [col for col in columns if col not in current_sample.columns]
                    if missing_cols:
                        return {"error": f"Columns not found: {missing_cols}"}
                    preview_df = current_sample[columns]

                elif change_type == "rename_columns":
                    mapping = change_params.get("mapping")
                    if not mapping:
                        return {"error": "Mapping must be specified for rename_columns operation"}
                    # Validate columns exist
                    missing_cols = [col for col in mapping.keys() if col not in current_sample.columns]
                    if missing_cols:
                        return {"error": f"Columns not found for renaming: {missing_cols}"}
                    preview_df = current_sample.rename(columns=mapping)

                else:
                    return {"error": f"Unsupported change type: {change_type}"}

                # Store preview for this step
                preview_results.append({
                    "step": i + 1,
                    "operation": change_type,
                    "description": change_description,
                    "before": current_sample.head(rows_to_show).to_dict('records'),
                    "after": preview_df.head(rows_to_show).to_dict('records') if len(preview_df) > 0 else [],
                    "rows_before": len(current_sample),
                    "rows_after": len(preview_df)
                })

                # Update current sample for next iteration
                current_sample = preview_df

            except Exception as e:
                return {"error": f"Error previewing operation '{change_type}': {str(e)}"}

        result = {
            "path": path,
            "rows_previewed": rows_to_show,
            "total_changes_previewed": len(changes_preview),
            "previews": preview_results,
            "final_row_count_after_all_changes": len(current_sample) if len(preview_results) > 0 else len(df)
        }

        return result
    except Exception as e:
        return {"error": str(e)}


@server.tool()
async def create_sanitized_copy(
    path: str,
    sanitization_rules: Dict[str, Any],
    output_path: str
) -> Dict[str, Any]:
    """Create a sanitized copy of a dataset based on specified rules.

    Args:
        path: Path to the dataset file
        sanitization_rules: Dictionary defining what to sanitize and how
        output_path: Path where the sanitized copy should be saved

    Returns:
        Dictionary containing sanitization results including statistics and output path
    """
    try:
        df = _load_file(path)

        # Track changes
        changes_made = {}
        columns_processed = []

        # Apply sanitization rules
        for col, rules in sanitization_rules.items():
            if col not in df.columns:
                continue

            columns_processed.append(col)
            original_series = df[col].copy()
            col_changes = 0

            # Apply each sanitization rule
            if "pii_detection" in rules and rules["pii_detection"]:
                # Simple PII detection and redaction for demonstration
                import re
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                phone_pattern = r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'

                def redact_pii(text):
                    if pd.isnull(text) or not isinstance(text, str):
                        return text
                    text = re.sub(email_pattern, '[EMAIL]', text)
                    text = re.sub(phone_pattern, '[PHONE]', text)
                    return text

                df[col] = df[col].apply(redact_pii)

            if "mask_numeric" in rules and rules["mask_numeric"]:
                try:
                    # Show only last 4 digits for numeric IDs
                    df[col] = df[col].apply(
                        lambda x: '*' * (len(str(x)) - 4) + str(x)[-4:] if pd.notnull(x) and len(str(x)) > 4 else x
                    )
                except Exception:
                    pass  # Keep original if transformation fails

            if "hash_values" in rules and rules["hash_values"]:
                import hashlib
                df[col] = df[col].apply(
                    lambda x: hashlib.sha256(str(x)).hexdigest() if pd.notnull(x) and str(x) != "" else x
                )

            if "remove_column" in rules and rules["remove_column"]:
                # Mark for removal (we'll drop the column after processing all rules)
                df[col] = "[REMOVED_COLUMN]"

            if "fixed_value" in rules:
                fixed_val = rules["fixed_value"]
                df[col] = fixed_val

            # Count changes
            col_changes = (original_series != df[col]).sum()
            if col_changes > 0 or "remove_column" in rules:
                changes_made[col] = int(col_changes)

        # Remove columns marked for removal
        columns_to_remove = [col for col, rules in sanitization_rules.items()
                           if rules.get("remove_column", False) and col in df.columns]
        if columns_to_remove:
            df = df.drop(columns=columns_to_remove)
            # Update columns_processed to reflect final state
            columns_processed = [col for col in columns_processed if col not in columns_to_remove]

        # Save the sanitized copy
        _save_file(df, output_path)

        result = {
            "path": path,
            "output_path": output_path,
            "sanitization_rules": sanitization_rules,
            "columns_processed": columns_processed,
            "columns_removed": columns_to_remove,
            "changes_by_column": changes_made,
            "total_changes_made": sum(changes_made.values()),
            "rows_processed": len(df),
            "columns_before": len(_load_file(path).columns),
            "columns_after": len(df.columns)
        }

        return result
    except Exception as e:
        return {"error": str(e)}


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())