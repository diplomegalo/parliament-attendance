"""
LLM-based attendance parser implementation.

Extracts member attendance from cleaned parliamentary minutes text
using Large Language Model with fuzzy name matching.
"""

import os
from typing import List, Dict, Any

from domain.repositories.llm_client import ILLMClient
from infrastructure.matchers.member_name_matcher import MemberNameMatcher


class LLMAttendanceParser:
    """
    Attendance parser using LLM for extraction.
    
    Uses a Large Language Model to extract member names and speaking
    activity from parliamentary minutes, then matches names to database
    members using fuzzy matching.
    """
    
    def __init__(
        self,
        llm_client: ILLMClient,
        member_matcher: MemberNameMatcher,
        max_text_length: int = 15000
    ):
        """
        Initialize LLM attendance parser.
        
        Args:
            llm_client: LLM client for text extraction
            member_matcher: Service for fuzzy name matching
            max_text_length: Maximum text length to send to LLM
        """
        self.llm_client = llm_client
        self.member_matcher = member_matcher
        self.max_text_length = max_text_length
        self.dry_run = os.getenv('DRY_RUN', 'false').lower() == 'true'
    
    def parse_attendance(
        self,
        minute_text: str,
        session_ref: str,
        legislature: int
    ) -> List[Dict[str, Any]]:
        """
        Parse attendance from minute text using LLM.
        
        Args:
            minute_text: Cleaned text from parliamentary minute
            session_ref: Session reference
            legislature: Legislature number
            
        Returns:
            List of attendance dictionaries with member_id, spoke, confidence
        """
        print(f"🤖 Parsing attendance for {session_ref} (dry_run={self.dry_run})")
        
        # Truncate text if too long
        if len(minute_text) > self.max_text_length:
            print(f"⚠️  Text too long ({len(minute_text)} chars), truncating to {self.max_text_length}")
            minute_text = minute_text[:self.max_text_length]
        
        # Build prompt for LLM
        prompt = self._build_extraction_prompt(minute_text)
        
        # Extract structured data from LLM
        try:
            schema = {
                "type": "object",
                "properties": {
                    "members": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "spoke": {"type": "boolean"},
                                "confidence": {"type": "number"}
                            },
                            "required": ["name", "spoke", "confidence"]
                        }
                    }
                },
                "required": ["members"]
            }
            
            response = self.llm_client.extract_structured_data(
                prompt=prompt,
                schema=schema,
                temperature=0.0  # Deterministic for data extraction
            )
            
            print(f"✅ LLM extracted {len(response.get('members', []))} member records")
            
        except Exception as e:
            print(f"❌ LLM extraction failed: {e}")
            raise
        
        # Parse LLM response and match to database members
        attendances = self._parse_llm_response(
            response,
            session_ref,
            legislature
        )
        
        print(f"✅ Matched {len(attendances)} members to database")
        
        return attendances
    
    def _build_extraction_prompt(self, minute_text: str) -> str:
        """
        Build prompt for LLM to extract attendance.
        
        Args:
            minute_text: Cleaned minute text
            
        Returns:
            Formatted prompt string
        """
        return f"""
You are analyzing Belgian Chamber of Representatives parliamentary minutes.
Extract the names of all parliament members mentioned in this text.

For each member, determine:
1. Their full name (exactly as written)
2. Whether they spoke (made interventions) during the session

IMPORTANT:
- Only include parliament MEMBERS (not ministers, staff, or visitors)
- Set "spoke" to true ONLY if they made a speech or intervention
- Set "spoke" to false if only mentioned as present
- Confidence should be 0.9-1.0 for clear mentions, 0.7-0.8 for uncertain

TEXT TO ANALYZE:
{minute_text}

Respond with valid JSON following this exact schema:
{{
  "members": [
    {{
      "name": "Full Name As Written",
      "spoke": true or false,
      "confidence": 0.7 to 1.0
    }}
  ]
}}
"""
    
    def _parse_llm_response(
        self,
        response: dict,
        session_ref: str,
        legislature: int
    ) -> List[Dict[str, Any]]:
        """
        Parse LLM JSON response and match to database members.
        
        Args:
            response: JSON response from LLM
            session_ref: Session reference
            legislature: Legislature number
            
        Returns:
            List of attendance dictionaries
        """
        attendances = []
        unmatched = []
        
        members_data = response.get('members', [])
        
        for member_data in members_data:
            extracted_name = member_data.get('name', '')
            spoke = member_data.get('spoke', False)
            llm_confidence = member_data.get('confidence', 0.8)
            
            # Match extracted name to database member
            match = self.member_matcher.find_member_by_name(
                extracted_name,
                legislature
            )
            
            if match:
                member_id, match_score = match
                
                # Combine LLM and matching confidence (take minimum)
                final_confidence = min(llm_confidence, match_score / 100.0)
                
                attendance = {
                    'member_id': member_id,
                    'session_ref': session_ref,
                    'spoke': spoke,
                    'confidence': final_confidence
                }
                
                attendances.append(attendance)
                
                print(f"  ✓ '{extracted_name}' → Member {member_id} "
                      f"(LLM: {llm_confidence:.2f}, Fuzzy: {match_score:.0f}%, "
                      f"Final: {final_confidence:.2f})")
            else:
                unmatched.append(extracted_name)
                print(f"  ✗ No match for: '{extracted_name}'")
        
        if unmatched:
            print(f"\n⚠️  {len(unmatched)} names could not be matched:")
            for name in unmatched[:5]:
                print(f"    - {name}")
            if len(unmatched) > 5:
                print(f"    ... and {len(unmatched) - 5} more")
        
        return attendances
