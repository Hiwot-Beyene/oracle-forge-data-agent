"""
Schema Introspection Tool

Provides intelligent schema navigation for DAB datasets.
Prevents context window bloat by returning only relevant tables
and join paths for a given query.
"""

import re
import json
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum


class DatabaseType(Enum):
    """Supported database types in DAB."""
    POSTGRESQL = "postgresql"
    MONGODB = "mongodb"
    SQLITE = "sqlite"
    DUCKDB = "duckdb"


@dataclass
class TableInfo:
    """Information about a database table/collection."""
    name: str
    db_type: DatabaseType
    columns: Dict[str, str]  # column_name -> data_type
    primary_key: Optional[str] = None
    foreign_keys: Dict[str, str] = None  # column -> referenced_table.column
    description: str = ""
    row_count: Optional[int] = None


@dataclass
class JoinPath:
    """Path to join two tables across databases."""
    source_table: str
    source_db: DatabaseType
    target_table: str
    target_db: DatabaseType
    join_keys: List[Tuple[str, str]]  # (source_column, target_column)
    format_conversion: Optional[str] = None
    description: str = ""


class SchemaIntrospector:
    """
    Intelligent schema navigation for DAB datasets.
    
    Features:
    - Keyword-based table relevance scoring
    - Join path discovery across database boundaries
    - Format conversion detection for cross-DB joins
    """
    
    # Keyword mappings for table relevance
    TABLE_KEYWORDS = {
        # Yelp
        'business': ['yelp', 'businesses'],
        'review': ['yelp', 'reviews'],
        'user': ['yelp', 'users'],
        'tip': ['yelp', 'tips'],
        
        # CRMArenaPro
        'customer': ['crmarenapro', 'customers'],
        'ticket': ['crmarenapro', 'tickets'],
        'order': ['crmarenapro', 'orders'],
        'product': ['crmarenapro', 'products', 'order_items'],
        'campaign': ['crmarenapro', 'campaigns'],
        'opportunity': ['crmarenapro', 'opportunities'],
        
        # BookReview
        'book': ['bookreview', 'books'],
        'reviewer': ['bookreview', 'reviewers'],
        
        # AG News
        'article': ['agnews', 'articles'],
        'category': ['agnews', 'article_categories'],
        'news': ['agnews', 'articles'],
        
        # StockMarket
        'stock': ['stockmarket', 'stock_*'],
        'price': ['stockmarket', 'stock_*'],
        'financial': ['stockmarket', 'company_financials'],
        'analyst': ['stockmarket', 'analyst_ratings'],
        
        # PanCancer
        'patient': ['pancancer_atlas', 'patients'],
        'gene': ['pancancer_atlas', 'gene_expression'],
        'sample': ['pancancer_atlas', 'samples'],
        'expression': ['pancancer_atlas', 'gene_expression'],
    }
    
    # Known join paths across databases
    JOIN_PATHS: Dict[str, List[JoinPath]] = {
        'yelp': [
            JoinPath(
                source_table='businesses',
                source_db=DatabaseType.DUCKDB,
                target_table='reviews',
                target_db=DatabaseType.MONGODB,
                join_keys=[('business_id', 'business_id')],
                description='Join businesses with reviews'
            ),
            JoinPath(
                source_table='users',
                source_db=DatabaseType.DUCKDB,
                target_table='reviews',
                target_db=DatabaseType.MONGODB,
                join_keys=[('user_id', 'user_id')],
                description='Join users with reviews'
            ),
        ],
        'crmarenapro': [
            JoinPath(
                source_table='customers',
                source_db=DatabaseType.POSTGRESQL,
                target_table='tickets',
                target_db=DatabaseType.SQLITE,
                join_keys=[('customer_id', 'cust_id')],
                format_conversion='Strip "CUST-" prefix and zero-pad',
                description='Join customers with support tickets'
            ),
            JoinPath(
                source_table='order_items',
                source_db=DatabaseType.SQLITE,
                target_table='products',
                target_db=DatabaseType.SQLITE,
                join_keys=[('product_code', 'sku')],
                format_conversion=None,
                description='Join order items with product catalog'
            ),
            JoinPath(
                source_table='customers',
                source_db=DatabaseType.POSTGRESQL,
                target_table='orders',
                target_db=DatabaseType.SQLITE,
                join_keys=[('customer_id', 'customer_id')],
                description='Join customers with orders'
            ),
        ],
        'bookreview': [
            JoinPath(
                source_table='reviews',
                source_db=DatabaseType.POSTGRESQL,
                target_table='books',
                target_db=DatabaseType.SQLITE,
                join_keys=[('book_id', 'id')],
                description='Join reviews with books'
            ),
            JoinPath(
                source_table='reviews',
                source_db=DatabaseType.POSTGRESQL,
                target_table='reviewers',
                target_db=DatabaseType.SQLITE,
                join_keys=[('reviewer_id', 'user_id')],
                description='Join reviews with reviewers'
            ),
        ],
        'agnews': [
            JoinPath(
                source_table='articles',
                source_db=DatabaseType.MONGODB,
                target_table='article_categories',
                target_db=DatabaseType.SQLITE,
                join_keys=[('title', 'article_title')],
                format_conversion='Fuzzy match on title',
                description='Join articles with categories via title'
            ),
        ],
    }
    
    def __init__(self, kb_path: str = "kb"):
        """Initialize introspector with knowledge base path."""
        self.kb_path = kb_path
        self._schema_cache: Dict[str, Dict] = {}
    
    def extract_keywords(self, query_text: str) -> Set[str]:
        """
        Extract relevant keywords from query for table matching.
        
        Args:
            query_text: Natural language query
            
        Returns:
            Set of matched keywords
        """
        query_lower = query_text.lower()
        matched = set()
        
        for keyword in self.TABLE_KEYWORDS:
            if keyword in query_lower:
                matched.add(keyword)
        
        return matched
    
    def get_relevant_tables(
        self,
        dataset: str,
        query_text: str
    ) -> List[str]:
        """
        Return only tables relevant to the query.
        
        Args:
            dataset: Dataset name
            query_text: Natural language query
            
        Returns:
            List of relevant table names
        """
        keywords = self.extract_keywords(query_text)
        relevant_tables = set()
        
        for keyword in keywords:
            for entry in self.TABLE_KEYWORDS.get(keyword, []):
                if isinstance(entry, str) and entry == dataset:
                    continue
                if isinstance(entry, list) and entry[0] == dataset:
                    relevant_tables.update(entry[1:])
                elif entry == dataset:
                    # Add all tables for dataset
                    pass
        
        # If no keywords matched, return all tables
        if not relevant_tables:
            return self.get_all_tables(dataset)
        
        return list(relevant_tables)
    
    def get_all_tables(self, dataset: str) -> List[str]:
        """Return all tables for a dataset."""
        dataset_tables = {
            'yelp': ['businesses', 'users', 'checkins', 'reviews', 'tips'],
            'crmarenapro': [
                'customers', 'contacts', 'opportunities', 'activities',
                'orders', 'order_items', 'products', 'tickets', 'ticket_comments',
                'campaigns', 'campaign_members', 'customer_360', 'sales_forecast'
            ],
            'bookreview': ['reviews', 'books', 'reviewers'],
            'agnews': ['articles', 'article_categories', 'category_mapping', 'source_metadata'],
            'googlelocal': ['businesses', 'reviews'],
            'github_repos': ['repositories', 'contributors', 'weekly_stats', 'repo_topics', 'dependencies', 'releases'],
            'deps_dev_v1': ['packages', 'version_history', 'dependencies'],
            'music_brainz_20k': ['artists', 'recordings', 'artist_relations'],
            'pancancer_atlas': ['patients', 'samples', 'gene_expression'],
            'patents': ['patents', 'assignees', 'citations'],
            'stockindex': ['index_daily', 'index_components', 'index_info'],
            'stockmarket': ['all_stocks_metadata', 'company_financials', 'analyst_ratings'],
        }
        return dataset_tables.get(dataset, [])
    
    def get_table_schema(self, dataset: str, table_name: str) -> Optional[TableInfo]:
        """
        Get schema information for a specific table.
        
        Args:
            dataset: Dataset name
            table_name: Table/collection name
            
        Returns:
            TableInfo or None if not found
        """
        # Load schema from cache or file
        cache_key = f"{dataset}_{table_name}"
        if cache_key in self._schema_cache:
            return self._schema_cache[cache_key]
        
        schema_path = f"{self.kb_path}/domain/schemas/{dataset}_schema.md"
        
        try:
            with open(schema_path, 'r') as f:
                content = f.read()
                
                # Parse table section
                pattern = rf'###+\s*Table:\s*`?{re.escape(table_name)}`?.*?(?=###+|$)'
                match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
                
                if not match:
                    # Try collection pattern for MongoDB
                    pattern = rf'###+\s*Collection:\s*`?{re.escape(table_name)}`?.*?(?=###+|$)'
                    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
                
                if match:
                    # Parse columns from markdown table
                    section = match.group(0)
                    columns = self._parse_columns(section)
                    
                    # Determine database type
                    db_type = self._infer_db_type(dataset, table_name)
                    
                    table_info = TableInfo(
                        name=table_name,
                        db_type=db_type,
                        columns=columns,
                        description=section[:200]
                    )
                    
                    self._schema_cache[cache_key] = table_info
                    return table_info
                    
        except FileNotFoundError:
            pass
        
        return None
    
    def _parse_columns(self, markdown_section: str) -> Dict[str, str]:
        """Parse column definitions from markdown table."""
        columns = {}
        
        # Find markdown table
        table_pattern = r'\|.*\|.*\|.*\|'
        lines = re.findall(table_pattern, markdown_section)
        
        for line in lines[2:]:  # Skip header and separator
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 2:
                col_name = parts[0].strip('`')
                col_type = parts[1].strip('`')
                columns[col_name] = col_type
        
        return columns
    
    def _infer_db_type(self, dataset: str, table_name: str) -> DatabaseType:
        """Infer database type from dataset and table name."""
        # MongoDB collections
        mongodb_tables = {
            'yelp': ['reviews', 'tips'],
            'agnews': ['articles'],
        }
        
        if dataset in mongodb_tables:
            if table_name in mongodb_tables[dataset]:
                return DatabaseType.MONGODB
        
        # PostgreSQL tables
        postgres_tables = {
            'crmarenapro': ['customers', 'contacts', 'opportunities', 'activities'],
            'bookreview': ['reviews'],
            'googlelocal': ['businesses'],
            'pancancer_atlas': ['patients', 'samples'],
            'patents': ['patents', 'assignees'],
        }
        
        if dataset in postgres_tables:
            if table_name in postgres_tables[dataset]:
                return DatabaseType.POSTGRESQL
        
        # DuckDB (default for analytics)
        duckdb_tables = {
            'yelp': ['businesses', 'users', 'checkins'],
            'crmarenapro': ['customer_360', 'sales_forecast'],
            'github_repos': ['repositories', 'contributors', 'weekly_stats'],
            'stockmarket': ['all_stocks_metadata'],
        }
        
        if dataset in duckdb_tables:
            if table_name in duckdb_tables[dataset]:
                return DatabaseType.DUCKDB
        
        # Default to SQLite
        return DatabaseType.SQLITE
    
    def get_join_path(
        self,
        dataset: str,
        source_table: str,
        target_table: str
    ) -> Optional[JoinPath]:
        """
        Get join path between two tables.
        
        Args:
            dataset: Dataset name
            source_table: Source table name
            target_table: Target table name
            
        Returns:
            JoinPath or None if no known path
        """
        if dataset not in self.JOIN_PATHS:
            return None
        
        for path in self.JOIN_PATHS[dataset]:
            if (path.source_table == source_table and path.target_table == target_table) or \
               (path.source_table == target_table and path.target_table == source_table):
                return path
        
        return None
    
    def get_all_join_paths(self, dataset: str, table_name: str) -> List[JoinPath]:
        """Get all join paths involving a table."""
        if dataset not in self.JOIN_PATHS:
            return []
        
        paths = []
        for path in self.JOIN_PATHS[dataset]:
            if path.source_table == table_name or path.target_table == table_name:
                paths.append(path)
        
        return paths
    
    def generate_schema_prompt(
        self,
        dataset: str,
        query_text: str,
        include_all: bool = False
    ) -> str:
        """
        Generate a concise schema prompt for the agent.
        
        Args:
            dataset: Dataset name
            query_text: Natural language query
            include_all: If True, include all tables regardless of relevance
            
        Returns:
            Prompt string with schema information
        """
        if include_all:
            tables = self.get_all_tables(dataset)
        else:
            tables = self.get_relevant_tables(dataset, query_text)
        
        sections = [f"## Dataset: {dataset}\n"]
        
        for table in tables:
            schema = self.get_table_schema(dataset, table)
            if schema:
                sections.append(f"### {table} ({schema.db_type.value})")
                sections.append("Columns:")
                for col, dtype in schema.columns.items():
                    sections.append(f"  - {col}: {dtype}")
                sections.append("")
        
        # Add relevant join paths
        join_paths = []
        for table in tables:
            join_paths.extend(self.get_all_join_paths(dataset, table))
        
        if join_paths:
            sections.append("## Join Paths")
            seen: List[JoinPath] = []
            for p in join_paths:
                if p not in seen:
                    seen.append(p)
            for path in seen:
                sections.append(f"- {path.source_table}.{path.join_keys[0][0]} ↔ {path.target_table}.{path.join_keys[0][1]}")
                if path.format_conversion:
                    sections.append(f"  Note: {path.format_conversion}")
        
        return "\n".join(sections)


# Convenience functions
def get_relevant_tables(dataset: str, query_text: str, kb_path: str = "kb") -> List[str]:
    """Return relevant tables for a query."""
    introspector = SchemaIntrospector(kb_path)
    return introspector.get_relevant_tables(dataset, query_text)


def get_join_path(
    dataset: str,
    source_table: str,
    target_table: str,
    kb_path: str = "kb"
) -> Optional[JoinPath]:
    """Get join path between two tables."""
    introspector = SchemaIntrospector(kb_path)
    return introspector.get_join_path(dataset, source_table, target_table)


def generate_schema_prompt(
    dataset: str,
    query_text: str,
    kb_path: str = "kb",
    include_all: bool = False
) -> str:
    """Generate concise schema prompt."""
    introspector = SchemaIntrospector(kb_path)
    return introspector.generate_schema_prompt(dataset, query_text, include_all)