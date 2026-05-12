"""
Core scanning engine for Shenwin.
"""

import urllib.request
import urllib.error
import threading
import queue
import time
import json
from typing import Dict, List, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed

from .platforms import PlatformManager
from .utils import create_opener, normalize_username


class ScanResult:
    """Single platform scan result."""
    
    def __init__(self, platform: str, url: str, exists: bool, 
                 response_time: float, status_code: Optional[int] = None,
                 error: Optional[str] = None):
        self.platform = platform
        self.url = url
        self.exists = exists
        self.response_time = response_time
        self.status_code = status_code
        self.error = error
    
    def to_dict(self) -> Dict:
        return {
            "platform": self.platform,
            "url": self.url,
            "exists": self.exists,
            "response_time": round(self.response_time, 3),
            "status_code": self.status_code,
            "error": self.error
        }


class ShenwinScanner:
    """
    Multi-threaded username scanner.
    """
    
    def __init__(self, threads: int = 50, timeout: int = 10,
                 proxy: Optional[str] = None, verbose: bool = False,
                 delay: float = 0.0):
        self.threads = threads
        self.timeout = timeout
        self.proxy = proxy
        self.verbose = verbose
        self.delay = delay  # Delay between requests to same domain
        self.platform_manager = PlatformManager()
        self._domain_last_request: Dict[str, float] = {}
        self._lock = threading.Lock()
    
    def _rate_limit(self, domain: str) -> None:
        """Basic rate limiting per domain."""
        if self.delay <= 0:
            return
        
        with self._lock:
            last = self._domain_last_request.get(domain, 0)
            elapsed = time.time() - last
            if elapsed < self.delay:
                time.sleep(self.delay - elapsed)
            self._domain_last_request[domain] = time.time()
    
    def _check_username(self, username: str, platform: str, 
                        platform_data: Dict) -> ScanResult:
        """
        Check single username on single platform.
        
        platform_data contains:
        - url: URL template with {username}
        - method: GET/POST
        - headers: custom headers
        - error_type: status_code / response_url / response_text
        - error_msg: what indicates "not found"
        - success_msg: what indicates "found" (optional)
        """
        start_time = time.time()
        normalized = normalize_username(username)
        url = platform_data["url"].format(username=normalized)
        
        try:
            domain = url.split("/")[2]
            self._rate_limit(domain)
            
            opener = create_opener(self.proxy, self.timeout)
            
            req = urllib.request.Request(
                url,
                headers=platform_data.get("headers", {}),
                method=platform_data.get("method", "GET")
            )
            
            response = opener.open(req, timeout=self.timeout)
            response_time = time.time() - start_time
            
            # Determine if account exists based on error_type
            error_type = platform_data.get("error_type", "status_code")
            
            if error_type == "status_code":
                # If we got here without exception, account likely exists
                # (some sites return 200 for both found/not found)
                exists = True
                
            elif error_type == "response_url":
                # Check if redirected to error URL
                final_url = response.geturl()
                error_url = platform_data.get("error_msg", "")
                exists = error_url not in final_url
                
            else:
                exists = True
            
            return ScanResult(
                platform=platform,
                url=url,
                exists=exists,
                response_time=response_time,
                status_code=response.getcode()
            )
            
        except urllib.error.HTTPError as e:
            response_time = time.time() - start_time
            
            # 404 usually means not found, but some sites use it differently
            error_msg = platform_data.get("error_msg", "")
            
            if e.code == 404:
                exists = False
            elif e.code == 403:
                # Rate limited or blocked
                exists = None  # Unknown
            else:
                # Other errors - check if this is the "not found" indicator
                exists = error_msg not in str(e)
            
            return ScanResult(
                platform=platform,
                url=url,
                exists=exists if exists is not None else False,
                response_time=response_time,
                status_code=e.code,
                error=str(e) if exists is None else None
            )
            
        except Exception as e:
            return ScanResult(
                platform=platform,
                url=url,
                exists=False,
                response_time=time.time() - start_time,
                error=str(e)
            )
    
    def scan(self, usernames: List[str], 
             platforms: Optional[List[str]] = None) -> Dict[str, Dict]:
        """
        Scan multiple usernames across platforms.
        
        Returns: {username: {platform: url, ...}, ...}
        """
        results: Dict[str, Dict] = {}
        platform_list = self.platform_manager.get_platforms(platforms)
        
        if self.verbose:
            total = len(usernames) * len(platform_list)
            print(f"[+] Scanning {len(usernames)} username(s) across {len(platform_list)} platforms ({total} total checks)")
        
        for username in usernames:
            results[username] = {}
            
            with ThreadPoolExecutor(max_workers=self.threads) as executor:
                future_to_platform = {
                    executor.submit(self._check_username, username, name, data): name
                    for name, data in platform_list.items()
                }
                
                for future in as_completed(future_to_platform):
                    platform_name = future_to_platform[future]
                    try:
                        result = future.result()
                        if result.exists:
                            results[username][platform_name] = result.url
                            if self.verbose:
                                print(f"    [FOUND] {platform_name}: {result.url}")
                    except Exception as e:
                        if self.verbose:
                            print(f"    [ERROR] {platform_name}: {e}")
        
        return results
    
    def scan_single(self, username: str, platform: str) -> Optional[ScanResult]:
        """Quick check single username on single platform."""
        platform_data = self.platform_manager.get_platform(platform)
        if not platform_data:
            return None
        return self._check_username(username, platform, platform_data)
