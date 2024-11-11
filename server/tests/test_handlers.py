from typing import Dict, Any
import pytest
from unittest import mock
from My_Internet.server.src.handlers import (
    RequestHandler,
    AdBlockHandler,
    AdultContentBlockHandler,
    DomainBlockHandler,
    DomainListHandler,
    RequestFactory
)
from My_Internet.server.src.utils import Codes, RESPONSE_MESSAGES

@pytest.fixture
def mock_db_manager() -> mock.Mock:
    """Create a mock database manager."""
    return mock.Mock()

@pytest.fixture
def mock_logger() -> mock.Mock:
    """Create a mock logger."""
    return mock.Mock()

class TestAdBlockHandler:
    @pytest.fixture
    def handler(self, mock_db_manager: mock.Mock) -> AdBlockHandler:
        """Create AdBlockHandler instance."""
        return AdBlockHandler(mock_db_manager)

    def test_handle_request_toggle_on(self, handler: AdBlockHandler) -> None:
        """Test handling ad block toggle on request."""
        request_data: Dict[str, Any] = {'action': 'on'}
        response = handler.handle_request(request_data)
        
        handler.db_manager.update_setting.assert_called_once_with('ad_block', 'on')
        assert response['code'] == Codes.CODE_AD_BLOCK
        assert response['message'] == "Ad blocking turned on"

    def test_handle_request_error(self, handler: AdBlockHandler) -> None:
        """Test handling error in ad block request."""
        handler.db_manager.update_setting.side_effect = Exception("Test error")
        response = handler.handle_request({'action': 'on'})
        
        assert response['code'] == Codes.CODE_AD_BLOCK
        assert response['message'] == "Test error"

class TestAdultContentBlockHandler:
    @pytest.fixture
    def handler(self, mock_db_manager: mock.Mock) -> AdultContentBlockHandler:
        """Create AdultContentBlockHandler instance."""
        return AdultContentBlockHandler(mock_db_manager)

    def test_handle_request_toggle_on(self, handler: AdultContentBlockHandler) -> None:
        """Test handling adult content block toggle on request."""
        request_data: Dict[str, Any] = {'action': 'on'}
        response = handler.handle_request(request_data)
        
        handler.db_manager.update_setting.assert_called_once_with('adult_block', 'on')
        assert response['code'] == Codes.CODE_ADULT_BLOCK
        assert response['message'] == "Adult content blocking turned on"

class TestDomainBlockHandler:
    @pytest.fixture
    def handler(self, mock_db_manager: mock.Mock) -> DomainBlockHandler:
        """Create DomainBlockHandler instance."""
        return DomainBlockHandler(mock_db_manager)

    def test_block_domain(self, handler: DomainBlockHandler) -> None:
        """Test blocking a domain."""
        request_data: Dict[str, Any] = {
            'action': 'block',
            'domain': 'example.com'
        }
        response = handler.handle_request(request_data)
        
        handler.db_manager.add_blocked_domain.assert_called_once_with('example.com')
        assert response['code'] == Codes.CODE_ADD_DOMAIN
        assert response['message'] == RESPONSE_MESSAGES['domain_blocked']

    def test_unblock_domain(self, handler: DomainBlockHandler) -> None:
        """Test unblocking a domain."""
        handler.db_manager.remove_blocked_domain.return_value = True
        request_data: Dict[str, Any] = {
            'action': 'unblock',
            'domain': 'example.com'
        }
        response = handler.handle_request(request_data)
        
        handler.db_manager.remove_blocked_domain.assert_called_once_with('example.com')
        assert response['code'] == Codes.CODE_REMOVE_DOMAIN
        assert response['message'] == RESPONSE_MESSAGES['success']

    def test_invalid_request(self, handler: DomainBlockHandler) -> None:
        """Test handling invalid request."""
        request_data: Dict[str, Any] = {'action': 'block'}  # Missing domain
        response = handler.handle_request(request_data)
        
        assert response['code'] == Codes.CODE_ADD_DOMAIN
        assert response['message'] == RESPONSE_MESSAGES['invalid_request']

class TestDomainListHandler:
    @pytest.fixture
    def handler(self, mock_db_manager: mock.Mock) -> DomainListHandler:
        """Create DomainListHandler instance."""
        return DomainListHandler(mock_db_manager)

    def test_get_domain_list(self, handler: DomainListHandler) -> None:
        """Test getting list of blocked domains."""
        domains = ['example.com', 'test.com']
        handler.db_manager.get_blocked_domains.return_value = domains
        response = handler.handle_request({})
        
        assert response['code'] == Codes.CODE_DOMAIN_LIST_UPDATE
        assert response['domains'] == domains
        assert response['message'] == RESPONSE_MESSAGES['success']

class TestRequestFactory:
    @pytest.fixture
    def factory(self, mock_db_manager: mock.Mock) -> RequestFactory:
        """Create RequestFactory instance."""
        return RequestFactory(mock_db_manager)

    def test_handle_valid_request(self, factory: RequestFactory) -> None:
        """Test handling valid request with correct code."""
        request_data: Dict[str, Any] = {
            'code': Codes.CODE_AD_BLOCK,
            'action': 'on'
        }
        response = factory.handle_request(request_data)
        assert response['code'] == Codes.CODE_AD_BLOCK

    def test_handle_invalid_code(self, factory: RequestFactory) -> None:
        """Test handling request with invalid code."""
        request_data: Dict[str, Any] = {'code': 'invalid_code'}
        response = factory.handle_request(request_data)
        assert response['message'] == RESPONSE_MESSAGES['invalid_request']