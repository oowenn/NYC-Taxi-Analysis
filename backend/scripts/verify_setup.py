"""
Verify backend setup is correct
"""
import sys
from pathlib import Path
import os

sys.path.insert(0, str(Path(__file__).parent.parent))

def verify_setup():
    """Verify all components are set up correctly"""
    print("Verifying backend setup...\n")
    
    errors = []
    warnings = []
    
    # Check data files
    data_dir = Path("../data")
    if not data_dir.exists():
        errors.append("Data directory not found")
    else:
        parquet_files = list(data_dir.glob("fhvhv_tripdata_2023-*.parquet"))
        if not parquet_files:
            warnings.append("No Parquet files found in data/ directory")
        else:
            print(f"✓ Found {len(parquet_files)} Parquet files")
        
        if not (data_dir / "taxi_zone_lookup.csv").exists():
            errors.append("taxi_zone_lookup.csv not found")
        else:
            print("✓ Found taxi_zone_lookup.csv")
        
        if not (data_dir / "fhv_base_lookup.csv").exists():
            warnings.append("fhv_base_lookup.csv not found (create this file)")
        else:
            print("✓ Found fhv_base_lookup.csv")
    
    # Check environment
    env_file = Path(".env")
    if not env_file.exists():
        warnings.append(".env file not found (copy from .env.example)")
    else:
        print("✓ Found .env file")
    
    # Check docs
    docs_dir = Path("../docs")
    if docs_dir.exists():
        md_files = list(docs_dir.glob("*.md"))
        print(f"✓ Found {len(md_files)} documentation files")
    else:
        warnings.append("docs/ directory not found")
    
    # Try importing modules
    try:
        import duckdb
        print("✓ DuckDB imported successfully")
    except ImportError:
        errors.append("DuckDB not installed (pip install duckdb)")
    
    try:
        from db.duckdb_setup import init_duckdb, close_duckdb
        print("✓ DuckDB setup module imports successfully")
        
        # Try initializing (this will fail if data files missing)
        try:
            conn = init_duckdb()
            print("✓ DuckDB initialized successfully")
            close_duckdb(conn)
        except Exception as e:
            errors.append(f"DuckDB initialization failed: {e}")
    except ImportError as e:
        errors.append(f"Import error: {e}")
    
    # Summary
    print("\n" + "="*50)
    if errors:
        print("❌ ERRORS:")
        for err in errors:
            print(f"  - {err}")
    
    if warnings:
        print("\n⚠️  WARNINGS:")
        for warn in warnings:
            print(f"  - {warn}")
    
    if not errors and not warnings:
        print("✅ All checks passed! Backend is ready to run.")
    elif not errors:
        print("\n✅ Setup complete with warnings (non-critical)")
    else:
        print("\n❌ Setup incomplete. Fix errors above.")
    
    return len(errors) == 0


if __name__ == "__main__":
    success = verify_setup()
    sys.exit(0 if success else 1)

