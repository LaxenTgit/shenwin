"""
Platform configuration manager.
Loads platform definitions from JSON and provides query interface.
"""

import json
import os
from typing import Dict, List, Optional


DEFAULT_PLATFORMS = {
    "github": {
        "url": "https://github.com/{username}",
        "method": "GET",
        "headers": {"User-Agent": "Mozilla/5.0"},
        "error_type": "status_code",
        "error_msg": "404",
        "category": "development",
        "alexa_rank": 50
    },
    "twitter": {
        "url": "https://twitter.com/{username}",
        "method": "GET",
        "headers": {"User-Agent": "Mozilla/5.0"},
        "error_type": "status_code", 
        "error_msg": "404",
        "category": "social",
        "alexa_rank": 10
    },
    "instagram": {
        "url": "https://www.instagram.com/{username}/",
        "method": "GET",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
        "error_type": "status_code",
        "error_msg": "404",
        "category": "social",
        "alexa_rank": 20
    },
    "reddit": {
        "url": "https://www.reddit.com/user/{username}",
        "method": "GET",
        "headers": {"User-Agent": "Mozilla/5.0"},
        "error_type": "status_code",
        "error_msg": "404",
        "category": "forum",
        "alexa_rank": 15
    },
    "youtube": {
        "url": "https://www.youtube.com/@{username}",
        "method": "GET",
        "headers": {"User-Agent": "Mozilla/5.0"},
        "error_type": "status_code",
        "error_msg": "404",
        "category": "social",
        "alexa_rank": 2
    },
    "twitch": {
        "url": "https://www.twitch.tv/{username}",
        "method": "GET",
        "headers": {"User-Agent": "Mozilla/5.0"},
        "error_type": "status_code",
        "error_msg": "404",
        "category": "gaming",
        "alexa_rank": 100
    },
    "steam": {
        "url": "https://steamcommunity.com/id/{username}",
        "method": "GET",
        "headers": {"User-Agent": "Mozilla/5.0"},
        "error_type": "status_code",
        "error_msg": "404",
        "category": "gaming",
        "alexa_rank": 500
    },
    "gitlab": {
        "url": "https://gitlab.com/{username}",
        "method": "GET",
        "headers": {"User-Agent": "Mozilla/5.0"},
        "error_type": "status_code",
        "error_msg": "404",
        "category": "development",
        "alexa_rank": 2000
    },
    "medium": {
        "url": "https://medium.com/@{username}",
        "method": "GET",
        "headers": {"User-Agent": "Mozilla/5.0"},
        "error_type": "status_code",
        "error_msg": "404",
        "category": "blogging",
        "alexa_rank": 300
    },
    "deviantart": {
        "url": "https://{username}.deviantart.com",
        "method": "GET",
        "headers": {"User-Agent": "Mozilla/5.0"},
        "error_type": "status_code",
        "error_msg": "404",
        "category": "art",
        "alexa_rank": 1000
    }
    # ... 490+ more
}


class PlatformManager:
    """
    Manages platform definitions. Can load from JSON file or use defaults.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self._platforms: Dict[str, Dict] = {}
        self._config_path = config_path or self._get_default_config_path()
        self._load()
    
    def _get_default_config_path(self) -> str:
        """Get path to platforms.json in package data directory."""
        package_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(os.path.dirname(package_dir), "data")
        return os.path.join(data_dir, "platforms.json")
    
    def _load(self) -> None:
        """Load platforms from JSON or use defaults."""
        if os.path.exists(self._config_path):
            try:
                with open(self._config_path, "r", encoding="utf-8") as f:
                    self._platforms = json.load(f)
                return
            except (json.JSONDecodeError, IOError) as e:
                print(f"[!] Warning: Could not load {self._config_path}: {e}")
                print("[!] Using default platforms")
        
        self._platforms = DEFAULT_PLATFORMS.copy()
        self._save_defaults()
    
    def _save_defaults(self) -> None:
        """Save default platforms to JSON for user customization."""
        os.makedirs(os.path.dirname(self._config_path), exist_ok=True)
        try:
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(self._platforms, f, indent=2, ensure_ascii=False)
        except IOError:
            pass  # Can't write, use in-memory only
    
    def get_platforms(self, names: Optional[List[str]] = None,
                     category: Optional[str] = None) -> Dict[str, Dict]:
        """
        Get platforms filtered by name and/or category.
        
        Args:
            names: Specific platform names (None = all)
            category: Filter by category (None = all)
        """
        result = {}
        
        for name, data in self._platforms.items():
            if names and name not in names:
                continue
            if category and data.get("category") != category:
                continue
            result[name] = data
        
        return result
    
    def get_platform(self, name: str) -> Optional[Dict]:
        """Get single platform by name."""
        return self._platforms.get(name)
    
    def list_platforms(self) -> List[str]:
        """List all platform names."""
        return list(self._platforms.keys())
    
    def list_categories(self) -> List[str]:
        """List all unique categories."""
        return sorted(set(
            p.get("category", "unknown") 
            for p in self._platforms.values()
        ))
    
    def add_platform(self, name: str, config: Dict) -> None:
        """Add new platform at runtime."""
        self._platforms[name] = config
        self._save()
    
    def remove_platform(self, name: str) -> bool:
        """Remove platform. Returns True if existed."""
        if name in self._platforms:
            del self._platforms[name]
            self._save()
            return True
        return False
    
    def update_platform(self, name: str, config: Dict) -> bool:
        """Update existing platform."""
        if name not in self._platforms:
            return False
        self._platforms[name].update(config)
        self._save()
        return True
    
    def _save(self) -> None:
        """Persist current platforms to JSON."""
        try:
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(self._platforms, f, indent=2, ensure_ascii=False)
        except IOError:
            pass
    
    def validate(self) -> List[str]:
        """
        Validate all platform configs. Returns list of errors.
        Useful for testing.
        """
        errors = []
        required = ["url", "error_type"]
        
        for name, data in self._platforms.items():
            for field in required:
                if field not in data:
                    errors.append(f"{name}: missing '{field}'")
            
            if "{username}" not in data.get("url", ""):
                errors.append(f"{name}: URL missing {{username}} placeholder")
            
            if data.get("error_type") not in ["status_code", "response_url", "response_text"]:
                errors.append(f"{name}: invalid error_type")
        
        return errors
    
    def stats(self) -> Dict:
        """Get platform statistics."""
        categories = {}
        for data in self._platforms.values():
            cat = data.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "total": len(self._platforms),
            "categories": categories
        }
