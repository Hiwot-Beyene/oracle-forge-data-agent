"""
Tests for multi_pass_retrieval.py
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import os

from utils.multi_pass_retrieval import (
    MultiPassRetriever,
    PassLevel,
    QueryContext,
    PassResult,
    iterative_query_refinement
)


class TestQueryContext:
    """Tests for QueryContext class."""
    
    def test_to_prompt_basic(self):
        context = QueryContext(
            dataset="yelp",
            query_text="Find businesses with >4 stars",
            pass_level=PassLevel.SCHEMA_ONLY,
            schema_info="Table: businesses"
        )
        
        prompt = context.to_prompt()
        assert "## Schema Information" in prompt
        assert "Table: businesses" in prompt
        assert "## Query" in prompt
        assert "Find businesses with >4 stars" in prompt
    
    def test_to_prompt_all_layers(self):
        context = QueryContext(
            dataset="crmarenapro",
            query_text="Customer spend with tickets",
            pass_level=PassLevel.CORRECTIONS,
            schema_info="Schema here",
            join_key_glossary="Join glossary here",
            domain_terms="Domain terms here",
            corrections="Previous error: format mismatch"
        )
        
        prompt = context.to_prompt()
        assert "## Schema Information" in prompt
        assert "## Join Key Resolution" in prompt
        assert "## Domain Definitions" in prompt
        assert "## Previous Corrections" in prompt
        assert "Previous error: format mismatch" in prompt


@pytest.fixture
def temp_kb():
    """Create temporary knowledge base for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        kb_path = Path(tmpdir) / "kb"
        domain_path = kb_path / "domain"
        schemas_path = domain_path / "schemas"
        schemas_path.mkdir(parents=True)

        # Create test schema file
        schema_content = """# Yelp Dataset Schema
## Table: businesses
| Column | Type |
|--------|------|
| business_id | VARCHAR |
| name | VARCHAR |
| stars | FLOAT |
"""
        (schemas_path / "yelp_schema.md").write_text(schema_content)

        # Create join key glossary
        glossary_content = """# Join Key Glossary
### Yelp Dataset
| Entity | Format | Resolution |
|--------|--------|------------|
| Business ID | string | No conversion |
"""
        (domain_path / "join_key_glossary.md").write_text(glossary_content)

        # Create domain terms
        terms_content = """# Domain Terms
### "active"
**Dataset:** Yelp
**Definition:** User has written at least one review
"""
        (domain_path / "domain_terms.md").write_text(terms_content)

        yield tmpdir


class TestMultiPassRetriever:
    """Tests for MultiPassRetriever class."""

    @pytest.fixture
    def temp_kb(self):
        """Create temporary knowledge base for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            kb_path = Path(tmpdir) / "kb"
            domain_path = kb_path / "domain"
            schemas_path = domain_path / "schemas"
            schemas_path.mkdir(parents=True)
            
            # Create test schema file
            schema_content = """# Yelp Dataset Schema
## Table: businesses
| Column | Type |
|--------|------|
| business_id | VARCHAR |
| name | VARCHAR |
| stars | FLOAT |
"""
            (schemas_path / "yelp_schema.md").write_text(schema_content)
            
            # Create join key glossary
            glossary_content = """# Join Key Glossary
### Yelp Dataset
| Entity | Format | Resolution |
|--------|--------|------------|
| Business ID | string | No conversion |
"""
            (domain_path / "join_key_glossary.md").write_text(glossary_content)
            
            # Create domain terms
            terms_content = """# Domain Terms
### "active"
**Dataset:** Yelp
**Definition:** User has written at least one review
"""
            (domain_path / "domain_terms.md").write_text(terms_content)
            
            yield tmpdir
    
    def test_detect_cross_database_yelp(self, temp_kb):
        retriever = MultiPassRetriever(kb_path=f"{temp_kb}/kb")
        
        # Query that requires joining reviews (MongoDB) with businesses (DuckDB)
        query = "Find average stars for businesses with reviews mentioning 'service'"
        assert retriever.detect_cross_database(query, "yelp") is True
    
    def test_detect_cross_database_single_db(self, temp_kb):
        retriever = MultiPassRetriever(kb_path=f"{temp_kb}/kb")
        
        # Query that only uses one database
        query = "List all businesses in San Francisco"
        assert retriever.detect_cross_database(query, "yelp") is False
    
    def test_detect_cross_database_crm(self, temp_kb):
        retriever = MultiPassRetriever(kb_path=f"{temp_kb}/kb")
        
        query = "Total spend by customers who opened support tickets"
        assert retriever.detect_cross_database(query, "crmarenapro") is True
    
    def test_detect_semantic_ambiguity(self, temp_kb):
        retriever = MultiPassRetriever(kb_path=f"{temp_kb}/kb")
        
        query = "Find active customers who churned last month"
        terms = retriever.detect_semantic_ambiguity(query)
        
        assert "active" in terms
        assert "churn" in terms
    
    def test_detect_semantic_ambiguity_none(self, temp_kb):
        retriever = MultiPassRetriever(kb_path=f"{temp_kb}/kb")
        
        query = "List all businesses with 5 stars"
        terms = retriever.detect_semantic_ambiguity(query)
        
        assert len(terms) == 0
    
    def test_detect_join_key_mismatch_crm(self, temp_kb):
        retriever = MultiPassRetriever(kb_path=f"{temp_kb}/kb")
        
        query = "Join customer data with ticket data"
        assert retriever.detect_join_key_mismatch(query, "crmarenapro") is True
    
    def test_detect_join_key_mismatch_none(self, temp_kb):
        retriever = MultiPassRetriever(kb_path=f"{temp_kb}/kb")
        
        query = "Simple customer query"
        assert retriever.detect_join_key_mismatch(query, "crmarenapro") is False
    
    def test_load_schema(self, temp_kb):
        retriever = MultiPassRetriever(kb_path=f"{temp_kb}/kb")
        
        schema = retriever.load_schema("yelp")
        assert "businesses" in schema
        assert "business_id" in schema
        
        # Test caching
        schema2 = retriever.load_schema("yelp")
        assert schema == schema2
        assert "yelp" in retriever._schema_cache
    
    def test_load_schema_not_found(self, temp_kb):
        retriever = MultiPassRetriever(kb_path=f"{temp_kb}/kb")
        
        schema = retriever.load_schema("nonexistent")
        assert "not found" in schema.lower()
    
    def test_load_join_glossary(self, temp_kb):
        retriever = MultiPassRetriever(kb_path=f"{temp_kb}/kb")
        
        glossary = retriever.load_join_glossary("yelp")
        assert "Business ID" in glossary
        assert "string" in glossary
    
    def test_load_domain_terms(self, temp_kb):
        retriever = MultiPassRetriever(kb_path=f"{temp_kb}/kb")
        
        terms = retriever.load_domain_terms(["active"])
        assert "active" in terms.lower()
        assert "Yelp" in terms
    
    def test_load_domain_terms_empty(self, temp_kb):
        retriever = MultiPassRetriever(kb_path=f"{temp_kb}/kb")
        
        terms = retriever.load_domain_terms([])
        assert terms == ""
    
    def test_build_context_pass1(self, temp_kb):
        retriever = MultiPassRetriever(kb_path=f"{temp_kb}/kb")
        
        context = retriever.build_context(
            dataset="yelp",
            query_text="List businesses",
            pass_level=PassLevel.SCHEMA_ONLY
        )
        
        assert context.pass_level == PassLevel.SCHEMA_ONLY
        assert context.schema_info != ""
        assert context.join_key_glossary == ""
        assert context.domain_terms == ""
    
    def test_build_context_pass2_with_cross_db(self, temp_kb):
        retriever = MultiPassRetriever(kb_path=f"{temp_kb}/kb")
        
        context = retriever.build_context(
            dataset="yelp",
            query_text="Reviews and businesses together",
            pass_level=PassLevel.JOIN_KEYS
        )
        
        assert context.pass_level == PassLevel.JOIN_KEYS
        assert context.schema_info != ""
        assert context.join_key_glossary != ""
    
    def test_build_context_pass3_with_ambiguous(self, temp_kb):
        retriever = MultiPassRetriever(kb_path=f"{temp_kb}/kb")
        
        context = retriever.build_context(
            dataset="yelp",
            query_text="Active users with recent reviews",
            pass_level=PassLevel.DOMAIN_TERMS
        )
        
        assert context.pass_level == PassLevel.DOMAIN_TERMS
        assert context.domain_terms != ""
    
    def test_should_continue_success(self, temp_kb):
        retriever = MultiPassRetriever(kb_path=f"{temp_kb}/kb")
        
        result = PassResult(
            pass_level=PassLevel.SCHEMA_ONLY,
            answer="test",
            success=True
        )
        
        should_continue, next_level = retriever.should_continue(result, max_passes=3)
        assert should_continue is False
        assert next_level is None
    
    def test_should_continue_failure_level1(self, temp_kb):
        retriever = MultiPassRetriever(kb_path=f"{temp_kb}/kb")
        
        result = PassResult(
            pass_level=PassLevel.SCHEMA_ONLY,
            answer=None,
            success=False,
            error_message="Schema insufficient"
        )
        
        should_continue, next_level = retriever.should_continue(result, max_passes=3)
        assert should_continue is True
        assert next_level == PassLevel.JOIN_KEYS
    
    def test_should_continue_max_passes(self, temp_kb):
        retriever = MultiPassRetriever(kb_path=f"{temp_kb}/kb")
        
        result = PassResult(
            pass_level=PassLevel.CORRECTIONS,
            answer=None,
            success=False
        )
        
        should_continue, next_level = retriever.should_continue(result, max_passes=3)
        assert should_continue is False
    
    def test_execute_with_agent_success_first_pass(self, temp_kb):
        retriever = MultiPassRetriever(kb_path=f"{temp_kb}/kb")
        
        # Mock agent that succeeds immediately
        mock_agent = Mock()
        mock_agent.run.return_value = ("42", [])
        
        answer, history = retriever.execute_with_agent(
            mock_agent,
            dataset="yelp",
            query_text="Count businesses",
            max_passes=3
        )
        
        assert answer == "42"
        assert len(history) == 1
        assert history[0].success is True
        assert history[0].pass_level == PassLevel.SCHEMA_ONLY
    
    def test_execute_with_agent_retry_success(self, temp_kb):
        retriever = MultiPassRetriever(kb_path=f"{temp_kb}/kb")
        
        # Mock agent that fails first, succeeds second
        mock_agent = Mock()
        mock_agent.run.side_effect = [
            Exception("Join key mismatch"),
            ("42", [])
        ]
        
        answer, history = retriever.execute_with_agent(
            mock_agent,
            dataset="crmarenapro",
            query_text="Customers with tickets",
            max_passes=3
        )
        
        assert answer == "42"
        assert len(history) == 2
        assert history[0].success is False
        assert history[1].success is True
    
    def test_execute_with_agent_all_fail(self, temp_kb):
        retriever = MultiPassRetriever(kb_path=f"{temp_kb}/kb")
        
        # Mock agent that always fails
        mock_agent = Mock()
        mock_agent.run.side_effect = Exception("Persistent error")
        
        with pytest.raises(Exception, match="Query failed after"):
            retriever.execute_with_agent(
                mock_agent,
                dataset="yelp",
                query_text="Query",
                max_passes=2
            )


class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    def test_iterative_query_refinement(self, temp_kb):
        with patch('utils.multi_pass_retrieval.MultiPassRetriever') as MockRetriever:
            mock_instance = Mock()
            mock_instance.execute_with_agent.return_value = ("answer", [])
            MockRetriever.return_value = mock_instance
            
            mock_agent = Mock()
            
            answer, history = iterative_query_refinement(
                mock_agent,
                dataset="yelp",
                query_text="Test query",
                kb_path="/fake/path"
            )
            
            assert answer == "answer"
            MockRetriever.assert_called_once_with("/fake/path")
            mock_instance.execute_with_agent.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])