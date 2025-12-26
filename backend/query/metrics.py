"""
Predefined metric templates for common queries
"""
from typing import Dict, Any, Optional
import re


class MetricTemplates:
    def __init__(self):
        self.templates = {
            "hourly_trips_by_company": {
                "sql": """
                    SELECT 
                        EXTRACT(HOUR FROM pickup_datetime) AS hour,
                        company,
                        COUNT(*) AS trips
                    FROM fhv_with_company
                    WHERE pickup_datetime >= CURRENT_DATE - INTERVAL 30 DAY
                    GROUP BY hour, company
                    ORDER BY hour, company
                """,
                "chart_config": {
                    "type": "line",
                    "x": "hour",
                    "y": "trips",
                    "series": "company",
                    "title": "Hourly Trips by Company"
                },
                "answer_template": "Here are hourly trips by company over the last 30 days. Total trips: {total_trips:,} across {hours} hours.",
                "keywords": ["hourly", "trips", "company", "hour", "by company"]
            },
            "market_share": {
                "sql": """
                    SELECT 
                        company,
                        COUNT(*) AS trips,
                        ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS market_share_pct
                    FROM fhv_with_company
                    WHERE pickup_datetime >= CURRENT_DATE - INTERVAL 30 DAY
                    GROUP BY company
                    ORDER BY trips DESC
                """,
                "chart_config": {
                    "type": "bar",
                    "x": "company",
                    "y": "market_share_pct",
                    "title": "Market Share by Company"
                },
                "answer_template": "Market share by company over the last 30 days:",
                "keywords": ["market share", "market", "share", "company share"]
            },
            "top_zones": {
                "sql": """
                    SELECT 
                        pickup_zone,
                        pickup_borough,
                        COUNT(*) AS trips
                    FROM fhv_with_company
                    WHERE pickup_datetime >= CURRENT_DATE - INTERVAL 30 DAY
                    GROUP BY pickup_zone, pickup_borough
                    ORDER BY trips DESC
                    LIMIT 20
                """,
                "chart_config": {
                    "type": "bar",
                    "x": "pickup_zone",
                    "y": "trips",
                    "title": "Top 20 Pickup Zones"
                },
                "answer_template": "Top 20 pickup zones over the last 30 days:",
                "keywords": ["top zones", "pickup zones", "popular zones", "busiest zones"]
            }
        }
    
    def get_template(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a template by name"""
        return self.templates.get(name)
    
    def match(self, query: str) -> Optional[Dict[str, Any]]:
        """Match query to a template"""
        query_lower = query.lower()
        
        for name, template in self.templates.items():
            keywords = template.get("keywords", [])
            if any(keyword in query_lower for keyword in keywords):
                return {
                    "template": name,
                    "params": {}
                }
        
        return None

