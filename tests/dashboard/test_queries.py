"""Tests for dashboard database queries.

Tests query functions with mocked database connection.
Note: These tests require a running database with test data.
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add dashboard to path
dashboard_dir = Path(__file__).parent.parent.parent / "dashboard"
sys.path.insert(0, str(dashboard_dir))


class TestQueryFunctions:
    """Test dashboard query functions."""

    @patch('utils.queries.execute_query')
    def test_get_total_sandwich_count(self, mock_execute):
        """Test total sandwich count query."""
        from utils.queries import get_total_sandwich_count

        # Mock response
        mock_execute.return_value = {'count': 42}

        result = get_total_sandwich_count()

        assert result == 42
        mock_execute.assert_called_once()

    @patch('utils.queries.execute_query')
    def test_get_total_sandwich_count_empty(self, mock_execute):
        """Test total sandwich count with no sandwiches."""
        from utils.queries import get_total_sandwich_count

        # Mock empty response
        mock_execute.return_value = None

        result = get_total_sandwich_count()

        assert result == 0

    @patch('utils.queries.execute_query')
    def test_get_avg_validity(self, mock_execute):
        """Test average validity query."""
        from utils.queries import get_avg_validity

        # Mock response
        mock_execute.return_value = {'avg_validity': 0.75}

        result = get_avg_validity()

        assert result == 0.75
        mock_execute.assert_called_once()

    @patch('utils.queries.execute_query')
    def test_get_avg_validity_no_data(self, mock_execute):
        """Test average validity with no data."""
        from utils.queries import get_avg_validity

        # Mock empty response
        mock_execute.return_value = None

        result = get_avg_validity()

        assert result == 0.0

    @patch('utils.queries.execute_query')
    def test_get_recent_sandwiches(self, mock_execute):
        """Test recent sandwiches query."""
        from utils.queries import get_recent_sandwiches

        # Mock response
        mock_sandwiches = [
            {'sandwich_id': '123', 'name': 'Test Sandwich 1', 'validity_score': 0.8},
            {'sandwich_id': '456', 'name': 'Test Sandwich 2', 'validity_score': 0.9}
        ]
        mock_execute.return_value = mock_sandwiches

        result = get_recent_sandwiches(limit=2)

        assert len(result) == 2
        assert result[0]['name'] == 'Test Sandwich 1'
        assert result[1]['name'] == 'Test Sandwich 2'

        # Check query was called with correct limit
        call_args = mock_execute.call_args
        assert call_args[0][1] == (2,)  # Second argument should be tuple with limit

    @patch('utils.queries.execute_query')
    def test_get_recent_sandwiches_empty(self, mock_execute):
        """Test recent sandwiches with empty database."""
        from utils.queries import get_recent_sandwiches

        # Mock empty response
        mock_execute.return_value = None

        result = get_recent_sandwiches(limit=20)

        assert result == []

    @patch('utils.queries.execute_query')
    def test_get_structural_types(self, mock_execute):
        """Test structural types query."""
        from utils.queries import get_structural_types

        # Mock response
        mock_types = [
            {'name': 'bound'},
            {'name': 'dialectic'},
            {'name': 'epistemic'}
        ]
        mock_execute.return_value = mock_types

        result = get_structural_types()

        assert len(result) == 3
        assert 'bound' in result
        assert 'dialectic' in result
        assert 'epistemic' in result

    @patch('utils.queries.execute_query')
    def test_search_sandwiches_with_filters(self, mock_execute):
        """Test search with validity and type filters."""
        from utils.queries import search_sandwiches
        import pandas as pd

        # Mock response
        mock_results = [
            {'sandwich_id': '123', 'name': 'Test', 'validity_score': 0.8}
        ]
        mock_execute.return_value = mock_results

        result = search_sandwiches(
            query="test",
            validity_min=0.7,
            validity_max=1.0,
            types=['bound', 'dialectic']
        )

        # Should return DataFrame
        assert isinstance(result, pd.DataFrame)

        # Check SQL was called with correct parameters
        call_args = mock_execute.call_args
        sql = call_args[0][0]
        params = call_args[0][1]

        assert 'validity_score BETWEEN' in sql
        assert 0.7 in params
        assert 1.0 in params


class TestDatabaseConnection:
    """Test database connection helpers."""

    @patch('utils.db.psycopg2.connect')
    def test_get_db_connection(self, mock_connect):
        """Test database connection retrieval."""
        from utils.db import get_db_connection

        # Clear cache first
        get_db_connection.clear()

        # Mock connection
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # Should connect to database
        conn = get_db_connection()

        assert conn is not None
        mock_connect.assert_called_once()

    @patch('utils.db.get_db_connection')
    def test_check_database_connection_healthy(self, mock_get_conn):
        """Test database health check when healthy."""
        from utils.db import check_database_connection

        # Mock healthy connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [1]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        mock_get_conn.return_value = mock_conn

        result = check_database_connection()

        assert result is True

    @patch('utils.db.get_db_connection')
    def test_check_database_connection_unhealthy(self, mock_get_conn):
        """Test database health check when connection fails."""
        from utils.db import check_database_connection

        # Mock failed connection
        mock_get_conn.side_effect = Exception("Connection failed")

        result = check_database_connection()

        assert result is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
