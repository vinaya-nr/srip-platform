"""Comprehensive tests for app.core.exceptions module.

This module tests all custom exception types and their error handling behavior,
including message propagation, status codes, and error envelope generation.
"""

import pytest
from fastapi import status
from app.core.exceptions import (
    SRIPBaseException,
    NotFoundException,
    DuplicateException,
    AuthorizationException,
    ValidationException,
    ExternalServiceException,
    error_envelope,
)


class TestSRIPBaseException:
    """Test suite for SRIPBaseException base class."""
    
    def test_base_exception_message(self):
        """Test exception message is stored properly."""
        exc = SRIPBaseException("Test error")
        assert exc.message == "Test error"
        assert str(exc) == "Test error"
    
    def test_base_exception_default_status_code(self):
        """Test default status code is 400 Bad Request."""
        exc = SRIPBaseException("Test")
        assert exc.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_base_exception_custom_status_code(self):
        """Test custom status code can be provided."""
        exc = SRIPBaseException("Test", status_code=status.HTTP_401_UNAUTHORIZED)
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_base_exception_with_details(self):
        """Test exception can include additional details."""
        details = {"field": "email", "reason": "invalid"}
        exc = SRIPBaseException("Validation failed", details=details)
        assert exc.details == details
    
    def test_base_exception_code(self):
        """Test exception has a code attribute."""
        exc = SRIPBaseException("Test")
        assert exc.code == "SRIP_ERROR"
    
    def test_base_exception_none_details(self):
        """Test exception with None details."""
        exc = SRIPBaseException("Test", details=None)
        assert exc.details is None


class TestNotFoundException:
    """Test suite for NotFoundException."""
    
    def test_not_found_status_code(self):
        """Test NotFoundException returns 404 status."""
        exc = NotFoundException("Resource not found")
        assert exc.status_code == status.HTTP_404_NOT_FOUND
    
    def test_not_found_code(self):
        """Test NotFoundException has correct code."""
        exc = NotFoundException("Resource")
        assert exc.code == "NOT_FOUND"
    
    def test_not_found_message(self):
        """Test NotFoundException message."""
        exc = NotFoundException("User with ID 123")
        assert exc.message == "User with ID 123"
    
    def test_not_found_inheritance(self):
        """Test NotFoundException inherits from SRIPBaseException."""
        exc = NotFoundException("Test")
        assert isinstance(exc, SRIPBaseException)


class TestDuplicateException:
    """Test suite for DuplicateException."""
    
    def test_duplicate_status_code(self):
        """Test DuplicateException returns 409 Conflict status."""
        exc = DuplicateException("Email already exists")
        assert exc.status_code == status.HTTP_409_CONFLICT
    
    def test_duplicate_code(self):
        """Test DuplicateException has correct code."""
        exc = DuplicateException("Duplicate")
        assert exc.code == "DUPLICATE_RESOURCE"
    
    def test_duplicate_message(self):
        """Test DuplicateException message."""
        exc = DuplicateException("Shop name already exists")
        assert exc.message == "Shop name already exists"
    
    def test_duplicate_inheritance(self):
        """Test DuplicateException inherits from SRIPBaseException."""
        exc = DuplicateException("Test")
        assert isinstance(exc, SRIPBaseException)


class TestAuthorizationException:
    """Test suite for AuthorizationException."""
    
    def test_authorization_status_code(self):
        """Test AuthorizationException returns 403 Forbidden status."""
        exc = AuthorizationException("Access denied")
        assert exc.status_code == status.HTTP_403_FORBIDDEN
    
    def test_authorization_code(self):
        """Test AuthorizationException has correct code."""
        exc = AuthorizationException("Not authorized")
        assert exc.code == "AUTHORIZATION_FAILED"
    
    def test_authorization_message(self):
        """Test AuthorizationException message."""
        exc = AuthorizationException("User does not have permission")
        assert exc.message == "User does not have permission"
    
    def test_authorization_inheritance(self):
        """Test AuthorizationException inherits from SRIPBaseException."""
        exc = AuthorizationException("Test")
        assert isinstance(exc, SRIPBaseException)


class TestValidationException:
    """Test suite for ValidationException."""
    
    def test_validation_status_code(self):
        """Test ValidationException returns 422 Unprocessable Entity status."""
        exc = ValidationException("Invalid input")
        assert exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_validation_code(self):
        """Test ValidationException has correct code."""
        exc = ValidationException("Validation")
        assert exc.code == "VALIDATION_FAILED"
    
    def test_validation_message(self):
        """Test ValidationException message."""
        exc = ValidationException("Email format is invalid")
        assert exc.message == "Email format is invalid"
    
    def test_validation_inheritance(self):
        """Test ValidationException inherits from SRIPBaseException."""
        exc = ValidationException("Test")
        assert isinstance(exc, SRIPBaseException)


class TestExternalServiceException:
    """Test suite for ExternalServiceException."""
    
    def test_external_service_status_code(self):
        """Test ExternalServiceException returns 503 Service Unavailable."""
        exc = ExternalServiceException("Payment gateway down")
        assert exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    
    def test_external_service_code(self):
        """Test ExternalServiceException has correct code."""
        exc = ExternalServiceException("Service error")
        assert exc.code == "EXTERNAL_SERVICE_FAILURE"
    
    def test_external_service_message(self):
        """Test ExternalServiceException message."""
        exc = ExternalServiceException("Redis connection failed")
        assert exc.message == "Redis connection failed"
    
    def test_external_service_inheritance(self):
        """Test ExternalServiceException inherits from SRIPBaseException."""
        exc = ExternalServiceException("Test")
        assert isinstance(exc, SRIPBaseException)


class TestErrorEnvelope:
    """Test suite for error_envelope function."""
    
    def test_error_envelope_structure(self):
        """Test error envelope contains required fields."""
        envelope = error_envelope("TEST_CODE", "Test message")
        
        assert envelope["success"] is False
        assert envelope["error"]["code"] == "TEST_CODE"
        assert envelope["error"]["message"] == "Test message"
        assert "timestamp" in envelope["error"]
        assert "correlation_id" in envelope["error"]
    
    def test_error_envelope_with_details(self):
        """Test error envelope includes details when provided."""
        details = {"field": "email"}
        envelope = error_envelope("VALIDATION_ERROR", "Invalid", details)
        
        assert envelope["error"]["details"] == details
    
    def test_error_envelope_without_details(self):
        """Test error envelope details is None when not provided."""
        envelope = error_envelope("ERROR", "Message")
        
        assert envelope["error"]["details"] is None
    
    def test_error_envelope_timestamp_format(self):
        """Test error envelope timestamp is ISO format."""
        envelope = error_envelope("TEST", "Message")
        timestamp = envelope["error"]["timestamp"]
        
        # ISO format check
        assert "T" in timestamp
        assert "+" in timestamp or "Z" in timestamp
    
    def test_error_envelope_with_complex_details(self):
        """Test error envelope with nested details."""
        details = {
            "errors": [
                {"field": "email", "msg": "invalid format"},
                {"field": "password", "msg": "too short"}
            ]
        }
        envelope = error_envelope("VALIDATION_FAILED", "Multiple validation errors", details)
        
        assert envelope["error"]["details"]["errors"]
        assert len(envelope["error"]["details"]["errors"]) == 2
