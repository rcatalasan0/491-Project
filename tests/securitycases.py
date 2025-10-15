"""
Security Tests for Stock Predictor API

Tests for common vulnerabilities:
- SQL Injection
- XSS attacks
- Authentication bypass attempts
- Rate limiting
- Input validation

Run with: pytest tests/security/test_security.py -v
"""

import pytest
import requests
import sys

sys.path.insert(0, '.')
from app import app


@pytest.fixture
def client():
    """Flask test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestSQLInjection:
    """Test for SQL injection vulnerabilities"""
    
    SQL_INJECTION_PAYLOADS = [
        "' OR '1'='1",
        "'; DROP TABLE stocks;--",
        "1' UNION SELECT * FROM users--",
        "admin'--",
        "' OR 1=1--",
        "'; DELETE FROM prices WHERE '1'='1",
        "1'; UPDATE stocks SET price=0--",
    ]
    
    def test_ticker_parameter_sql_injection(self, client):
        """Test ticker parameter against SQL injection"""
        for payload in self.SQL_INJECTION_PAYLOADS:
            response = client.get(f'/predict?ticker={payload}&days=7')
            
            # Should either return 404 (not found) or 400 (bad request)
            # Should NOT return 200 or cause server error
            assert response.status_code in [400, 404]
            
            # Response should still be valid JSON
            data = response.get_json()
            assert data is not None
            assert 'error' in data
    
    def test_days_parameter_sql_injection(self, client):
        """Test days parameter against SQL injection"""
        for payload in self.SQL_INJECTION_PAYLOADS:
            response = client.get(f'/predict?ticker=LMT&days={payload}')
            
            # Should handle gracefully
            assert response.status_code in [400, 404, 500]


class TestXSSAttacks:
    """Test for Cross-Site Scripting vulnerabilities"""
    
    XSS_PAYLOADS = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "javascript:alert('XSS')",
        "<svg/onload=alert('XSS')>",
        "<iframe src='javascript:alert(1)'>",
        "'-alert(1)-'",
        "\"><script>alert(String.fromCharCode(88,83,83))</script>",
    ]
    
    def test_ticker_parameter_xss(self, client):
        """Test ticker parameter against XSS attacks"""
        for payload in self.XSS_PAYLOADS:
            response = client.get(f'/predict?ticker={payload}&days=7')
            
            # Response should be JSON, not HTML with executable script
            assert response.content_type == 'application/json'
            
            # Response body should not contain unescaped script tags
            response_text = response.data.decode('utf-8')
            assert '<script>' not in response_text.lower()
            assert 'onerror=' not in response_text.lower()
    
    def test_response_headers_prevent_xss(self, client):
        """Check for security headers"""
        response = client.get('/health')
        
        # Check for Content-Type header
        assert 'application/json' in response.content_type


class TestInputValidation:
    """Test input validation and sanitization"""
    
    def test_ticker_length_validation(self, client):
        """Test ticker parameter length limits"""
        # Very long ticker
        long_ticker = "A" * 1000
        response = client.get(f'/predict?ticker={long_ticker}&days=7')
        assert response.status_code in [400, 404]
    
    def test_days_range_validation(self, client):
        """Test days parameter range validation"""
        invalid_days = [-1, 0, 31, 100, 9999]
        
        for days in invalid_days:
            response = client.get(f'/predict?ticker=LMT&days={days}')
            assert response.status_code == 400
            data = response.get_json()
            assert 'error' in data
    
    def test_special_characters_in_ticker(self, client):
        """Test special characters in ticker parameter"""
        special_chars = ['!@#$%', '../../etc/passwd', '../../../', '||', '&&', ';', '|']
        
        for char in special_chars:
            response = client.get(f'/predict?ticker={char}&days=7')
            # Should handle gracefully, not crash
            assert response.status_code in [400, 404]
    
    def test_unicode_characters_handled(self, client):
        """Test Unicode characters don't cause issues"""
        unicode_tickers = ['测试', '日本語', '한글', 'עברית', 'مرحبا']
        
        for ticker in unicode_tickers:
            response = client.get(f'/predict?ticker={ticker}&days=7')
            # Should handle gracefully
            assert response.status_code in [400, 404]
            assert response.get_json() is not None


class TestAuthenticationSecurity:
    """Test authentication and authorization (for future implementation)"""
    
    def test_no_sensitive_info_in_responses(self, client):
        """Ensure no sensitive info in error messages"""
        response = client.get('/predict?ticker=INVALID')
        data = response.get_json()
        
        # Should not expose:
        sensitive_keywords = [
            'password', 'secret', 'key', 'token', 
            'database', 'connection', 'stack trace',
            'exception', 'traceback'
        ]
        
        response_text = str(data).lower()
        for keyword in sensitive_keywords:
            assert keyword not in response_text
    
    def test_no_directory_traversal(self, client):
        """Test against directory traversal attacks"""
        traversal_attempts = [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32',
            '....//....//....//etc/passwd',
        ]
        
        for attempt in traversal_attempts:
            response = client.get(f'/predict?ticker={attempt}&days=7')
            # Should not succeed or expose filesystem
            assert response.status_code in [400, 404]


class TestDenialOfService:
    """Test for potential DoS vulnerabilities"""
    
    def test_large_days_parameter(self, client):
        """Test with very large days parameter"""
        response = client.get('/predict?ticker=LMT&days=999999999')
        # Should reject gracefully, not timeout
        assert response.status_code == 400
    
    def test_rapid_requests_handled(self, client):
        """Test system handles rapid requests"""
        # Make 100 rapid requests
        for i in range(100):
            response = client.get('/health')
            # Should handle all requests
            assert response.status_code == 200
    
    def test_multiple_parameter_combinations(self, client):
        """Test with many parameter variations"""
        for i in range(50):
            response = client.get(f'/predict?ticker=LMT&days=7&extra={i}')
            # Should handle extra parameters gracefully
            assert response.status_code in [200, 400]


class TestHTTPSecurity:
    """Test HTTP security best practices"""
    
    def test_cors_configuration(self, client):
        """Test CORS headers are properly set"""
        response = client.get('/health')
        
        # CORS should be enabled for development
        assert 'Access-Control-Allow-Origin' in response.headers
    
    def test_content_type_headers(self, client):
        """Test proper Content-Type headers"""
        endpoints = ['/health', '/stocks', '/predict?ticker=LMT&days=7']
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            if response.status_code == 200:
                assert 'application/json' in response.content_type
    
    def test_no_sensitive_headers_leaked(self, client):
        """Ensure sensitive headers are not exposed"""
        response = client.get('/health')
        
        # Should not expose these headers
        sensitive_headers = ['X-Powered-By', 'Server']
        
        for header in sensitive_headers:
            # It's okay if they're not present
            if header in response.headers:
                # But if present, should not reveal too much
                value = response.headers[header].lower()
                assert 'version' not in value


class TestErrorHandling:
    """Test secure error handling"""
    
    def test_404_doesnt_expose_structure(self, client):
        """404 errors should not expose internal structure"""
        response = client.get('/nonexistent/path/deeply/nested')
        assert response.status_code == 404
        
        data = response.get_json()
        # Should be generic error, not expose filesystem
        assert 'error' in data
    
    def test_500_errors_handled_gracefully(self, client):
        """500 errors should not expose stack traces"""
        # Try to trigger an error (if possible)
        response = client.get('/predict?ticker=LMT&days=abc')
        
        # Should not contain stack trace
        if response.status_code == 500:
            response_text = response.data.decode('utf-8')
            assert 'Traceback' not in response_text
            assert 'File "' not in response_text


class TestDataLeakage:
    """Test for information disclosure"""
    
    def test_error_messages_not_verbose(self, client):
        """Error messages should not be too verbose"""
        response = client.get('/predict?ticker=INVALID')
        data = response.get_json()
        
        error_msg = data.get('error', '')
        
        # Should not contain:
        assert 'exception' not in error_msg.lower()
        assert 'traceback' not in error_msg.lower()
        assert 'line ' not in error_msg.lower()
    
    def test_internal_paths_not_exposed(self, client):
        """Internal file paths should not be exposed"""
        response = client.get('/predict?ticker=INVALID')
        response_text = response.data.decode('utf-8')
        
        # Should not expose file paths
        assert '/app/' not in response_text
        assert 'C:\\' not in response_text
        assert '/home/' not in response_text
        assert 'src/' not in response_text


class TestSecurityRecommendations:
    """Tests for future security enhancements"""
    
    @pytest.mark.skip(reason="To be implemented in Sprint 3")
    def test_rate_limiting_enabled(self, client):
        """Rate limiting should be implemented"""
        # Make many requests rapidly
        responses = []
        for i in range(150):
            response = client.get('/predict?ticker=LMT&days=7')
            responses.append(response.status_code)
        
        # Should get rate limited (429 status)
        assert 429 in responses
    
    @pytest.mark.skip(reason="To be implemented in Sprint 3")
    def test_jwt_authentication_required(self, client):
        """JWT authentication should be required for predictions"""
        response = client.get('/predict?ticker=LMT&days=7')
        # Without auth token, should return 401
        assert response.status_code == 401
    
    @pytest.mark.skip(reason="To be implemented when HTTPS is configured")
    def test_https_only(self, client):
        """API should only be accessible via HTTPS"""
        # This test would need to run against deployed environment
        pass


if __name__ == '__main__':
    print("🔒 Running Security Tests")
    print("Testing for: SQL Injection, XSS, Input Validation, DoS\n")
    pytest.main([__file__, '-v', '--tb=short'])
