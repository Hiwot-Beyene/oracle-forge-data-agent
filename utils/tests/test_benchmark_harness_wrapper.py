"""
Tests for benchmark_wrapper.py
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from utils.benchmark_harness_wrapper import (
    BenchmarkHarness,
    QueryTrace,
    ToolCall,
    ValidationResult,
    TerminateReason,
    run_dab_query,
    compute_pass_at_1
)


class TestQueryTrace:
    """Tests for QueryTrace dataclass."""
    
    def test_create_trace(self):
        trace = QueryTrace(
            query_id="1",
            dataset="yelp",
            run_number=0,
            start_time="2024-01-01T00:00:00",
            end_time="2024-01-01T00:00:01",
            duration_ms=1000,
            terminate_reason=TerminateReason.SUCCESS,
            final_answer="42"
        )
        
        assert trace.query_id == "1"
        assert trace.dataset == "yelp"
        assert trace.final_answer == "42"
        assert trace.terminate_reason == TerminateReason.SUCCESS
    
    def test_trace_with_tool_calls(self):
        tool_call = ToolCall(
            timestamp="2024-01-01T00:00:00",
            tool_name="query_postgres",
            parameters={"query": "SELECT * FROM businesses"},
            result=[{"name": "Test"}],
            duration_ms=100,
            success=True
        )
        
        trace = QueryTrace(
            query_id="1",
            dataset="yelp",
            run_number=0,
            start_time="2024-01-01T00:00:00",
            end_time="2024-01-01T00:00:01",
            duration_ms=1000,
            terminate_reason=TerminateReason.SUCCESS,
            final_answer="42",
            tool_calls=[tool_call]
        )
        
        assert len(trace.tool_calls) == 1
        assert trace.tool_calls[0].tool_name == "query_postgres"


@pytest.fixture
def temp_dab():
    """Create temporary DAB structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dab_path = Path(tmpdir) / "DataAgentBench"

        # Create dataset directory
        query_dir = dab_path / "query_yelp" / "query1"
        query_dir.mkdir(parents=True)

        # Create query.json
        query_data = {"query": "Find businesses with 5 stars"}
        (query_dir / "query.json").write_text(json.dumps(query_data))

        # Create ground_truth.txt
        (query_dir / "ground_truth.txt").write_text("42")

        yield tmpdir, dab_path


class TestBenchmarkHarness:
    """Tests for BenchmarkHarness class."""

    @pytest.fixture
    def temp_dab(self):
        """Create temporary DAB structure for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dab_path = Path(tmpdir) / "DataAgentBench"
            
            # Create dataset directory
            query_dir = dab_path / "query_yelp" / "query1"
            query_dir.mkdir(parents=True)
            
            # Create query.json
            query_data = {"query": "Find businesses with 5 stars"}
            (query_dir / "query.json").write_text(json.dumps(query_data))
            
            # Create ground_truth.txt
            (query_dir / "ground_truth.txt").write_text("42")
            
            yield tmpdir, dab_path
    
    @pytest.fixture
    def harness(self, temp_dab):
        _, dab_path = temp_dab
        return BenchmarkHarness(dab_path=str(dab_path))
    
    def test_init_creates_directories(self, temp_dab):
        tmpdir, dab_path = temp_dab
        
        harness = BenchmarkHarness(
            dab_path=str(dab_path),
            results_dir=f"{tmpdir}/results",
            logs_dir=f"{tmpdir}/logs"
        )
        
        assert Path(harness.results_dir).exists()
        assert Path(harness.logs_dir).exists()
    
    def test_get_query_dir(self, harness):
        query_dir = harness._get_query_dir("yelp", "1")
        assert query_dir.name == "query1"
        assert "query_yelp" in str(query_dir)
    
    def test_load_ground_truth_txt(self, harness):
        gt = harness._load_ground_truth("yelp", "1")
        assert gt == "42"
    
    def test_load_ground_truth_not_found(self, harness):
        gt = harness._load_ground_truth("nonexistent", "1")
        assert gt is None
    
    def test_run_query(self, harness):
        mock_agent = Mock()
        mock_agent.run.return_value = ("42", [])
        
        trace = harness.run_query(
            agent=mock_agent,
            dataset="yelp",
            query_id="1",
            run_number=0
        )
        
        assert trace.dataset == "yelp"
        assert trace.query_id == "1"
        assert trace.run_number == 0
        assert trace.final_answer == "42"
        assert trace.terminate_reason == TerminateReason.SUCCESS
    
    def test_run_query_with_error(self, harness):
        mock_agent = Mock()
        mock_agent.run.side_effect = Exception("Test error")
        
        trace = harness.run_query(
            agent=mock_agent,
            dataset="yelp",
            query_id="1",
            run_number=0
        )
        
        assert trace.terminate_reason == TerminateReason.ERROR
        assert trace.error_message == "Test error"
        assert trace.final_answer is None
    
    def test_run_query_with_context(self, harness):
        mock_agent = Mock()
        mock_agent.run.return_value = ("42", [])
        
        trace = harness.run_query(
            agent=mock_agent,
            dataset="yelp",
            query_id="1",
            run_number=0,
            use_hints=False,
            context_builder=None
        )
        
        # Context should be None when no hints and no builder
        assert trace.context_used is None
    
    def test_validate_result_success(self, harness):
        trace = QueryTrace(
            query_id="1",
            dataset="yelp",
            run_number=0,
            start_time=datetime.now().isoformat(),
            end_time=datetime.now().isoformat(),
            duration_ms=100,
            terminate_reason=TerminateReason.SUCCESS,
            final_answer="42"
        )
        
        validation = harness.validate_result(trace, "yelp", "1")
        
        assert validation.query_id == "1"
        assert validation.dataset == "yelp"
        assert validation.ground_truth == "42"
        assert validation.llm_answer == "42"
    
    def test_validate_result_no_tool_call(self, harness):
        trace = QueryTrace(
            query_id="1",
            dataset="yelp",
            run_number=0,
            start_time=datetime.now().isoformat(),
            end_time=datetime.now().isoformat(),
            duration_ms=100,
            terminate_reason=TerminateReason.NO_TOOL_CALL,
            final_answer=None
        )
        
        validation = harness.validate_result(trace, "yelp", "1")
        
        assert validation.is_valid is False
        assert "no tool calls" in validation.reason.lower()
    
    def test_validate_result_error(self, harness):
        trace = QueryTrace(
            query_id="1",
            dataset="yelp",
            run_number=0,
            start_time=datetime.now().isoformat(),
            end_time=datetime.now().isoformat(),
            duration_ms=100,
            terminate_reason=TerminateReason.ERROR,
            final_answer=None,
            error_message="Connection failed"
        )
        
        validation = harness.validate_result(trace, "yelp", "1")
        
        assert validation.is_valid is False
        assert "Connection failed" in validation.reason
    
    def test_save_trace(self, harness, temp_dab):
        tmpdir, _ = temp_dab
        harness.logs_dir = Path(tmpdir) / "logs"
        
        trace = QueryTrace(
            query_id="1",
            dataset="yelp",
            run_number=0,
            start_time=datetime.now().isoformat(),
            end_time=datetime.now().isoformat(),
            duration_ms=100,
            terminate_reason=TerminateReason.SUCCESS,
            final_answer="42",
            tool_calls=[
                ToolCall(
                    timestamp=datetime.now().isoformat(),
                    tool_name="test_tool",
                    parameters={},
                    result="test",
                    duration_ms=10,
                    success=True
                )
            ]
        )
        
        trace_path = harness.save_trace(trace)
        
        assert trace_path.exists()
        assert (trace_path.parent / "tool_calls.jsonl").exists()
        assert (trace_path.parent / "llm_calls.jsonl").exists()
    
    def test_compute_pass_at_1(self, harness, temp_dab):
        tmpdir, _ = temp_dab
        harness.logs_dir = Path(tmpdir) / "logs"
        
        # Create a successful run log
        log_dir = harness.logs_dir / "query_yelp" / "query1" / "run_0"
        log_dir.mkdir(parents=True)
        
        trace = QueryTrace(
            query_id="1",
            dataset="yelp",
            run_number=0,
            start_time=datetime.now().isoformat(),
            end_time=datetime.now().isoformat(),
            duration_ms=100,
            terminate_reason=TerminateReason.SUCCESS,
            final_answer="42"
        )
        
        from dataclasses import asdict
        (log_dir / "final_agent.json").write_text(json.dumps(asdict(trace), default=str))
        
        # Should compute score (may be 0.0 or 1.0 depending on validation)
        score = harness.compute_pass_at_1("yelp")
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
    
    def test_compute_pass_at_1_no_logs(self, harness):
        score = harness.compute_pass_at_1("nonexistent")
        assert score == 0.0
    
    def test_generate_submission_json(self, harness):
        traces = [
            QueryTrace(
                query_id="1",
                dataset="yelp",
                run_number=0,
                start_time=datetime.now().isoformat(),
                end_time=datetime.now().isoformat(),
                duration_ms=100,
                terminate_reason=TerminateReason.SUCCESS,
                final_answer="42"
            ),
            QueryTrace(
                query_id="1",
                dataset="yelp",
                run_number=1,
                start_time=datetime.now().isoformat(),
                end_time=datetime.now().isoformat(),
                duration_ms=100,
                terminate_reason=TerminateReason.SUCCESS,
                final_answer="42"
            )
        ]
        
        submission = harness.generate_submission_json(
            agent_name="TestAgent",
            traces=traces
        )
        
        assert len(submission) == 2
        assert submission[0]["dataset"] == "yelp"
        assert submission[0]["query"] == "1"
        assert submission[0]["run"] == 0
        assert submission[0]["answer"] == "42"
    
    def test_generate_submission_json_with_file(self, harness, temp_dab):
        tmpdir, _ = temp_dab
        output_path = Path(tmpdir) / "submission.json"
        
        traces = [
            QueryTrace(
                query_id="1",
                dataset="yelp",
                run_number=0,
                start_time=datetime.now().isoformat(),
                end_time=datetime.now().isoformat(),
                duration_ms=100,
                terminate_reason=TerminateReason.SUCCESS,
                final_answer="42"
            )
        ]
        
        submission = harness.generate_submission_json(
            agent_name="TestAgent",
            traces=traces,
            output_path=str(output_path)
        )
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            loaded = json.load(f)
            assert len(loaded) == 1
    
    def test_score_log_entry(self, harness):
        entry = harness.score_log_entry(
            dataset="yelp",
            baseline_score=0.3,
            current_score=0.5,
            notes="Improved join resolution"
        )
        
        assert "yelp" in entry
        assert "30.0%" in entry
        assert "50.0%" in entry
        assert "+20.0%" in entry
        assert "Improved join resolution" in entry
    
    def test_score_log_entry_negative_delta(self, harness):
        entry = harness.score_log_entry(
            dataset="yelp",
            baseline_score=0.5,
            current_score=0.3,
            notes="Regression detected"
        )
        
        assert "-20.0%" in entry


class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    def test_run_dab_query(self, temp_dab):
        tmpdir, dab_path = temp_dab
        
        mock_agent = Mock()
        mock_agent.run.return_value = ("42", [])
        
        with patch('utils.benchmark_harness_wrapper.BenchmarkHarness') as MockHarness:
            mock_harness = Mock()
            mock_harness.run_query.return_value = QueryTrace(
                query_id="1",
                dataset="yelp",
                run_number=0,
                start_time="",
                end_time="",
                duration_ms=0,
                terminate_reason=TerminateReason.SUCCESS,
                final_answer="42"
            )
            MockHarness.return_value = mock_harness
            
            traces = run_dab_query(
                mock_agent,
                dataset="yelp",
                query_id="1",
                trials=2,
                dab_path=str(dab_path)
            )
            
            assert len(traces) == 2
            assert mock_harness.run_query.call_count == 2
            assert mock_harness.save_trace.call_count == 2
    
    def test_compute_pass_at_1_function(self):
        with patch('utils.benchmark_harness_wrapper.BenchmarkHarness') as MockHarness:
            mock_harness = Mock()
            mock_harness.compute_pass_at_1.return_value = 0.75
            MockHarness.return_value = mock_harness
            
            score = compute_pass_at_1("yelp", logs_dir="/fake/logs")
            
            assert score == 0.75
            MockHarness.assert_called_once_with(logs_dir="/fake/logs")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])