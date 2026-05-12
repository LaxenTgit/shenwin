"""
Username variation generation engine.
"""

import itertools
from typing import List, Set


LEET_MAP = {
    'a': ['a', '4', '@'],
    'e': ['e', '3'],
    'i': ['i', '1', '!'],
    'o': ['o', '0'],
    's': ['s', '5', '$'],
    't': ['t', '7'],
    'l': ['l', '1'],
    'g': ['g', '9'],
    'b': ['b', '8'],
}


class VariationEngine:
    """
    Generate username variations for broader OSINT coverage.
    """
    
    COMMON_PREFIXES = ["the", "real", "official", "its", "im", "i_am", "mr", "ms"]
    COMMON_SUFFIXES = ["official", "real", "tv", "hd", "gaming", "plays", 
                       "yt", "ig", "fb", "tw", "dev", "code"]
    COMMON_SEPARATORS = ["", "_", "-", "."]
    
    def __init__(self, max_length: int = 30):
        self.max_length = max_length
    
    def generate(self, username: str, 
                 leet: bool = True,
                 numbers: bool = True,
                 prefixes: bool = True,
                 suffixes: bool = True,
                 years: bool = True,
                 max_variations: int = 100) -> List[str]:
        """
        Generate all variations of a username.
        
        Args:
            username: Base username
            leet: Enable leetspeak substitutions
            numbers: Add numeric suffixes (1-999)
            prefixes: Add common prefixes
            suffixes: Add common suffixes  
            years: Add year suffixes (2010-2026)
            max_variations: Limit total variations
        """
        variations: Set[str] = set()
        variations.add(username)  # Always include original
        
        # Leetspeak variations
        if leet:
            leet_vars = self._leet_variations(username)
            variations.update(leet_vars)
        
        # Prefix + original
        if prefixes:
            for prefix in self.COMMON_PREFIXES:
                for sep in self.COMMON_SEPARATORS:
                    if sep:
                        var = f"{prefix}{sep}{username}"
                    else:
                        var = f"{prefix}{username}"
                    if len(var) <= self.max_length:
                        variations.add(var)
        
        # Original + suffix
        if suffixes:
            for suffix in self.COMMON_SUFFIXES:
                for sep in self.COMMON_SEPARATORS:
                    if sep:
                        var = f"{username}{sep}{suffix}"
                    else:
                        var = f"{username}{suffix}"
                    if len(var) <= self.max_length:
                        variations.add(var)
        
        # Numeric suffixes (1-99, common patterns)
        if numbers:
            for i in range(1, 100):
                var = f"{username}{i}"
                if len(var) <= self.max_length:
                    variations.add(var)
            # Common patterns: 123, 007, 666, 999
            for num in [123, 007, 666, 999, 420, 69]:
                var = f"{username}{num}"
                if len(var) <= self.max_length:
                    variations.add(var)
        
        # Year suffixes
        if years:
            for year in range(2010, 2027):
                for sep in ["", "_", "-"]:
                    var = f"{username}{sep}{year}"
                    if len(var) <= self.max_length:
                        variations.add(var)
        
        # Remove original from the set, then convert to list
        variations.discard(username)
        result = list(variations)
        
        # Limit and shuffle for variety
        if len(result) > max_variations:
            import random
            random.shuffle(result)
            result = result[:max_variations]
        
        return result
    
    def _leet_variations(self, username: str) -> List[str]:
        """Generate leetspeak variations."""
        # Get possible substitutions for each char
        char_options = []
        for char in username.lower():
            if char in LEET_MAP:
                char_options.append(LEET_MAP[char])
            else:
                char_options.append([char])
        
        # Generate all combinations (can explode, so limit)
        combinations = list(itertools.product(*char_options))
        
        # Limit to prevent combinatorial explosion
        if len(combinations) > 50:
            import random
            random.shuffle(combinations)
            combinations = combinations[:50]
        
        return ["".join(combo) for combo in combinations]
    
    def generate_similar(self, username: str, count: int = 10) -> List[str]:
        """
        Generate 'similar' usernames (typos, common substitutions).
        Useful for finding impersonation accounts.
        """
        similar = set()
        
        # Common typos: double letters, missing letters
        for i in range(len(username)):
            # Remove one char
            similar.add(username[:i] + username[i+1:])
            # Double one char
            similar.add(username[:i] + username[i] + username[i:])
        
        # Swap adjacent chars
        for i in range(len(username) - 1):
            swapped = list(username)
            swapped[i], swapped[i+1] = swapped[i+1], swapped[i]
            similar.add("".join(swapped))
        
        # Remove original
        similar.discard(username)
        
        result = list(similar)
        if len(result) > count:
            import random
            random.shuffle(result)
            result = result[:count]
        
        return result
    
    def quick_variations(self, username: str) -> List[str]:
        """Fast variation set for quick scans."""
        return self.generate(
            username,
            leet=True,
            numbers=True,
            prefixes=False,
            suffixes=False,
            years=False,
            max_variations=20
        )
