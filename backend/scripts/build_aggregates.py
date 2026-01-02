"""
Precompute common aggregates and save to JSON
This can be run periodically to update cached metrics
"""
import os
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.duckdb_setup import init_duckdb, close_duckdb
from query.metrics import MetricTemplates

OUTPUT_DIR = Path("../data/aggregates")


def build_aggregates():
    """Build and save common aggregates"""
    conn = init_duckdb()
    templates = MetricTemplates()
    
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    aggregates = {}
    
    # Build each template
    for template_name in templates.templates.keys():
        print(f"Building {template_name}...")
        try:
            template = templates.get_template(template_name)
            result = conn.execute(template["sql"]).fetchdf()
            
            aggregates[template_name] = {
                "data": result.to_dict("records"),
                "chart": template["chart_config"],
                "last_updated": __import__("datetime").datetime.now().isoformat()
            }
            
            # Save individual file
            output_file = OUTPUT_DIR / f"{template_name}.json"
            with open(output_file, 'w') as f:
                json.dump(aggregates[template_name], f, indent=2)
            
            print(f"  Saved {len(result)} rows to {output_file}")
        except Exception as e:
            print(f"  Error building {template_name}: {e}")
    
    # Save combined file
    combined_file = OUTPUT_DIR / "all_aggregates.json"
    with open(combined_file, 'w') as f:
        json.dump(aggregates, f, indent=2)
    
    print(f"\nAll aggregates saved to {OUTPUT_DIR}")
    
    close_duckdb(conn)


if __name__ == "__main__":
    build_aggregates()

