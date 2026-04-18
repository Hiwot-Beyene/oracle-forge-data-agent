"""
Join Key Resolver

Handles cross-database join key format conversions.
Based on the join_key_glossary.md knowledge base.

Supports:
- Format detection and normalization
- Pre-join validation to prevent failures
- Common enterprise data format conversions
"""

import re
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum


class KeyFormat(Enum):
    """Common key format patterns."""
    INTEGER = "integer"
    STRING = "string"
    CUST_PREFIXED = "cust_prefixed"  # "CUST-00123"
    ORD_PREFIXED = "ord_prefixed"    # "ORD-2024-00001"
    PROD_CODE = "product_code"       # "PROD-ABC-123"
    UUID = "uuid"
    OBJECT_ID = "object_id"          # MongoDB ObjectId


@dataclass
class KeyConversion:
    """Conversion rule between two key formats."""
    source_format: KeyFormat
    target_format: KeyFormat
    conversion_func: str
    description: str


class JoinKeyResolver:
    """
    Resolve and normalize join keys across database boundaries.
    
    Implements all format conversions documented in kb/domain/join_key_glossary.md
    """
    
    # Format detection patterns
    FORMAT_PATTERNS = {
        KeyFormat.CUST_PREFIXED: re.compile(r'^CUST-\d+$', re.IGNORECASE),
        KeyFormat.ORD_PREFIXED: re.compile(r'^ORD-\d{4}-\d+$', re.IGNORECASE),
        KeyFormat.PROD_CODE: re.compile(r'^[A-Z]+-[A-Z0-9]+-\d+$', re.IGNORECASE),
        KeyFormat.UUID: re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE),
        KeyFormat.OBJECT_ID: re.compile(r'^[0-9a-f]{24}$', re.IGNORECASE),
    }
    
    # Known conversions by dataset
    DATASET_CONVERSIONS: Dict[str, Dict[str, KeyConversion]] = {
        'crmarenapro': {
            'customer_id_to_cust_id': KeyConversion(
                source_format=KeyFormat.INTEGER,
                target_format=KeyFormat.CUST_PREFIXED,
                conversion_func='int_to_cust_prefixed',
                description='Convert integer customer ID to "CUST-XXXXX" format'
            ),
            'cust_id_to_customer_id': KeyConversion(
                source_format=KeyFormat.CUST_PREFIXED,
                target_format=KeyFormat.INTEGER,
                conversion_func='cust_prefixed_to_int',
                description='Convert "CUST-XXXXX" to integer customer ID'
            ),
        },
        'bookreview': {
            'book_id_to_id': KeyConversion(
                source_format=KeyFormat.INTEGER,
                target_format=KeyFormat.INTEGER,
                conversion_func='identity',
                description='Field name differs but format matches'
            ),
            'reviewer_id_to_user_id': KeyConversion(
                source_format=KeyFormat.INTEGER,
                target_format=KeyFormat.INTEGER,
                conversion_func='identity',
                description='Field name differs but format matches'
            ),
        },
    }
    
    def __init__(self):
        """Initialize resolver with conversion functions."""
        self._conversion_cache: Dict[str, Any] = {}
    
    def detect_format(self, value: Any) -> KeyFormat:
        """
        Detect the format of a key value.
        
        Args:
            value: Key value to analyze
            
        Returns:
            Detected KeyFormat
        """
        if value is None:
            return KeyFormat.STRING
        
        # Try integer conversion
        try:
            int(value)
            return KeyFormat.INTEGER
        except (ValueError, TypeError):
            pass
        
        # Check string patterns
        str_value = str(value)
        
        for format_type, pattern in self.FORMAT_PATTERNS.items():
            if pattern.match(str_value):
                return format_type
        
        return KeyFormat.STRING
    
    def int_to_cust_prefixed(self, value: Union[int, str]) -> str:
        """Convert integer to CUST-XXXXX format."""
        int_val = int(value)
        return f"CUST-{int_val:05d}"
    
    def cust_prefixed_to_int(self, value: str) -> int:
        """Convert CUST-XXXXX to integer."""
        match = re.search(r'CUST-0*(\d+)', value, re.IGNORECASE)
        if match:
            return int(match.group(1))
        raise ValueError(f"Cannot parse customer ID from: {value}")
    
    def ord_prefixed_to_int(self, value: str) -> int:
        """Convert ORD-YYYY-XXXXX to integer order ID."""
        match = re.search(r'ORD-\d{4}-0*(\d+)', value, re.IGNORECASE)
        if match:
            return int(match.group(1))
        raise ValueError(f"Cannot parse order ID from: {value}")
    
    def identity(self, value: Any) -> Any:
        """Identity conversion (no change)."""
        return value
    
    def normalize_key(
        self,
        value: Any,
        from_db_type: str,
        to_db_type: str,
        key_category: Optional[str] = None
    ) -> Any:
        """
        Normalize a key value for cross-database join.
        
        Args:
            value: Raw key value
            from_db_type: Source database type ('postgres', 'mongodb', 'sqlite', 'duckdb')
            to_db_type: Target database type
            key_category: Type of key ('customer_id', 'product_code', etc.)
            
        Returns:
            Normalized value suitable for target database
        """
        # Detect format
        source_format = self.detect_format(value)
        
        # Check for known conversion
        cache_key = f"{key_category}_{from_db_type}_{to_db_type}"
        
        if cache_key in self._conversion_cache:
            conversion = self._conversion_cache[cache_key]
            func = getattr(self, conversion.conversion_func)
            return func(value)
        
        # CRMArenaPro customer ID resolution
        if key_category == 'customer_id':
            if 'sqlite' in from_db_type.lower() and 'postgres' in to_db_type.lower():
                # SQLite uses CUST-00123, PostgreSQL uses 123
                self._conversion_cache[cache_key] = KeyConversion(
                    source_format=KeyFormat.CUST_PREFIXED,
                    target_format=KeyFormat.INTEGER,
                    conversion_func='cust_prefixed_to_int',
                    description='CUST-prefixed to integer'
                )
                return self.cust_prefixed_to_int(str(value))
            elif 'postgres' in from_db_type.lower() and 'sqlite' in to_db_type.lower():
                # PostgreSQL uses 123, SQLite uses CUST-00123
                self._conversion_cache[cache_key] = KeyConversion(
                    source_format=KeyFormat.INTEGER,
                    target_format=KeyFormat.CUST_PREFIXED,
                    conversion_func='int_to_cust_prefixed',
                    description='Integer to CUST-prefixed'
                )
                return self.int_to_cust_prefixed(value)

        # CRMArenaPro order ID resolution
        if key_category == 'order_id':
            if 'sqlite' in from_db_type.lower() and 'postgres' in to_db_type.lower():
                self._conversion_cache[cache_key] = KeyConversion(
                    source_format=KeyFormat.ORD_PREFIXED,
                    target_format=KeyFormat.INTEGER,
                    conversion_func='ord_prefixed_to_int',
                    description='ORD-prefixed to integer'
                )
                return self.ord_prefixed_to_int(str(value))
        
        # Field name mapping (no format change)
        field_mappings = {
            ('bookreview', 'book_id'): 'id',
            ('bookreview', 'reviewer_id'): 'user_id',
            ('crmarenapro', 'product_code'): 'sku',
        }
        
        for (dataset, source_field), target_field in field_mappings.items():
            if key_category and source_field in key_category:
                # Return same value, caller handles field rename
                return value
        
        # Default: no conversion
        return value
    
    def detect_format_mismatch(
        self,
        source_values: List[Any],
        target_format_expected: KeyFormat
    ) -> Tuple[bool, Optional[str]]:
        """
        Detect if a join will fail due to format mismatch.
        
        Args:
            source_values: Sample of source key values
            target_format_expected: Expected format in target database
            
        Returns:
            (has_mismatch, description)
        """
        if not source_values:
            return False, None
        
        # Sample first few values
        sample = source_values[:5]
        formats = [self.detect_format(v) for v in sample]
        
        # Check if any format differs from expected
        mismatches = [f for f in formats if f != target_format_expected]
        
        if mismatches:
            return True, f"Expected {target_format_expected.value}, found {mismatches[0].value}"
        
        return False, None
    
    def get_conversion_rule(
        self,
        dataset: str,
        from_field: str,
        to_field: str
    ) -> Optional[KeyConversion]:
        """
        Get conversion rule for specific dataset fields.
        
        Args:
            dataset: Dataset name
            from_field: Source field name
            to_field: Target field name
            
        Returns:
            KeyConversion or None
        """
        conversion_key = f"{from_field}_to_{to_field}"
        
        if dataset in self.DATASET_CONVERSIONS:
            return self.DATASET_CONVERSIONS[dataset].get(conversion_key)
        
        return None
    
    def batch_normalize(
        self,
        values: List[Any],
        from_db_type: str,
        to_db_type: str,
        key_category: str
    ) -> List[Any]:
        """
        Normalize a batch of key values.
        
        Args:
            values: List of raw key values
            from_db_type: Source database type
            to_db_type: Target database type
            key_category: Type of key
            
        Returns:
            List of normalized values
        """
        return [self.normalize_key(v, from_db_type, to_db_type, key_category) for v in values]
    
    def create_join_mapping(
        self,
        source_keys: List[Any],
        target_keys: List[Any],
        from_db_type: str,
        to_db_type: str,
        key_category: str
    ) -> Dict[Any, Any]:
        """
        Create a mapping dictionary for joining datasets.
        
        Args:
            source_keys: Keys from source database
            target_keys: Keys from target database
            from_db_type: Source database type
            to_db_type: Target database type
            key_category: Type of key
            
        Returns:
            Dictionary mapping source keys to matching target keys
        """
        # Convert target keys to source format so we can match against source keys directly
        target_by_source_key: Dict[Any, Any] = {}
        for tk in target_keys:
            norm = self.normalize_key(tk, to_db_type, from_db_type, key_category)
            target_by_source_key[norm] = tk

        # Map source keys to their matching target key
        mapping = {}
        for sk in source_keys:
            if sk in target_by_source_key:
                mapping[sk] = target_by_source_key[sk]

        return mapping


# Convenience function
def normalize_key(
    value: Any,
    from_db_type: str,
    to_db_type: str,
    key_category: Optional[str] = None
) -> Any:
    """
    Normalize a key value for cross-database join.
    
    Args:
        value: Raw key value
        from_db_type: Source database type
        to_db_type: Target database type
        key_category: Type of key (e.g., 'customer_id')
        
    Returns:
        Normalized value
    
    Examples:
        >>> normalize_key("CUST-00123", "sqlite", "postgres", "customer_id")
        123
        
        >>> normalize_key(123, "postgres", "sqlite", "customer_id")
        "CUST-00123"
    """
    resolver = JoinKeyResolver()
    return resolver.normalize_key(value, from_db_type, to_db_type, key_category)


def detect_format_mismatch(
    values: List[Any],
    expected_format: str
) -> Tuple[bool, Optional[str]]:
    """
    Detect if a join will fail due to format mismatch.
    
    Args:
        values: Sample of key values
        expected_format: Expected format ('integer', 'cust_prefixed', etc.)
        
    Returns:
        (has_mismatch, description)
    """
    resolver = JoinKeyResolver()
    format_enum = KeyFormat(expected_format)
    return resolver.detect_format_mismatch(values, format_enum)