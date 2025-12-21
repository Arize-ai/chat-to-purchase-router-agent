"""
Natural language to SQL query conversion using LLM.
"""
import os
import re
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
import openai
from backend.agent.db import execute_query

logger = logging.getLogger(__name__)

# Database schema description
SCHEMA_DESCRIPTION = """
Database Schema:
- Table: products
  - id: INTEGER (PRIMARY KEY)
  - name: VARCHAR(255)
  - description: TEXT
  - price: DECIMAL(10, 2)
  - rating: DECIMAL(3, 2) (0-5 scale)
  - category: VARCHAR(100)
  - image_path: VARCHAR(500)
"""

# Valid categories in the database (lowercase as stored in DB)
VALID_CATEGORIES = [
    "ankle boots",
    "athletic shoes",
    "boots",
    "casual shoes",
    "creepers",
    "dress shoes",
    "flats",
    "heels",
    "hiking shoes",
    "loafers",
    "sneakers",
    "work shoes"
]


def _generate_sql_from_nl(query: str) -> Tuple[str, Optional[tuple]]:
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    valid_categories_str = ", ".join(VALID_CATEGORIES)
    
    prompt = f"""You are a SQL query generator. Convert the following natural language query to a PostgreSQL SELECT statement.

    {SCHEMA_DESCRIPTION}

    Valid Categories (use exact match, case-sensitive, all lowercase): {valid_categories_str}

    Natural Language Query: "{query}"

    CRITICAL SECURITY RULES - YOU MUST FOLLOW THESE:
    - Generate ONLY SELECT statements - NEVER use INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, TRUNCATE, EXEC, or EXECUTE
    - Query ONLY the products table - do not access any other tables
    - Return ONLY the SQL query, no explanations, no markdown, no code blocks
    - Generate valid, executable PostgreSQL SQL that will run without errors

    Query Rules:
    - Only SELECT from products table
    - For category filtering: Match the user's category request to one of the valid categories above. Use exact match with = operator (e.g., category = 'Athletic shoes'), f the query doesn't match any valid category, do NOT filter by category.
    - For name/brand searches: Use ILIKE with wildcards (e.g., name ILIKE '%Nike%')
    - Return all columns: SELECT * FROM products
    - Add LIMIT 50 to prevent huge result sets
    - Use actual values in the query (not parameterized)
    - For price comparisons, use direct numeric values (e.g., price <= 100.0)
    - For ratings, use direct numeric values (e.g., rating >= 4.0)

    Examples:
    Query: "running shoes under $100"
    SQL: SELECT * FROM products WHERE category = 'athletic shoes' AND price <= 100.0 LIMIT 50

    Query: "highly rated casual shoes"
    SQL: SELECT * FROM products WHERE category = 'casual shoes' AND rating >= 4.0 LIMIT 50

    Query: "Nike products"
    SQL: SELECT * FROM products WHERE name ILIKE '%Nike%' LIMIT 50

    Query: "cheapest sneakers"
    SQL: SELECT * FROM products WHERE category = 'sneakers' ORDER BY price ASC LIMIT 50

    Query: "shoes under $50"
    SQL: SELECT * FROM products WHERE price <= 50.0 LIMIT 50

    IMPORTANT: If you cannot generate valid SQL from the given information, return an empty string "" instead of generating invalid SQL.

    Now convert this query: "{query}"
    SQL:"""

    response = client.chat.completions.create(
        model="gpt-4o-mini", 
        messages=[
            {"role": "system", "content": "You are a SQL query generator. Return only SQL queries, no explanations."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1, 
        max_tokens=200,
    )
    
    sql = response.choices[0].message.content.strip()
    
    return sql, None

def search_products_nl(query: str) -> Union[List[Dict[str, Any]], str]:
    
    sql, params = _generate_sql_from_nl(query.strip())
    
    sql_clean = sql.strip() if sql else ""
    print(f"SQL clean: {repr(sql_clean)}")
    if not sql_clean:
        return "I couldn't generate a valid search query from your request. Please try rephrasing your search."
    
    print(f"Executing SQL query: {sql}")
    
    try:
        results = execute_query(sql, params)
        if not results:
            return "I couldn't find any products matching your search in our catalog."
        return f"Found {len(results)} product(s): {results}"
    except Exception as e:
        logger.error(f"Error executing SQL query: {e}")
        return "I encountered an error while searching. Please try again."
        


