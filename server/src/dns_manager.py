import subprocess
import os
from typing import Optional
from pathlib import Path
from .logger import setup_logger
from .utils import (
    STR_TOGGLE_ON,
    STR_CLOUDFLARE_DNS_SCRIPT,
    STR_ADGUARD_DNS_SCRIPT,
    STR_ADGUARD_FAMILY_DNS_SCRIPT,
    STR_RESET_DNS_SCRIPT
)

class DNSManager:
    """Manages DNS redirection based on ad and adult content blocking settings."""
    
    def __init__(self) -> None:
        self.logger = setup_logger("DNSManager")
        self.scripts_dir = Path(__file__).parent.parent.parent / "scripts"
        
        # Verify scripts exist and are executable
        self._verify_scripts()
    
    def _verify_scripts(self) -> None:
        """Verify all required scripts exist and are executable."""
        required_scripts = [
            STR_CLOUDFLARE_DNS_SCRIPT,
            STR_ADGUARD_DNS_SCRIPT,
            STR_ADGUARD_FAMILY_DNS_SCRIPT,
            STR_RESET_DNS_SCRIPT
        ]
        
        for script in required_scripts:
            script_path = self.scripts_dir / script
            if not script_path.exists():
                raise FileNotFoundError(f"Required script not found: {script}")
            if not os.access(script_path, os.X_OK):
                raise PermissionError(f"Script not executable: {script}")
    
    def _run_script(self, script_name: str) -> None:
        """Run a DNS configuration script."""
        try:
            script_path = self.scripts_dir / script_name
            result = subprocess.run(
                [str(script_path)],
                capture_output=True,
                text=True,
                check=True
            )
            self.logger.info(f"DNS script output: {result.stdout}")
            if result.stderr:
                self.logger.warning(f"DNS script stderr: {result.stderr}")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to run DNS script: {e}")
            raise
    
    def update_dns_settings(self, ad_block: str, adult_block: str) -> None:
        """
        Update DNS settings based on current blocking settings.
        
        Args:
            ad_block: "on" or "off" for ad blocking
            adult_block: "on" or "off" for adult content blocking
        """
        try:
            # Both on - use AdGuard Family
            if ad_block == STR_TOGGLE_ON and adult_block == STR_TOGGLE_ON:
                self.logger.info("Enabling AdGuard Family DNS (ads + adult content)")
                self._run_script(STR_ADGUARD_FAMILY_DNS_SCRIPT)
            
            # Only ad blocking - use AdGuard
            elif ad_block == STR_TOGGLE_ON:
                self.logger.info("Enabling AdGuard DNS (ads only)")
                self._run_script(STR_ADGUARD_DNS_SCRIPT)
            
            # Only adult content blocking - use Cloudflare
            elif adult_block == STR_TOGGLE_ON:
                self.logger.info("Enabling Cloudflare DNS (adult content only)")
                self._run_script(STR_CLOUDFLARE_DNS_SCRIPT)
            
            # Both off - reset DNS
            else:
                self.logger.info("Resetting DNS settings")
                self._run_script(STR_RESET_DNS_SCRIPT)
                
        except Exception as e:
            self.logger.error(f"Failed to update DNS settings: {e}")
            raise