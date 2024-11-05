import pytest
from unittest import mock
from typing import Dict, Any
from My_Internet.server.src.handlers import EASYLIST_URL
from My_Internet.server.src.handlers import (
    RequestHandler, 
    AdultContentBlockHandler,
    DomainBlockHandler,
    AdBlockHandler,
    RequestFactory
)
from My_Internet.server.src.response_codes import (
    SUCCESS, 
    INVALID_REQUEST, 
    DOMAIN_BLOCKED,
    DOMAIN_NOT_FOUND, 
    AD_BLOCK_ENABLED,
    ADULT_CONTENT_BLOCKED, 
    RESPONSE_MESSAGES
)

class TestAdultContentBlockHandler:
    @pytest.fixture
    def handler(self, mock_db_manager: mock.Mock) -> AdultContentBlockHandler:
        """Create handler instance and reset state."""
        handler = AdultContentBlockHandler(mock_db_manager)
        # Reset class-level state before each test
        AdultContentBlockHandler._is_enabled = False
        return handler

    def test_init(self, handler: AdultContentBlockHandler, mock_db_manager: mock.Mock) -> None:
        """Test handler initialization."""
        assert handler.db_manager == mock_db_manager
        assert not handler._is_enabled

    def test_handle_enable_request(self, handler: AdultContentBlockHandler) -> None:
        """Test enabling adult content blocking."""
        request_data: Dict[str, Any] = {'action': 'enable'}
        response = handler.handle_request(request_data)
        
        assert response['code'] == SUCCESS
        assert response['adult_content_block'] == 'on'
        assert AdultContentBlockHandler.is_blocking_enabled()

    def test_handle_disable_request(self, handler: AdultContentBlockHandler) -> None:
        """Test disabling adult content blocking."""
        AdultContentBlockHandler._is_enabled = True
        request_data: Dict[str, Any] = {'action': 'disable'}
        
        response = handler.handle_request(request_data)
        
        assert response['code'] == SUCCESS
        assert response['adult_content_block'] == 'off'
        assert not AdultContentBlockHandler.is_blocking_enabled()

    def test_handle_check_request(self, handler: AdultContentBlockHandler) -> None:
        """Test checking domain with blocking enabled."""
        AdultContentBlockHandler._is_enabled = True
        request_data = {'action': 'check', 'domain': 'example.com'}
        
        response = handler.handle_request(request_data)
        
        assert response['code'] == ADULT_CONTENT_BLOCKED

    def test_handle_check_request_disabled(self, handler: AdultContentBlockHandler) -> None:
        """Test checking domain with blocking disabled."""
        request_data = {'action': 'check', 'domain': 'example.com'}
        
        response = handler.handle_request(request_data)
        
        assert response['code'] == SUCCESS

    def test_handle_invalid_request(self, handler: AdultContentBlockHandler) -> None:
        """Test handling invalid requests."""
        invalid_requests = [
            {'action': 'invalid_action'},
            {'action': 'check'},  # Missing domain
            {}  # Empty request
        ]
        
        for request_data in invalid_requests:
            response = handler.handle_request(request_data)
            assert response['code'] == INVALID_REQUEST


class TestDomainBlockHandler:
    @pytest.fixture
    def handler(self, mock_db_manager: mock.Mock) -> DomainBlockHandler:
        """Create handler instance."""
        return DomainBlockHandler(mock_db_manager)

    def test_block_domain(self, handler: DomainBlockHandler, sample_domains: list[str]) -> None:
        """Test blocking a domain."""
        domain = sample_domains[0]
        response = handler.handle_request({
            'action': 'block',
            'domain': domain
        })
        
        handler.db_manager.add_blocked_domain.assert_called_once_with(domain)
        assert response['code'] == DOMAIN_BLOCKED

    def test_unblock_domain(self, handler: DomainBlockHandler, sample_domains: list[str]) -> None:
        """Test unblocking a domain."""
        domain = sample_domains[0]
        handler.db_manager.is_domain_blocked.return_value = True
        
        response = handler.handle_request({
            'action': 'unblock',
            'domain': domain
        })
        
        handler.db_manager.remove_blocked_domain.assert_called_once_with(domain)
        assert response['code'] == SUCCESS

    def test_unblock_nonexistent_domain(self, handler: DomainBlockHandler) -> None:
        """Test unblocking a domain that isn't blocked."""
        handler.db_manager.is_domain_blocked.return_value = False
        
        response = handler.handle_request({
            'action': 'unblock',
            'domain': 'nonexistent.com'
        })
        
        assert response['code'] == DOMAIN_NOT_FOUND


class TestAdBlockHandler:
    @pytest.fixture
    def handler(self, mock_db_manager: mock.Mock, mock_requests: mock.Mock) -> AdBlockHandler:
        """Create handler instance with loading disabled."""
        with mock.patch('My_Internet.server.src.handlers.AdBlockHandler.load_easylist'):
            # Create handler without loading easylist during initialization
            handler = AdBlockHandler(mock_db_manager)
            # Reset the mock before the test
            mock_requests.reset_mock()
            return handler

    def test_load_easylist(self, handler: AdBlockHandler, mock_requests: mock.Mock) -> None:
        """Test loading the easylist."""
        # Configure mock response
        mock_response = mock.Mock()
        mock_response.text = "test.com\n!comment\nexample.com"
        mock_requests.get.return_value = mock_response

        # Call method
        handler.load_easylist()
        
        # Verify calls using the imported constant
        mock_requests.get.assert_called_once_with(EASYLIST_URL)
        mock_response.raise_for_status.assert_called_once()
        handler.db_manager.clear_easylist.assert_called_once()
        
        # Verify that store_easylist_entries was called with correct data
        expected_entries = [('test.com',), ('example.com',)]
        handler.db_manager.store_easylist_entries.assert_called_once_with(expected_entries)

    def test_handle_check_request(self, handler: AdBlockHandler) -> None:
        """Test checking a domain against easylist."""
        handler.db_manager.is_easylist_blocked.return_value = True
        response = handler.handle_request({'domain': 'example.com'})
        
        assert response['code'] == AD_BLOCK_ENABLED

    def test_handle_check_request_not_blocked(self, handler: AdBlockHandler) -> None:
        """Test checking an unblocked domain."""
        handler.db_manager.is_easylist_blocked.return_value = False
        response = handler.handle_request({'domain': 'example.com'})
        
        assert response['code'] == SUCCESS


class TestRequestFactory:
    def test_create_handlers(self, request_factory: RequestFactory) -> None:
        """Test creating different types of handlers."""
        handlers = {
            'ad_block': AdBlockHandler,
            'domain_block': DomainBlockHandler,
            'adult_content_block': AdultContentBlockHandler
        }
        
        for handler_type, handler_class in handlers.items():
            handler = request_factory.create_request_handler(handler_type)
            assert isinstance(handler, handler_class)

    @mock.patch.object(AdultContentBlockHandler, 'handle_request')
    def test_request_delegation(
        self, 
        mock_handle: mock.Mock,
        request_factory: RequestFactory
    ) -> None:
        """Test request delegation to appropriate handler."""
        expected_response = {'code': SUCCESS, 'message': 'Test response'}
        mock_handle.return_value = expected_response
        
        request_data = {
            'type': 'adult_content_block',
            'action': 'enable'
        }
        
        response = request_factory.handle_request(request_data)
        mock_handle.assert_called_once_with(request_data)
        assert response == expected_response

    def test_handle_invalid_request_type(self, request_factory: RequestFactory) -> None:
        """Test handling invalid request type."""
        response = request_factory.handle_request({'type': 'invalid_type'})
        assert response['code'] == INVALID_REQUEST

    def test_factory_handler_integration(self, request_factory: RequestFactory) -> None:
        """Test integration between factory and handlers."""
        test_cases = [
            {
                'request': {'type': 'adult_content_block', 'action': 'enable'},
                'expected_code': SUCCESS
            },
            {
                'request': {'type': 'domain_block', 'action': 'block', 'domain': 'example.com'},
                'expected_code': DOMAIN_BLOCKED
            },
            {
                'request': {'type': 'ad_block', 'domain': 'test.com'},
                'expected_code': SUCCESS
            }
        ]
        
        for test_case in test_cases:
            response = request_factory.handle_request(test_case['request'])
            assert response['code'] == test_case['expected_code']