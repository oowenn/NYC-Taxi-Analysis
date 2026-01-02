"""
Test end-to-end: hourly trips by company
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.duckdb_setup import init_duckdb, close_duckdb
from query.engine import QueryEngine
from query.metrics import MetricTemplates

def test_hourly_trips():
    """Test hourly trips by company query"""
    print("Testing hourly trips by company...")
    
    conn = init_duckdb()
    query_engine = QueryEngine(conn)
    templates = MetricTemplates()
    
    # Match template
    match = templates.match("show hourly trips by company")
    print(f"Template match: {match}")
    
    if match:
        # Execute template
        result = query_engine.execute_template(match["template"], match.get("params", {}))
        
        print(f"\nSQL:\n{result['sql']}")
        print(f"\nRows returned: {result['row_count']}")
        print(f"\nFirst 5 rows:")
        for row in result['data'][:5]:
            print(row)
        
        print(f"\nChart config: {result['chart']}")
        print(f"\nSummary: {result['summary']}")
        
        print("\n✅ Test passed!")
    else:
        print("❌ Template matching failed")
    
    close_duckdb(conn)


if __name__ == "__main__":
    test_hourly_trips()

