from enum import Enum
from typing import Optional, List, Dict, Any
import re

class PatternType(Enum):
    DOMAIN = "domain"      # ||example.com^
    EXACT = "exact"        # |http://example.com/|
    WILDCARD = "wildcard"  # /banner/*/img^
    EXCEPTION = "exception"  # @@||example.com^

class FilterRule:
    def __init__(self, raw_pattern: str):
        self.raw_pattern = raw_pattern
        self.pattern_type = self._determine_pattern_type()
        self.processed_pattern = self._process_pattern()
        self.options: Dict[str, Any] = self._parse_options()
        
    def _determine_pattern_type(self) -> PatternType:
        pattern = self.raw_pattern.strip()
        
        if pattern.startswith("@@"):
            return PatternType.EXCEPTION
        elif pattern.startswith("||"):
            return PatternType.DOMAIN
        elif pattern.startswith("|") and pattern.endswith("|"):
            return PatternType.EXACT
        else:
            return PatternType.WILDCARD

    def _process_pattern(self) -> str:
        """Process the raw pattern into a normalized form."""
        pattern = self.raw_pattern.strip()
        
        # Remove options part if exists
        if "$" in pattern:
            pattern = pattern.split("$")[0]

        # Process based on type
        if self.pattern_type == PatternType.EXCEPTION:
            return pattern[2:]  # Remove @@
        elif self.pattern_type == PatternType.DOMAIN:
            return pattern[2:-1]  # Remove || and ^
        elif self.pattern_type == PatternType.EXACT:
            return pattern[1:-1]  # Remove leading and trailing |
        else:
            return pattern

    def _parse_options(self) -> Dict[str, Any]:
        """Parse filter options like $script,image,domain=example.com."""
        options = {}
        if "$" in self.raw_pattern:
            options_part = self.raw_pattern.split("$")[1]
            for opt in options_part.split(","):
                if "=" in opt:
                    key, value = opt.split("=")
                    options[key] = value
                else:
                    options[opt] = True
        return options

    def matches(self, url: str, domain: str) -> bool:
        """Check if URL matches this filter rule."""
        # Check domain restrictions if any
        if "domain" in self.options:
            allowed_domains = self.options["domain"].split("|")
            if not any(domain.endswith(d) for d in allowed_domains):
                return False

        # Match based on pattern type
        if self.pattern_type == PatternType.DOMAIN:
            return domain.endswith(self.processed_pattern)
        elif self.pattern_type == PatternType.EXACT:
            return url == self.processed_pattern
        else:
            # Convert wildcard pattern to regex
            regex_pattern = (
                self.processed_pattern
                .replace(".", r"\.")
                .replace("*", ".*")
                .replace("?", ".")
            )
            return bool(re.search(regex_pattern, url))