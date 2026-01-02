#!/usr/bin/env python3
"""
Quick test script for Groq integration
"""
import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from scripts.test_llm_pipeline import generate_sql_with_validation, build_plan_sql_prompt

async def test_groq():
    """Test Groq API with a simple SQL generation"""
    # Check for required environment variables
    groq_key = os.getenv('GROQ_API_KEY')
    if not groq_key:
        print("❌ Error: GROQ_API_KEY environment variable not set")
        print("   Set it with: export GROQ_API_KEY=your_key_here")
        return False
    
    # Set environment (use existing or defaults)
    os.environ.setdefault('LLM_PROVIDER', 'groq')
    os.environ.setdefault('GROQ_MODEL', 'llama-3.1-8b-instant')
    os.environ.setdefault('LLM_TIMEOUT', '30')
    
    question = "What are the top 5 pickup zones?"
    model = "llama-3.1-8b-instant"
    timeout = 30.0
    
    print(f"🧪 Testing Groq API")
    print(f"Question: {question}")
    print("=" * 60)
    
    try:
        print("\n📝 Generating SQL with Groq...")
        sql = await generate_sql_with_validation(
            question, 
            model, 
            timeout, 
            max_attempts=2, 
            verbose=True
        )
        
        if sql:
            print(f"\n✅ Success! Generated SQL:")
            print("-" * 60)
            print(sql)
            print("-" * 60)
            return True
        else:
            print("\n❌ Failed to generate SQL")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_groq())
    sys.exit(0 if success else 1)

