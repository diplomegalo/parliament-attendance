"""
LLM-based minister attendance parser implementation.

Extracts minister attendance from cleaned parliamentary minutes text
using Large Language Model with fuzzy name matching.
Only processes minutes containing vote nominatif.
"""

import os
from typing import Optional, Dict, Any

from domain.repositories.llm_client import ILLMClient
from infrastructure.matchers.member_name_matcher import MemberNameMatcher


class LLMMinisterAttendanceParser:
    """
    Minister attendance parser using LLM for extraction.
    
    Uses a Large Language Model to check if a specific minister's name
    appears in the attendance section of parliamentary minutes.
    Only processes minutes containing vote nominatif.
    """
    
    def __init__(
        self,
        llm_client: ILLMClient,
        member_matcher: MemberNameMatcher,
        max_text_length: int = 15000
    ):
        """
        Initialize LLM minister attendance parser.
        
        Args:
            llm_client: LLM client for text extraction
            member_matcher: Service for fuzzy name matching
            max_text_length: Maximum text length to send to LLM
        """
        self.llm_client = llm_client
        self.member_matcher = member_matcher
        self.max_text_length = max_text_length
        self.dry_run = os.getenv('DRY_RUN', 'false').lower() == 'true'
    
    def parse_minister_attendance(
        self,
        minute_text: str,
        minute_ref: str,
        minister_name: str,
        legislature: int
    ) -> Optional[Dict[str, Any]]:
        """
        Parse minister attendance from minute text using LLM.
        
        Args:
            minute_text: Cleaned text from parliamentary minute
            minute_ref: Minute reference (e.g., "0072")
            minister_name: Full name of minister to search for
            legislature: Legislature number
            
        Returns:
            Dictionary with minister_id, present, confidence, context
            or None if minute has no vote nominatif
        """
        print(
            f"🤖 Parsing minister attendance for {minute_ref} "
            f"(dry_run={self.dry_run})"
        )
        
        # Check if minute contains vote nominatif
        if not self._has_vote_nominatif(minute_text):
            print(
                f"⚠️  No vote nominatif found in minute {minute_ref}. "
                f"Skipping."
            )
            return None
        
        # Truncate text if too long
        if len(minute_text) > self.max_text_length:
            print(
                f"⚠️  Text too long ({len(minute_text)} chars), "
                f"truncating to {self.max_text_length}"
            )
            minute_text = minute_text[:self.max_text_length]
        
        # Build prompt for LLM
        prompt = self._build_extraction_prompt(minute_text, minister_name)
        
        # Extract structured data from LLM
        try:
            schema = {
                "type": "object",
                "properties": {
                    "present": {"type": "boolean"},
                    "confidence": {"type": "number"},
                    "context": {"type": "string"}
                },
                "required": ["present", "confidence"]
            }
            
            response = self.llm_client.extract_structured_data(
                prompt=prompt,
                schema=schema,
                temperature=0.0  # Deterministic for data extraction
            )
            
            present = response.get('present', False)
            confidence = response.get('confidence', 0.0)
            context = response.get('context', '')
            
            print(
                f"✅ LLM result: present={present}, "
                f"confidence={confidence:.2f}"
            )
            
        except Exception as e:
            print(f"❌ LLM extraction failed: {e}")
            raise
        
        # Match minister name to database
        matches = self.member_matcher.match_names(
            [minister_name],
            legislature
        )
        
        if not matches or not matches[0]:
            print(f"❌ Could not match minister name: {minister_name}")
            return None
        
        match = matches[0]
        member_id = match['member_id']
        
        print(
            f"  ✓ '{minister_name}' → Member {member_id} "
            f"(Match: {match['score']:.0%})"
        )
        
        return {
            'minister_id': member_id,
            'minute_ref': minute_ref,
            'legislature': legislature,
            'present': present,
            'confidence': confidence,
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
    
    def _build_extraction_prompt(
        self,
        minute_text: str,
        minister_name: str
    ) -> str:
        """
        Build prompt for LLM to extract minister attendance.
        
        Args:
            minute_text: Text to analyze
            minister_name: Name of minister to search for
            
        Returns:
            Formatted prompt string
        """
        return f"""You are analyzing a Belgian parliamentary minute.

Your task: Determine if the minister named "{minister_name}" was present.

IMPORTANT RULES:
1. Search for "{minister_name}" in the DETAIL section (attendance lists)
2. The DETAIL section is under headers like:
   - "DETAIL VAN DE NAAMSTEMMINGEN"
   - "DETAIL DES VOTES NOMINATIFS"
   - "Naamstemming - Vote nominatif"
3. Return "present": true ONLY if the name appears in attendance lists
4. Return "present": false if name does not appear
5. Provide confidence score (0.0 to 1.0)
6. Optionally provide context (e.g., "Found in Vote 3 attendance")

Parliamentary minute text:
{minute_text}

Return your answer as JSON with fields:
- present (boolean)
- confidence (number between 0 and 1)
- context (optional string)
"""
