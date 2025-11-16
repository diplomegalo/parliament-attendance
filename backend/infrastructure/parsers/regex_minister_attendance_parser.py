"""
Regex-based minister attendance parser implementation.

Extracts minister attendance from cleaned parliamentary minutes text
using simple regex pattern matching.
Only processes minutes containing vote nominatif.
"""

from typing import Optional, Dict, Any
import re

from infrastructure.matchers.member_name_matcher import MemberNameMatcher


class RegexMinisterAttendanceParser:
    """
    Minister attendance parser using regex for extraction.
    
    Uses simple regex pattern matching to check if a specific minister's name
    appears in the attendance section of parliamentary minutes.
    Only processes minutes containing vote nominatif.
    """
    
    def __init__(
        self,
        member_matcher: MemberNameMatcher
    ):
        """
        Initialize regex minister attendance parser.
        
        Args:
            member_matcher: Service for fuzzy name matching
        """
        self.member_matcher = member_matcher
    
    def parse_minister_attendance(
        self,
        minute_text: str,
        minute_ref: str,
        minister_name: str,
        legislature: int
    ) -> Optional[Dict[str, Any]]:
        """
        Parse minister attendance from minute text using regex.
        
        Args:
            minute_text: Cleaned text from parliamentary minute
            minute_ref: Minute reference (e.g., "0072")
            minister_name: Full name of minister to search for
            legislature: Legislature number
            
        Returns:
            Dictionary with minister_id, present, confidence, context
            or None if minute has no vote nominatif
        """
        print(f"🔍 Parsing minister attendance for {minute_ref} with regex")
        
        # Check if minute contains vote nominatif
        if not self._has_vote_nominatif(minute_text):
            print(
                f"⚠️  No vote nominatif found in minute {minute_ref}. "
                f"Skipping."
            )
            return None
        
        # Extract DETAIL section (attendance lists)
        detail_section = self._extract_detail_section(minute_text)
        
        if not detail_section:
            print(f"⚠️  No DETAIL section found in minute {minute_ref}")
            detail_section = minute_text
        
        # Search for minister name using regex
        present, context = self._search_minister_name(
            detail_section,
            minister_name
        )
        
        # Set confidence based on match
        confidence = 0.95 if present else 0.95
        
        print(
            f"✅ Regex result: present={present}, "
            f"confidence={confidence:.2f}"
        )
        
        # Match minister name to database
        match = self.member_matcher.find_member_by_name(
            minister_name,
            legislature
        )
        
        if not match:
            print(f"❌ Could not match minister name: {minister_name}")
            return None
        
        member_id, match_score = match
        
        print(
            f"  ✓ '{minister_name}' → Member {member_id} "
            f"(Match: {match_score:.0f}%)"
        )
        
        return {
            'minister_id': member_id,
            'minute_ref': minute_ref,
            'legislature': legislature,
            'present': present,
            'confidence_score': confidence,
            'context': context if context else None
        }
    
    def _has_vote_nominatif(self, text: str) -> bool:
        """
        Check if text contains vote nominatif markers.
        
        Args:
            text: Minute text to check
            
        Returns:
            True if text contains vote nominatif
        """
        vote_markers = [
            'vote nominatif',
            'Stemming/vote',
            'DETAIL VAN DE NAAMSTEMMINGEN',
            'DETAIL DES VOTES NOMINATIFS',
            'Naamstemming'
        ]
        
        text_lower = text.lower()
        return any(marker.lower() in text_lower for marker in vote_markers)
    
    def _extract_detail_section(self, text: str) -> Optional[str]:
        """
        Extract DETAIL section from minute text.
        
        Args:
            text: Full minute text
            
        Returns:
            DETAIL section text or None if not found
        """
        # Pattern to find DETAIL section headers
        detail_pattern = re.compile(
            r'(DETAIL VAN DE NAAMSTEMMINGEN|DETAIL DES VOTES NOMINATIFS)',
            re.IGNORECASE
        )
        
        match = detail_pattern.search(text)
        if match:
            # Return everything from DETAIL section onwards
            return text[match.start():]
        
        return None
    
    def _search_minister_name(
        self,
        text: str,
        minister_name: str
    ) -> tuple[bool, Optional[str]]:
        """
        Search for minister name in text using regex.
        
        Args:
            text: Text to search in
            minister_name: Name to search for
            
        Returns:
            Tuple of (present, context)
        """
        # Split name into parts for flexible matching
        name_parts = minister_name.split()
        
        # Try exact match first (case-insensitive)
        exact_pattern = re.compile(
            re.escape(minister_name),
            re.IGNORECASE
        )
        
        match = exact_pattern.search(text)
        if match:
            # Extract context around match
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end].strip()
            return True, f"Found exact match: ...{context}..."
        
        # Try matching last name only (more flexible)
        if len(name_parts) >= 2:
            last_name = name_parts[-1]
            last_name_pattern = re.compile(
                r'\b' + re.escape(last_name) + r'\b',
                re.IGNORECASE
            )
            
            match = last_name_pattern.search(text)
            if match:
                # Extract context around match
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end].strip()
                return True, f"Found last name match: ...{context}..."
        
        return False, None
