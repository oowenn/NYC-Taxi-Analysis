"""
Agent-style validation tools for SQL and Python code
"""
import re
import ast
from typing import Dict, List, Optional, Tuple, Any
import duckdb


# Schema information for fhv_with_company view
FHV_COLUMNS = {
    "pickup_datetime", "dropoff_datetime", "company", "hvfhs_license_num",
    "trip_miles", "trip_time", "PULocationID", "DOLocationID",
    "pickup_borough", "pickup_zone", "dropoff_borough", "dropoff_zone",
    "base_name", "originating_base_num", "dispatching_base_num",
    "request_datetime", "on_scene_datetime"
}

ALLOWED_VIEWS = {"fhv_with_company", "fhv_with_zones", "fhv_clean", "fhv_raw", "taxi_zones", "base_lookup"}
DANGEROUS_KEYWORDS = {"DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", "TRUNCATE", "GRANT", "REVOKE"}


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


def validate_sql(sql: str, conn: Optional[duckdb.DuckDBPyConnection] = None) -> Tuple[bool, List[str]]:
    """
    Validate SQL query before execution.
    Returns (is_valid, list_of_errors)
    """
    errors = []
    sql_upper = sql.upper().strip()
    
    # 1. Safety checks
    for keyword in DANGEROUS_KEYWORDS:
        if keyword in sql_upper:
            errors.append(f"Dangerous keyword '{keyword}' not allowed")
    
    # 2. Check for allowed views
    uses_allowed_view = any(view.upper() in sql_upper for view in ALLOWED_VIEWS)
    if "SELECT" in sql_upper and not uses_allowed_view:
        errors.append(f"Query must use one of the allowed views: {', '.join(ALLOWED_VIEWS)}")
    
    # 3. Extract column references from SQL
    # Simple regex to find column names (after SELECT, in GROUP BY, ORDER BY, WHERE, etc.)
    column_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b'
    
    # Find all potential column references
    # This is a simplified check - we'll do a more thorough check with DuckDB if connection provided
    if conn:
        try:
            # Try to parse/explain the query to catch syntax errors
            try:
                explain_result = conn.execute(f"EXPLAIN {sql}").fetchall()
            except Exception as e:
                errors.append(f"SQL syntax error: {str(e)}")
                return (False, errors)
            
            # Try to get column info from a LIMIT 0 query
            try:
                test_sql = sql.rstrip(";")
                if "LIMIT" not in sql_upper:
                    test_sql += " LIMIT 0"
                else:
                    # Replace existing LIMIT with 0
                    test_sql = re.sub(r'\s+LIMIT\s+\d+', ' LIMIT 0', test_sql, flags=re.IGNORECASE)
                
                result = conn.execute(test_sql).fetchdf()
                result_columns = set(result.columns)
                
                # Check if any columns in SELECT/GROUP BY don't exist
                # This is a heuristic - we check if common invalid columns appear
                invalid_columns = {"start_time", "end_time", "timestamp", "date"}  # Common mistakes
                sql_lower = sql.lower()
                for invalid_col in invalid_columns:
                    if invalid_col in sql_lower and invalid_col not in {col.lower() for col in result_columns}:
                        # Check if it's actually used (not just in a comment)
                        pattern = rf'\b{invalid_col}\b'
                        if re.search(pattern, sql_lower):
                            # Suggest correct column
                            if "start" in invalid_col or "pickup" in sql_lower:
                                errors.append(f"Column '{invalid_col}' not found. Did you mean 'pickup_datetime'?")
                            elif "end" in invalid_col or "dropoff" in sql_lower:
                                errors.append(f"Column '{invalid_col}' not found. Did you mean 'dropoff_datetime'?")
                
            except Exception as e:
                error_msg = str(e)
                # Check for common column errors
                if "column" in error_msg.lower() and "not found" in error_msg.lower():
                    # Extract column name from error
                    match = re.search(r'column\s+["\']?([^"\']+)["\']?', error_msg, re.IGNORECASE)
                    if match:
                        col_name = match.group(1)
                        if "time" in col_name.lower() or "date" in col_name.lower():
                            if "start" in col_name.lower() or "pickup" in col_name.lower():
                                errors.append(f"Column '{col_name}' not found. Use 'pickup_datetime' instead.")
                            elif "end" in col_name.lower() or "dropoff" in col_name.lower():
                                errors.append(f"Column '{col_name}' not found. Use 'dropoff_datetime' instead.")
                        else:
                            errors.append(f"Column error: {error_msg}")
                    else:
                        errors.append(f"SQL execution error: {error_msg}")
                else:
                    errors.append(f"SQL execution error: {error_msg}")
        except Exception as e:
            # If we can't even explain, it's a syntax error
            errors.append(f"SQL syntax error: {str(e)}")
    
    # 4. Check for required patterns
    if "SELECT" in sql_upper:
        if "GROUP BY" in sql_upper and "LIMIT" not in sql_upper:
            errors.append("Queries with GROUP BY should include LIMIT for safety")
    
    return (len(errors) == 0, errors)


def validate_python_code(code: str) -> Tuple[bool, List[str]]:
    """
    Validate Python code syntax before execution.
    Returns (is_valid, list_of_errors)
    """
    errors = []
    
    # 1. Check for dangerous operations
    dangerous_patterns = [
        (r'\bimport\s+os\b', "Direct os import not allowed"),
        (r'\bimport\s+sys\b', "Direct sys import not allowed"),
        (r'\b__import__\b', "__import__ not allowed"),
        (r'\beval\s*\(', "eval() not allowed"),
        (r'\bexec\s*\(', "exec() not allowed (nested)"),
        (r'\bopen\s*\(', "open() not allowed"),
        (r'\bfile\s*\(', "file() not allowed"),
    ]
    
    for pattern, message in dangerous_patterns:
        if re.search(pattern, code):
            errors.append(message)
    
    # 2. Check Python syntax
    try:
        ast.parse(code)
    except SyntaxError as e:
        errors.append(f"Python syntax error: {e.msg} at line {e.lineno}")
    except Exception as e:
        errors.append(f"Python parse error: {str(e)}")
    
    # 3. Check for required matplotlib patterns
    if "plt." not in code and "matplotlib" not in code:
        errors.append("Code should use matplotlib (plt) for plotting")
    
    # 4. Check for forbidden operations
    if "plt.show()" in code:
        errors.append("plt.show() is not allowed in headless mode")
    
    return (len(errors) == 0, errors)


def build_sql_correction_prompt(question: str, sql: str, errors: List[str], attempt: int = 2, last_attempt: Optional[Dict[str, Any]] = None) -> str:
    """Build a prompt to ask LLM to correct SQL based on validation errors"""
    errors_text = "\n".join(f"- {e}" for e in errors)
    
    # Include context from only the last attempt if available
    previous_context = ""
    if last_attempt:
        prev_errors = last_attempt.get("errors", [])
        if prev_errors:
            prev_errors_text = "; ".join(prev_errors[:3])  # Limit to first 3 errors
            previous_context = f"\n\nNote: In the previous attempt, these errors occurred: {prev_errors_text}\n"
    
    return f"""
You previously generated this SQL query for the question: "{question}"

SQL (Attempt {attempt}):
{sql}

However, validation/execution found these errors:
{errors_text}
{previous_context}
Please correct the SQL query. Remember:
- Use view fhv_with_company
- Available columns: pickup_datetime (default time field), dropoff_datetime, company, hvfhs_license_num, trip_miles, trip_time, PULocationID, DOLocationID, pickup_borough, pickup_zone, dropoff_borough, dropoff_zone, base_name
- Use pickup_datetime for time filters unless the question explicitly asks for another column
- Include a time filter within 2023-01-01..2023-03-31
- Aggregate-first (GROUP BY); include LIMIT (e.g., 500)
- When counting trips, use COUNT(*) AS trips
- Pay close attention to the specific errors listed above and fix them directly

Output only the corrected SQL string, no extra text or code fences.
""".strip()


def build_code_correction_prompt(question: str, chart_plan: str, code: str, error: str, df_sample: Optional[str] = None, attempt: int = 2, last_attempt: Optional[Dict[str, Any]] = None, validation_errors: Optional[List[str]] = None) -> str:
    """Build a prompt to ask LLM to correct Python code based on execution/validation error"""
    sample_text = f"\n\nSample data (df.head()):\n{df_sample}" if df_sample else ""
    
    # Include validation errors if any
    validation_text = ""
    if validation_errors:
        validation_text = f"\n\nValidation errors (before execution):\n" + "\n".join(f"- {e}" for e in validation_errors)
    
    # Include context from only the last attempt if available
    previous_context = ""
    if last_attempt:
        prev_error = last_attempt.get("error", "Unknown error")
        if prev_error:
            prev_error_short = prev_error.split("\n")[0] if "\n" in prev_error else prev_error
            previous_context = f"\n\nNote: In the previous attempt, this error occurred: {prev_error_short}\n"
    
    return f"""
You previously generated this Python/matplotlib code for the question: "{question}"

Chart plan: {chart_plan}

Code (Attempt {attempt}):
{code}

However, execution/validation failed with this error:
{error}
{validation_text}
{previous_context}
{sample_text}

Please correct the code. Remember:
- Assume a pandas DataFrame named df already exists
- Imports are already done (pd, plt, np)
- Use only matplotlib + pandas (no seaborn/plotly)
- Do NOT call plt.show() or savefig() - caller will save
- IMPORTANT: Make axes readable:
  * If x-axis is time/timestamp, convert to readable format (e.g., pd.to_datetime() then format, or extract hour if hourly data)
  * If x-axis is numeric, ensure proper formatting and rotation if needed
  * Always set clear, descriptive labels using plt.xlabel() and plt.ylabel()
  * Use plt.xticks(rotation=...) if labels are long or overlapping
  * Set appropriate figure size (e.g., figsize=(12, 6) or larger for many data points)
- The code must be valid, executable Python
- Pay close attention to the specific error message above and fix it directly

Return JSON only:
{{
  "code": "corrected python code here"
}}
""".strip()

