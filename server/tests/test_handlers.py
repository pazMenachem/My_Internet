import pytest
from unittest import mock
from typing import Dict, Any
from My_Internet.server.src.handlers import (
    RequestHandler, 
    AdultContentBlockHandler,
    DomainBlockHandler,
    AdBlockHandler,
    RequestFactory,
    EASYLIST_URL
)
from My_Internet.server.src.response_codes import (
    Codes,
    RESPONSE_MESSAGES
)

class TestAdBlockHandler:
    @pytest.fixture
    def handler(self, mock_db_manager: mock.Mock, mock_requests: mock.Mock) -> AdBlockHandler:
        """Create handler instance."""
        with mock.patch('My_Internet.server.src.handlers.AdBlockHandler.load_easylist'):
            handler = AdBlockHandler(mock_db_manager)
            mock_requests.reset_mock()
            return handler

    def test_load_easylist(self, handler: AdBlockHandler, mock_requests: mock.Mock) -> None:
        """Test loading and parsing easylist."""
        # Configure mock response
        mock_response = mock.Mock()
        mock_response.text = "test.com\n!comment\nexample.com"
        mock_requests.get.return_value = mock_response

        # Call method
        handler.load_easylist()
        
        # Verify calls
        mock_requests.get.assert_called_once_with(EASYLIST_URL)
        mock_response.raise_for_status.assert_called_once()
        handler.db_manager.clear_easylist.assert_called_once()
        
        # Verify easylist storage
        expected_entries = [('test.com',), ('example.com',)]
        handler.db_manager.store_easylist_entries.assert_called_once_with(expected_entries)

    def test_handle_toggle_request(self, handler: AdBlockHandler) -> None:
        """Test toggling ad blocking on/off."""
        # Test enabling
        response = handler.handle_request({'action': 'on'})
        handler.db_manager.update_setting.assert_called_with('ad_block', 'on')
        assert response['code'] == Codes.CODE_AD_BLOCK

        # Test disabling
        response = handler.handle_request({'action': 'off'})
        handler.db_manager.update_setting.assert_called_with('ad_block', 'off')
        assert response['code'] == Codes.CODE_AD_BLOCK

    def test_handle_check_domain(self, handler: AdBlockHandler) -> None:
        """Test checking domain with ad blocking."""
        # Setup: ad blocking enabled and domain matched in easylist
        handler.db_manager.get_setting.return_value = 'on'
        handler.db_manager.is_easylist_blocked.return_value = True
        
        response = handler.handle_request({'domain': 'ads.example.com'})
        assert response['code'] == Codes.CODE_AD_BLOCK
        assert handler.db_manager.is_easylist_blocked.called

class TestAdultContentBlockHandler:
    @pytest.fixture
    def handler(self, mock_db_manager: mock.Mock) -> AdultContentBlockHandler:
        """Create handler instance."""
        return AdultContentBlockHandler(mock_db_manager)

    def test_handle_toggle_request(self, handler: AdultContentBlockHandler) -> None:
        """Test toggling adult content blocking."""
        # Test enabling
        response = handler.handle_request({'action': 'on'})
        handler.db_manager.update_setting.assert_called_with('adult_block', 'on')
        assert response['code'] == Codes.CODE_ADULT_BLOCK

        # Test disabling
        response = handler.handle_request({'action': 'off'})
        handler.db_manager.update_setting.assert_called_with('adult_block', 'off')
        assert response['code'] == Codes.CODE_ADULT_BLOCK

    def test_handle_check_request(self, handler: AdultContentBlockHandler) -> None:
        """Test checking domain with adult content blocking."""
        # Setup: adult blocking enabled
        handler.db_manager.get_setting.return_value = 'on'
        
        response = handler.handle_request({
            'action': 'check',
            'domain': 'example.com'
        })
        assert response['code'] == Codes.CODE_ADULT_BLOCK

class TestDomainBlockHandler:
    @pytest.fixture
    def handler(self, mock_db_manager: mock.Mock) -> DomainBlockHandler:
        """Create handler instance."""
        return DomainBlockHandler(mock_db_manager)

    def test_block_domain(self, handler: DomainBlockHandler) -> None:
        """Test blocking a domain."""
        response = handler.handle_request({
            'action': 'block',
            'domain': 'example.com'
        })
        
        handler.db_manager.add_blocked_domain.assert_called_once_with('example.com')
        assert response['code'] == Codes.CODE_ADD_DOMAIN

    def test_unblock_domain(self, handler: DomainBlockHandler) -> None:
        """Test unblocking a domain."""
        # Setup: domain exists
        handler.db_manager.is_domain_blocked.return_value = True
        
        response = handler.handle_request({
            'action': 'unblock',
            'domain': 'example.com'
        })
        
        handler.db_manager.remove_blocked_domain.assert_called_once_with('example.com')
        assert response['code'] == Codes.CODE_REMOVE_DOMAIN

    def test_unblock_nonexistent_domain(self, handler: DomainBlockHandler) -> None:
        """Test unblocking a nonexistent domain."""
        handler.db_manager.remove_blocked_domain.return_value = False
        
        response = handler.handle_request({
            'action': 'unblock',
            'domain': 'nonexistent.com'
        })
                
        assert 'domain not found' in response['message'].lower()


class TestRequestFactory:
    @pytest.fixture
    def factory(self, mock_db_manager: mock.Mock) -> RequestFactory:
        """Create factory instance."""
        return RequestFactory(mock_db_manager)

    def test_create_handlers(self, factory: RequestFactory) -> None:
        """Test creating different types of handlers."""
        test_cases = [
            (Codes.CODE_AD_BLOCK, AdBlockHandler),
            (Codes.CODE_ADULT_BLOCK, AdultContentBlockHandler),
            (Codes.CODE_ADD_DOMAIN, DomainBlockHandler),
            (Codes.CODE_REMOVE_DOMAIN, DomainBlockHandler)
        ]
        
        for code, handler_class in test_cases:
            handler = factory.create_request_handler(code)
            assert isinstance(handler, handler_class)

    def test_handle_request(self, factory: RequestFactory, sample_requests: dict) -> None:
        """Test handling different types of requests."""
        for request in sample_requests.values():
            response = factory.handle_request(request)
            assert 'code' in response
            assert 'message' in response

    def test_invalid_request_type(self, factory: RequestFactory) -> None:
        """Test handling invalid request type."""
        response = factory.handle_request({'code': 'invalid'})
        assert 'invalid' in response['message'].lower()