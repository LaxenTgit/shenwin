"""
Result exporters for Shenwin.
"""

import json
import csv
import os
from typing import Dict, List
from datetime import datetime


class JSONExporter:
    """Export results to JSON format."""
    
    @staticmethod
    def export(results: Dict[str, Dict], filepath: str, 
               metadata: Dict = None) -> None:
        """
        Export scan results to JSON.
        
        Args:
            results: {username: {platform: url, ...}, ...}
            filepath: Output file path
            metadata: Optional additional metadata
        """
        output = {
            "tool": "shenwin",
            "version": "1.0.0",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "summary": {
                "total_usernames": len(results),
                "total_findings": sum(len(p) for p in results.values())
            },
            "results": {}
        }
        
        if metadata:
            output["metadata"] = metadata
        
        for username, platforms in results.items():
            output["results"][username] = {
                "findings_count": len(platforms),
                "platforms": [
                    {
                        "name": platform,
                        "url": url,
                        "category": _guess_category(platform)
                    }
                    for platform, url in platforms.items()
                ]
            }
        
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def export_raw(results: Dict[str, Dict], filepath: str) -> None:
        """Export raw results without wrapping."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)


class CSVExporter:
    """Export results to CSV format."""
    
    @staticmethod
    def export(results: Dict[str, Dict], filepath: str) -> None:
        """
        Export to CSV with columns: username, platform, url, category
        """
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["username", "platform", "url", "category", "found_at"])
            
            found_at = datetime.utcnow().isoformat() + "Z"
            
            for username, platforms in results.items():
                for platform, url in platforms.items():
                    writer.writerow([
                        username,
                        platform,
                        url,
                        _guess_category(platform),
                        found_at
                    ])
    
    @staticmethod
    def export_summary(results: Dict[str, Dict], filepath: str) -> None:
        """Export summary only (one row per username)."""
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["username", "platforms_found", "urls"])
            
            for username, platforms in results.items():
                writer.writerow([
                    username,
                    len(platforms),
                    "; ".join(platforms.values())
                ])


def _guess_category(platform: str) -> str:
    """Guess platform category from name."""
    categories = {
        "github": "development", "gitlab": "development", "bitbucket": "development",
        "twitter": "social", "instagram": "social", "facebook": "social",
        "reddit": "forum", "stackoverflow": "forum",
        "twitch": "gaming", "steam": "gaming",
        "youtube": "video", "vimeo": "video",
        "medium": "blogging", "wordpress": "blogging",
    }
    return categories.get(platform.lower(), "unknown")


class HTMLExporter:
    """Optional: Generate nice HTML report."""
    
    @staticmethod
    def export(results: Dict[str, Dict], filepath: str) -> None:
        """Generate styled HTML report."""
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Shenwin Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #1a1a2e; color: #eee; }
        h1 { color: #e94560; }
        .username { background: #16213e; padding: 20px; margin: 20px 0; border-radius: 8px; }
        .platform { display: inline-block; margin: 5px; padding: 8px 12px; background: #0f3460; 
                    border-radius: 4px; text-decoration: none; color: #eee; }
        .platform:hover { background: #e94560; }
        .stats { color: #aaa; margin-bottom: 20px; }
    </style>
</head>
<body>
    <h1>🐰 Shenwin OSINT Report</h1>
    <div class="stats">Generated: {date}</div>
"""
        
        for username, platforms in results.items():
            html += f'    <div class="username">\n'
            html += f'        <h2>@{username}</h2>\n'
            html += f'        <p>Found on {len(platforms)} platform(s)</p>\n'
            for platform, url in platforms.items():
                html += f'        <a href="{url}" class="platform" target="_blank">{platform}</a>\n'
            html += '    </div>\n'
        
        html += """</body>
</html>"""
        
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html.format(date=datetime.utcnow().isoformat()))
