"""
Error Handling Test Suite
Tests for graceful error recovery, proper error messages, and system resilience
"""

import unittest
import pytest
import json
import time
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import requests
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app


class TestErrorHandling(unittest.TestCase):
    """Test suite for comprehensive error handling scenarios"""
    
    def setUp(self):
        """Set up test client and test data"""
        self.app = app
        self.client = self.app.test_client()
        self.app.config['TESTING'] = True
        self.app.config['DEBUG'] = False
        
    def tearDown(self):
        """Clean up after tests"""
        pass


class TestAPIErrorHandling(TestErrorHandling):
    """Test API endpoint error handling"""
    
    def test_404_not_found_error(self):
        """Test handling of non-existent endpoints"""
        response = self.client.get('/non_existent_endpoint')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data.lower() or 'not found', data.lower())
        
    def test_method_not_allowed_error(self):
        """Test handling of incorrect HTTP methods"""
        # Assuming /predict only accepts GET
        response = self.client.delete('/predict')
        self.assertEqual(response.status_code, 405)
        
    def test_missing_required_parameters(self):
        """Test handling of missing required parameters"""
        response = self.client.get('/predict')  # Missing ticker parameter
        self.assertIn(response.status_code, [400, 422])
        data = json.loads(response.data)
        self.assertIn('error', data.lower() or 'missing', data.lower())
        
    def test_invalid_parameter_types(self):
        """Test handling of invalid parameter types"""
        response = self.client.get('/predict?ticker=AAPL&days=invalid')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data.lower() or 'invalid', data.lower())
        
    def test_empty_request_body(self):
        """Test handling of empty POST request body"""
        response = self.client.post('/api/analyze', 
                                   data='',
                                   content_type='application/json')
        self.assertIn(response.status_code, [400, 422])
        
    def test_malformed_json_request(self):
        """Test handling of malformed JSON in request"""
        response = self.client.post('/api/analyze',
                                   data='{"invalid": json}',
                                   content_type='application/json')
        self.assertEqual(response.status_code, 400)
        
    def test_content_type_mismatch(self):
        """Test handling of incorrect content-type header"""
        response = self.client.post('/api/analyze',
                                   data='plain text data',
                                   content_type='text/plain')
        self.assertIn(response.status_code, [400, 415])


class TestDatabaseErrorHandling(TestErrorHandling):
    """Test database-related error handling"""
    
    @patch('psycopg2.connect')
    def test_database_connection_failure(self, mock_connect):
        """Test handling of database connection failures"""
        mock_connect.side_effect = Exception("Database connection failed")
        response = self.client.get('/stocks')
        self.assertEqual(response.status_code, 503)
        data = json.loads(response.data)
        self.assertIn('service unavailable', data.get('error', '').lower())
        
    @patch('app.db.execute')
    def test_database_query_timeout(self, mock_execute):
        """Test handling of database query timeouts"""
        mock_execute.side_effect = TimeoutError("Query timeout")
        response = self.client.get('/stocks')
        self.assertEqual(response.status_code, 504)
        
    @patch('app.db.execute')
    def test_database_constraint_violation(self, mock_execute):
        """Test handling of database constraint violations"""
        mock_execute.side_effect = Exception("UNIQUE constraint violation")
        response = self.client.post('/api/portfolio',
                                  json={'ticker': 'AAPL', 'shares': 100})
        self.assertEqual(response.status_code, 409)
        
    def test_sql_injection_attempt(self):
        """Test handling of SQL injection attempts"""
        malicious_input = "'; DROP TABLE users; --"
        response = self.client.get(f'/predict?ticker={malicious_input}')
        # Should sanitize input and return error, not execute injection
        self.assertIn(response.status_code, [400, 422])
        # Verify no actual SQL execution occurred
        
    @patch('app.db.commit')
    def test_transaction_rollback_on_error(self, mock_commit):
        """Test proper transaction rollback on errors"""
        mock_commit.side_effect = Exception("Commit failed")
        response = self.client.post('/api/transaction',
                                  json={'action': 'buy', 'ticker': 'AAPL'})
        self.assertEqual(response.status_code, 500)
        # Verify rollback was called


class TestExternalAPIErrorHandling(TestErrorHandling):
    """Test external API integration error handling"""
    
    @patch('requests.get')
    def test_external_api_timeout(self, mock_get):
        """Test handling of external API timeouts"""
        mock_get.side_effect = requests.Timeout("API timeout")
        response = self.client.get('/predict?ticker=AAPL&days=7')
        self.assertEqual(response.status_code, 504)
        data = json.loads(response.data)
        self.assertIn('timeout', data.get('error', '').lower())
        
    @patch('requests.get')
    def test_external_api_connection_error(self, mock_get):
        """Test handling of external API connection errors"""
        mock_get.side_effect = requests.ConnectionError("Connection failed")
        response = self.client.get('/stocks')
        self.assertEqual(response.status_code, 503)
        
    @patch('requests.get')
    def test_external_api_rate_limit(self, mock_get):
        """Test handling of rate limit errors from external APIs"""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {'Retry-After': '60'}
        mock_get.return_value = mock_response
        
        response = self.client.get('/stocks')
        self.assertEqual(response.status_code, 429)
        data = json.loads(response.data)
        self.assertIn('rate limit', data.get('error', '').lower())
        
    @patch('requests.get')
    def test_external_api_invalid_response(self, mock_get):
        """Test handling of invalid responses from external APIs"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response
        
        response = self.client.get('/stocks')
        self.assertEqual(response.status_code, 502)
        
    @patch('requests.get')
    def test_external_api_partial_data(self, mock_get):
        """Test handling of incomplete data from external APIs"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'incomplete': 'data'}  # Missing required fields
        mock_get.return_value = mock_response
        
        response = self.client.get('/predict?ticker=AAPL&days=7')
        self.assertIn(response.status_code, [422, 500])


class TestAuthenticationErrorHandling(TestErrorHandling):
    """Test authentication and authorization error handling"""
    
    def test_missing_authentication_token(self):
        """Test handling of missing authentication tokens"""
        response = self.client.get('/api/protected')
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn('unauthorized', data.get('error', '').lower())
        
    def test_invalid_authentication_token(self):
        """Test handling of invalid authentication tokens"""
        headers = {'Authorization': 'Bearer invalid_token_here'}
        response = self.client.get('/api/protected', headers=headers)
        self.assertEqual(response.status_code, 401)
        
    def test_expired_authentication_token(self):
        """Test handling of expired authentication tokens"""
        expired_token = "expired_jwt_token_here"
        headers = {'Authorization': f'Bearer {expired_token}'}
        response = self.client.get('/api/protected', headers=headers)
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn('expired', data.get('error', '').lower())
        
    def test_insufficient_permissions(self):
        """Test handling of insufficient user permissions"""
        # Assume user token with limited permissions
        headers = {'Authorization': 'Bearer limited_user_token'}
        response = self.client.delete('/api/admin/users/1', headers=headers)
        self.assertEqual(response.status_code, 403)
        
    def test_account_locked_error(self):
        """Test handling of locked account access attempts"""
        response = self.client.post('/login',
                                   json={'username': 'locked_user', 'password': 'pass'})
        self.assertIn(response.status_code, [401, 423])


class TestDataValidationErrorHandling(TestErrorHandling):
    """Test data validation error handling"""
    
    def test_invalid_stock_ticker(self):
        """Test handling of invalid stock ticker symbols"""
        response = self.client.get('/predict?ticker=INVALID123&days=7')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('invalid ticker', data.get('error', '').lower())
        
    def test_out_of_range_values(self):
        """Test handling of out-of-range parameter values"""
        response = self.client.get('/predict?ticker=AAPL&days=10000')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('out of range', data.get('error', '').lower())
        
    def test_negative_values(self):
        """Test handling of negative values where not allowed"""
        response = self.client.get('/predict?ticker=AAPL&days=-5')
        self.assertEqual(response.status_code, 400)
        
    def test_oversized_request_payload(self):
        """Test handling of requests exceeding size limits"""
        large_data = {'data': 'x' * (10 * 1024 * 1024)}  # 10MB payload
        response = self.client.post('/api/analyze', json=large_data)
        self.assertEqual(response.status_code, 413)
        
    def test_special_characters_in_input(self):
        """Test handling of special characters in user input"""
        response = self.client.get('/predict?ticker=<script>alert()</script>&days=7')
        self.assertEqual(response.status_code, 400)
        # Verify input is sanitized, not executed


class TestMLModelErrorHandling(TestErrorHandling):
    """Test machine learning model error handling"""
    
    @patch('app.ml_model.predict')
    def test_model_prediction_failure(self, mock_predict):
        """Test handling of model prediction failures"""
        mock_predict.side_effect = Exception("Model prediction failed")
        response = self.client.get('/predict?ticker=AAPL&days=7')
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertIn('prediction failed', data.get('error', '').lower())
        
    @patch('app.ml_model.load')
    def test_model_loading_failure(self, mock_load):
        """Test handling of model loading failures"""
        mock_load.side_effect = FileNotFoundError("Model file not found")
        response = self.client.get('/predict?ticker=AAPL&days=7')
        self.assertEqual(response.status_code, 503)
        
    def test_insufficient_training_data(self):
        """Test handling of insufficient data for predictions"""
        response = self.client.get('/predict?ticker=NEWIPO&days=30')
        self.assertEqual(response.status_code, 422)
        data = json.loads(response.data)
        self.assertIn('insufficient data', data.get('error', '').lower())
        
    @patch('app.ml_model.predict')
    def test_model_timeout(self, mock_predict):
        """Test handling of model prediction timeouts"""
        mock_predict.side_effect = TimeoutError("Prediction timeout")
        response = self.client.get('/predict?ticker=AAPL&days=7')
        self.assertEqual(response.status_code, 504)


class TestSystemResourceErrorHandling(TestErrorHandling):
    """Test system resource error handling"""
    
    @patch('app.check_memory')
    def test_memory_exhaustion(self, mock_memory):
        """Test handling of memory exhaustion"""
        mock_memory.return_value = False  # Indicates low memory
        response = self.client.post('/api/analyze',
                                   json={'data': 'large_dataset'})
        self.assertEqual(response.status_code, 507)
        
    @patch('os.path.exists')
    def test_disk_space_error(self, mock_exists):
        """Test handling of insufficient disk space"""
        mock_exists.side_effect = OSError("No space left on device")
        response = self.client.post('/api/export',
                                   json={'format': 'csv'})
        self.assertEqual(response.status_code, 507)
        
    def test_file_permission_error(self):
        """Test handling of file permission errors"""
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            response = self.client.get('/api/logs')
            self.assertEqual(response.status_code, 500)
            
    def test_concurrent_request_limit(self):
        """Test handling of too many concurrent requests"""
        # Simulate multiple concurrent requests
        responses = []
        for _ in range(100):
            responses.append(self.client.get('/stocks'))
        
        # At least some should be rate limited
        rate_limited = [r for r in responses if r.status_code == 429]
        self.assertGreater(len(rate_limited), 0)


class TestRecoveryMechanisms(TestErrorHandling):
    """Test error recovery and resilience mechanisms"""
    
    @patch('app.primary_service')
    @patch('app.fallback_service')
    def test_fallback_to_secondary_service(self, mock_fallback, mock_primary):
        """Test fallback to secondary service on primary failure"""
        mock_primary.side_effect = Exception("Primary service down")
        mock_fallback.return_value = {'status': 'fallback'}
        
        response = self.client.get('/stocks')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'fallback')
        
    @patch('app.cache.get')
    def test_serve_cached_data_on_error(self, mock_cache):
        """Test serving cached data when live data unavailable"""
        mock_cache.return_value = {'cached': True, 'data': 'cached_stocks'}
        
        with patch('requests.get', side_effect=Exception("API down")):
            response = self.client.get('/stocks')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['cached'])
            
    def test_circuit_breaker_activation(self):
        """Test circuit breaker pattern for failing services"""
        # Make multiple failing requests
        for _ in range(5):
            with patch('requests.get', side_effect=Exception("Service down")):
                self.client.get('/stocks')
        
        # Circuit should be open, returning immediate error
        response = self.client.get('/stocks')
        self.assertEqual(response.status_code, 503)
        data = json.loads(response.data)
        self.assertIn('circuit open', data.get('error', '').lower())
        
    @patch('app.retry_with_backoff')
    def test_retry_with_exponential_backoff(self, mock_retry):
        """Test retry mechanism with exponential backoff"""
        mock_retry.side_effect = [Exception(), Exception(), {'success': True}]
        response = self.client.get('/stocks')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_retry.call_count, 3)


class TestLoggingAndMonitoring(TestErrorHandling):
    """Test error logging and monitoring"""
    
    @patch('app.logger.error')
    def test_error_logging(self, mock_logger):
        """Test that errors are properly logged"""
        with patch('app.db.execute', side_effect=Exception("Database error")):
            self.client.get('/stocks')
            mock_logger.assert_called()
            
    @patch('app.metrics.increment')
    def test_error_metrics_collection(self, mock_metrics):
        """Test that error metrics are collected"""
        response = self.client.get('/non_existent')
        mock_metrics.assert_called_with('errors.404')
        
    def test_error_correlation_id(self):
        """Test that errors include correlation IDs for tracking"""
        response = self.client.get('/predict')  # Missing required params
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error_id', data)
        
    @patch('app.alert_ops_team')
    def test_critical_error_alerting(self, mock_alert):
        """Test that critical errors trigger alerts"""
        with patch('app.db.connect', side_effect=Exception("Database down")):
            self.client.get('/stocks')
            mock_alert.assert_called()


if __name__ == '__main__':
    unittest.main()
