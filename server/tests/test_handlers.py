from typing import Dict, Any
import pytest
from unittest import mock
from My_Internet.server.src.handlers import (
    RequestHandler,
    AdBlockHandler,
    AdultContentBlockHandler,
    DomainBlockHandler,
    SettingsHandler,
    RequestFactory
)
from My_Internet.server.src.utils import (
    Codes,
    STR_AD_BLOCK,
    STR_ADULT_BLOCK,
    STR_CODE,
    STR_CONTENT,
    STR_OPERATION,
    STR_DOMAINS,
    STR_SETTINGS
)

@pytest.fixture
def mock_db_manager() -> mock.Mock:
    """Provides a mock database manager for testing.
    
    Returns:
        mock.Mock: A mock object simulating DatabaseManager functionality
    """
    return mock.Mock()

@pytest.fixture
def mock_logger() -> mock.Mock:
    """Provides a mock logger for testing.
    
    Returns:
        mock.Mock: A mock object simulating Logger functionality
    """
    return mock.Mock()

@pytest.fixture
def mock_dns_manager():
    """Provides a mock DNS manager for testing.
    
    Returns:
        mock.Mock: A mock object simulating DNSManager functionality with update_dns_settings method
    """
    dns_manager = mock.Mock()
    dns_manager.update_dns_settings = mock.Mock()
    return dns_manager

class TestAdBlockHandler:
    """Test suite for AdBlockHandler functionality."""
    
    @pytest.fixture
    def handler(self, mock_db_manager, mock_dns_manager):
        """Provides configured AdBlockHandler instance for testing.
        
        Args:
            mock_db_manager: Mock database manager fixture
            mock_dns_manager: Mock DNS manager fixture
            
        Returns:
            AdBlockHandler: Configured handler instance
        """
        handler = AdBlockHandler(mock_db_manager)
        handler.dns_manager = mock_dns_manager
        handler.logger = mock.Mock()
        return handler

    def test_handle_request_toggle_on(self, handler: AdBlockHandler) -> None:
        """Verifies ad blocking can be enabled successfully."""
        request_data = {STR_CODE: Codes.CODE_AD_BLOCK, STR_CONTENT: 'on'}
        handler.db_manager.get_setting.return_value = 'on'
        response = handler.handle_request(request_data)
        handler.db_manager.update_setting.assert_called_once_with(STR_AD_BLOCK, 'on')
        assert response[STR_CODE] == Codes.CODE_SUCCESS
        assert response[STR_OPERATION] == Codes.CODE_AD_BLOCK

    def test_handle_request_error(self, handler: AdBlockHandler) -> None:
        """Test handling error in ad block request."""
        request_data = {STR_CODE: Codes.CODE_AD_BLOCK, STR_CONTENT: 'on'}
        handler.db_manager.update_setting.side_effect = Exception("Test error")
        response = handler.handle_request(request_data)
        assert response[STR_CODE] == Codes.CODE_ERROR
        assert response[STR_OPERATION] == Codes.CODE_AD_BLOCK
        assert response[STR_CONTENT] == "Test error"

class TestAdultContentBlockHandler:
    @pytest.fixture
    def handler(self, mock_db_manager, mock_dns_manager):
        handler = AdultContentBlockHandler(mock_db_manager)
        handler.dns_manager = mock_dns_manager
        handler.logger = mock.Mock()
        return handler

    def test_handle_request_toggle_on(self, handler: AdultContentBlockHandler) -> None:
        """Test handling adult content block toggle on request."""
        request_data = {STR_CODE: Codes.CODE_ADULT_BLOCK, STR_CONTENT: 'on'}
        handler.db_manager.get_setting.return_value = 'on'
        response = handler.handle_request(request_data)
        handler.db_manager.update_setting.assert_called_once_with(STR_ADULT_BLOCK, 'on')
        assert response[STR_CODE] == Codes.CODE_SUCCESS
        assert response[STR_OPERATION] == Codes.CODE_ADULT_BLOCK

    def test_handle_request_with_dns_update(self, handler):
        """Test handling adult content block request with DNS update."""
        handler.db_manager.get_setting.return_value = 'on'
        request_data = {STR_CODE: Codes.CODE_ADULT_BLOCK, STR_CONTENT: 'on'}
        response = handler.handle_request(request_data)
        handler.db_manager.update_setting.assert_called_once_with(STR_ADULT_BLOCK, 'on')
        handler.dns_manager.update_dns_settings.assert_called_once_with('on', 'on')
        assert response[STR_CODE] == Codes.CODE_SUCCESS
        assert response[STR_OPERATION] == Codes.CODE_ADULT_BLOCK

class TestDomainBlockHandler:
    @pytest.fixture
    def handler(self, mock_db_manager):
        handler = DomainBlockHandler(mock_db_manager)
        handler.logger = mock.Mock()
        return handler

    def test_block_domain(self, handler: DomainBlockHandler) -> None:
        """Test blocking a domain.
        
        Args:
            handler (DomainBlockHandler): The domain block handler instance
            
        Tests:
            - Domain blocking functionality
            - Proper response codes
            - Correct domain formatting with www prefix
        """
        request_data = {
            STR_CODE: Codes.CODE_ADD_DOMAIN,
            STR_CONTENT: 'example.com'
        }
        handler.db_manager.is_domain_blocked.return_value = False
        response = handler.handle_request(request_data)
        handler.db_manager.add_blocked_domain.assert_called_once_with('www.example.com')
        assert response[STR_CODE] == Codes.CODE_SUCCESS
        assert response[STR_OPERATION] == Codes.CODE_ADD_DOMAIN

    def test_unblock_domain(self, handler: DomainBlockHandler) -> None:
        """Test unblocking a domain."""
        handler.db_manager.remove_blocked_domain.return_value = True
        request_data = {
            STR_CODE: Codes.CODE_REMOVE_DOMAIN,
            STR_CONTENT: 'example.com'
        }
        response = handler.handle_request(request_data)
        handler.db_manager.remove_blocked_domain.assert_called_once_with('www.example.com')
        assert response[STR_CODE] == Codes.CODE_SUCCESS
        assert response[STR_OPERATION] == Codes.CODE_REMOVE_DOMAIN

    def test_invalid_request(self, handler: DomainBlockHandler) -> None:
        """Test handling invalid request."""
        request_data = {STR_CODE: Codes.CODE_ADD_DOMAIN}  
        response = handler.handle_request(request_data)
        assert response[STR_CODE] == Codes.CODE_ERROR
        assert STR_OPERATION not in response  

    def test_block_domain_with_www(self, handler: DomainBlockHandler) -> None:
        """Test blocking domain that already includes www prefix.
        
        Args:
            handler (DomainBlockHandler): The domain block handler instance
            
        Tests:
            - Domain blocking with pre-existing www prefix
            - Proper response codes
            - No duplicate www prefixes
        """
        request_data = {
            STR_CODE: Codes.CODE_ADD_DOMAIN,
            STR_CONTENT: 'www.example.com'
        }
        handler.db_manager.is_domain_blocked.return_value = False
        response = handler.handle_request(request_data)
        handler.db_manager.add_blocked_domain.assert_called_once_with('www.example.com')
        assert response[STR_CODE] == Codes.CODE_SUCCESS
        assert response[STR_OPERATION] == Codes.CODE_ADD_DOMAIN

    def test_block_already_blocked_domain(self, handler):
        """Test blocking already blocked domain."""
        handler.db_manager.is_domain_blocked.return_value = True
        request_data = {
            STR_CODE: Codes.CODE_ADD_DOMAIN,
            STR_CONTENT: 'example.com'
        }
        response = handler.handle_request(request_data)
        assert response[STR_CODE] == Codes.CODE_ERROR
        assert 'already blocked' in response[STR_CONTENT]

class TestSettingsHandler:
    @pytest.fixture
    def handler(self, mock_db_manager, mock_dns_manager):
        """Create SettingsHandler instance."""
        handler = SettingsHandler(mock_db_manager)
        handler.dns_manager = mock_dns_manager
        return handler

    def test_get_settings_and_domains(self, handler):
        """Test getting settings and domain list."""
        handler.db_manager.get_blocked_domains.return_value = ['www.example.com']
        handler.db_manager.get_setting.side_effect = ['on', 'off']
        response = handler.handle_request({})
        assert response[STR_CODE] == Codes.CODE_SUCCESS
        assert response[STR_OPERATION] == Codes.CODE_INIT_SETTINGS
        assert response[STR_DOMAINS] == ['www.example.com']
        assert response[STR_SETTINGS] == {STR_AD_BLOCK: 'on', STR_ADULT_BLOCK: 'off'}
        handler.dns_manager.update_dns_settings.assert_called_once_with('on', 'off')

class TestRequestFactory:
    @pytest.fixture
    def factory(self, mock_db_manager):
        factory = RequestFactory(mock_db_manager)
        factory.logger = mock.Mock()
        return factory

    def test_handle_valid_request(self, factory: RequestFactory) -> None:
        """Test handling valid request with correct code."""
        request_data = {
            STR_CODE: Codes.CODE_AD_BLOCK,
            STR_CONTENT: 'on'
        }
        response = factory.handle_request(request_data)
        assert response[STR_CODE] == Codes.CODE_SUCCESS
        assert response[STR_OPERATION] == Codes.CODE_AD_BLOCK

    def test_handle_invalid_code(self, factory: RequestFactory) -> None:
        """Test handling request with invalid code."""
        request_data = {'code': 'invalid_code'}
        response = factory.handle_request(request_data)
        assert response[STR_CODE] == Codes.CODE_ERROR

    def test_handle_settings_request(self, factory):
        """Test handling settings request."""
        request_data = {STR_CODE: Codes.CODE_INIT_SETTINGS}
        response = factory.handle_request(request_data)
        assert response[STR_CODE] in [Codes.CODE_SUCCESS, Codes.CODE_ERROR]
        assert STR_OPERATION in response