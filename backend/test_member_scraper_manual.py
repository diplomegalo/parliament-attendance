#!/usr/bin/env python3
"""
Manual test script for member scraper.

Since lachambre.be has bot protection, this script helps test the scraper
with manually downloaded HTML.

Usage:
1. Open browser: https://www.lachambre.be/kvvcr/showpage.cfm?section=/depute&language=fr&cfm=cvlist54.cfm?legis=56&today=n
2. Save page as HTML: members_56.html
3. Run: python test_member_scraper_manual.py members_56.html
"""

import sys
import logging
from pathlib import Path
from infrastructure.member_scraper import load_members_from_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)


def main():
    """Test member scraper with manually downloaded HTML."""
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nERROR: Please provide HTML file path")
        print("Example: python test_member_scraper_manual.py members_56.html")
        sys.exit(1)
    
    html_file = Path(sys.argv[1])
    
    if not html_file.exists():
        print(f"ERROR: File not found: {html_file}")
        sys.exit(1)
    
    legislature = 56
    if len(sys.argv) > 2:
        legislature = int(sys.argv[2])
    
    print("=" * 80)
    print(f"TESTING MEMBER SCRAPER - Legislature {legislature}")
    print("=" * 80)
    print(f"Input file: {html_file}")
    print(f"File size: {html_file.stat().st_size:,} bytes")
    print()
    
    try:
        # Load members
        members = load_members_from_file(str(html_file), legislature)
        
        print(f"✓ Successfully parsed {len(members)} members")
        print()
        
        # Show sample members
        print("Sample members (first 10):")
        print("-" * 80)
        for i, member in enumerate(members[:10], 1):
            print(f"{i:2d}. {member.full_name:30s} | "
                  f"{member.party:15s} | {member.constituency}")
        
        if len(members) > 10:
            print(f"... and {len(members) - 10} more")
        
        print()
        
        # Show statistics
        print("Statistics:")
        print("-" * 80)
        
        # Count by party
        parties = {}
        for member in members:
            parties[member.party] = parties.get(member.party, 0) + 1
        
        print(f"Total members: {len(members)}")
        print(f"Unique parties: {len(parties)}")
        print()
        print("Members by party:")
        for party, count in sorted(
            parties.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            print(f"  {party:20s}: {count:3d}")
        
        print()
        print("=" * 80)
        print("✅ TEST COMPLETED SUCCESSFULLY")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
