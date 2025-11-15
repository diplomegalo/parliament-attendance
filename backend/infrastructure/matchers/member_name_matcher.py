"""
Member Name Matcher

Fuzzy string matching for member names using RapidFuzz.
Handles name variations and misspellings in attendance records.
"""

import os
from typing import Optional, Tuple, List, Dict, Any

try:
    from rapidfuzz import fuzz
except ImportError:
    raise ImportError("rapidfuzz package is required. Install with: pip install rapidfuzz>=3.0.0")

from domain.repositories.member_repository import IMemberRepository


class MemberNameMatcher:
    """
    Fuzzy name matcher for identifying parliament members from text.
    
    Uses RapidFuzz Levenshtein distance to match names with misspellings,
    different formats (FirstName LastName vs LastName FirstName), and variations.
    """
    
    def __init__(
        self,
        member_repository: IMemberRepository,
        threshold: Optional[int] = None
    ):
        """
        Initialize the member name matcher.
        
        Args:
            member_repository: Repository for accessing member data
            threshold: Minimum similarity score (0-100) for matches (default: 85)
        """
        self.member_repository = member_repository
        self.threshold = threshold or int(os.getenv("FUZZY_MATCH_THRESHOLD", "85"))
        self._members_cache: Dict[int, List[Dict[str, Any]]] = {}
    
    def find_member_by_name(
        self,
        name: str,
        legislature: int,
        threshold: Optional[int] = None
    ) -> Optional[Tuple[int, float]]:
        """
        Find a member by name using fuzzy matching.
        
        Args:
            name: Name to search for (can be in various formats)
            legislature: Legislature number to search within
            threshold: Optional custom threshold for this search
            
        Returns:
            Tuple of (member_id, confidence_score) if found, None otherwise
            Confidence score is 0-100 representing match quality
        """
        min_threshold = threshold or self.threshold
        members = self._get_members(legislature)
        
        if not members:
            return None
        
        best_match = None
        best_score = 0.0
        
        # Normalize search name
        search_name = name.strip().lower()
        
        for member in members:
            # Try multiple name variations
            variations = [
                member["full_name"].lower(),
                member["last_name"].lower(),
                f"{member['first_name']} {member['last_name']}".lower(),
                f"{member['last_name']} {member['first_name']}".lower()
            ]
            
            # Find best match among variations
            for variation in variations:
                score = fuzz.ratio(search_name, variation)
                
                if score > best_score:
                    best_score = score
                    best_match = member["id"]
        
        # Return match only if above threshold
        if best_score >= min_threshold:
            return (best_match, best_score)
        
        return None
    
    def find_multiple_matches(
        self,
        name: str,
        legislature: int,
        limit: int = 5,
        min_score: int = 70
    ) -> List[Tuple[int, str, float]]:
        """
        Find multiple potential matches for disambiguation.
        
        Args:
            name: Name to search for
            legislature: Legislature number
            limit: Maximum number of matches to return
            min_score: Minimum similarity score to include
            
        Returns:
            List of (member_id, full_name, confidence_score) tuples,
            sorted by confidence score (highest first)
        """
        members = self._get_members(legislature)
        
        if not members:
            return []
        
        matches = []
        search_name = name.strip().lower()
        
        for member in members:
            # Try multiple name variations
            variations = [
                member["full_name"].lower(),
                f"{member['first_name']} {member['last_name']}".lower(),
                f"{member['last_name']} {member['first_name']}".lower()
            ]
            
            # Find best match among variations
            best_score = max(fuzz.ratio(search_name, var) for var in variations)
            
            if best_score >= min_score:
                matches.append((
                    member["id"],
                    member["full_name"],
                    best_score
                ))
        
        # Sort by score (highest first) and limit
        matches.sort(key=lambda x: x[2], reverse=True)
        return matches[:limit]
    
    def _get_members(self, legislature: int) -> List[Dict[str, Any]]:
        """
        Get members for a legislature, using cache.
        
        Args:
            legislature: Legislature number
            
        Returns:
            List of member dictionaries
        """
        if legislature not in self._members_cache:
            self._members_cache[legislature] = self.member_repository.find_by_legislature(legislature)
        
        return self._members_cache[legislature]
    
    def clear_cache(self):
        """Clear the members cache."""
        self._members_cache.clear()
