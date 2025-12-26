"""
Query engine with safe SQL execution
"""
import duckdb
from typing import Dict, Any, List, Optional
import time

ALLOWED_VIEWS = ["fhv_raw", "fhv_clean", "fhv_with_zones", "fhv_with_company", "taxi_zones", "base_lookup"]
DANGEROUS_KEYWORDS = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", "TRUNCATE", "GRANT", "REVOKE"]
MAX_EXECUTION_TIME = 30  # seconds
MAX_ROWS_RETURNED = 10000


class QueryEngine:
    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self.conn = conn
    
    def execute_safe_sql(self, sql: str) -> Dict[str, Any]:
        """Execute SQL with safety checks"""
        sql_upper = sql.upper().strip()
        
        # Check for dangerous keywords
        for keyword in DANGEROUS_KEYWORDS:
            if keyword in sql_upper:
                raise ValueError(f"Dangerous keyword '{keyword}' not allowed")
        
        # Check if query uses allowed views (case-insensitive)
        uses_allowed_view = any(view.upper() in sql_upper for view in ALLOWED_VIEWS)
        if not uses_allowed_view and "SELECT" in sql_upper:
            raise ValueError("Query must use one of the allowed views")
        
        # Ensure LIMIT for non-aggregate queries
        if "GROUP BY" not in sql_upper and "LIMIT" not in sql_upper:
            sql = sql.rstrip(";") + " LIMIT " + str(MAX_ROWS_RETURNED)
        
        # Execute with timeout
        start_time = time.time()
        try:
            result = self.conn.execute(sql).fetchdf()
            
            if time.time() - start_time > MAX_EXECUTION_TIME:
                raise ValueError("Query execution timeout")
            
            # Limit rows
            if len(result) > MAX_ROWS_RETURNED:
                result = result.head(MAX_ROWS_RETURNED)
            
            return {
                "data": result.to_dict("records"),
                "row_count": len(result),
                "sql": sql
            }
        except Exception as e:
            raise ValueError(f"SQL execution error: {str(e)}")
    
    def execute_template(self, template_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a predefined metric template"""
        from query.metrics import MetricTemplates
        templates = MetricTemplates()
        template = templates.get_template(template_name)
        
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        
        sql = template["sql"].format(**params)
        result = self.execute_safe_sql(sql)
        
        return {
            **result,
            "chart": template.get("chart_config", {}),
            "summary": self._generate_summary(result["data"], template_name)
        }
    
    def _generate_summary(self, data: List[Dict], template_name: str) -> Dict[str, Any]:
        """Generate summary statistics for template results"""
        if not data:
            return {}
        
        # Simple summary based on template
        if "hourly" in template_name:
            total = sum(row.get("trips", 0) for row in data)
            return {"total_trips": total, "hours": len(data)}
        elif "market_share" in template_name:
            return {"companies": len(data)}
        else:
            return {"rows": len(data)}

