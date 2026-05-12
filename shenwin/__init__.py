"""
Shenwin - Python OSINT username enumeration tool.
"""

__version__ = "1.0.0"
__author__ = "LaxenT"
__license__ = "MIT"

from .core import ShenwinScanner
from .variations import VariationEngine
from .exporters import JSONExporter, CSVExporter

__all__ = [
    "ShenwinScanner",
    "VariationEngine",
    "JSONExporter",
    "CSVExporter",
]


def main():
    """CLI entry point."""
    import argparse
    import sys
    from .core import ShenwinScanner
    from .exporters import JSONExporter, CSVExporter

    parser = argparse.ArgumentParser(
        description="Shenwin - Username enumeration across 500+ platforms",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  shenwin -w targetuser              Single username scan
  shenwin -w user -v                 With variations (leet, numbers, etc.)
  shenwin -w user -o results.json    JSON export
  shenwin -w user --threads 100      Custom thread count
        """
    )

    parser.add_argument("-w", "--username", required=True, help="Target username")
    parser.add_argument("-v", "--variations", action="store_true", help="Enable variation engine")
    parser.add_argument("-o", "--output", help="Output file (JSON or CSV)")
    parser.add_argument("-t", "--threads", type=int, default=50, help="Thread count (default: 50)")
    parser.add_argument("--timeout", type=int, default=10, help="Request timeout")
    parser.add_argument("--proxy", help="Proxy URL (http://host:port)")
    parser.add_argument("--platforms", nargs="+", help="Specific platforms only")
    parser.add_argument("--verbose", "-V", action="store_true", help="Verbose output")

    args = parser.parse_args()

    scanner = ShenwinScanner(
        threads=args.threads,
        timeout=args.timeout,
        proxy=args.proxy,
        verbose=args.verbose
    )

    usernames = [args.username]
    if args.variations:
        from .variations import VariationEngine
        engine = VariationEngine()
        usernames.extend(engine.generate(args.username))
        if args.verbose:
            print(f"[+] Generated {len(usernames)} variations")

    results = scanner.scan(usernames, platforms=args.platforms)

    if args.output:
        if args.output.endswith(".json"):
            JSONExporter.export(results, args.output)
        elif args.output.endswith(".csv"):
            CSVExporter.export(results, args.output)
        else:
            print("[-] Output format not recognized. Use .json or .csv", file=sys.stderr)
            sys.exit(1)
        print(f"[+] Results saved to {args.output}")
    else:
        for username, platforms in results.items():
            print(f"\n[+] Results for '{username}':")
            for platform, url in platforms.items():
                print(f"    [FOUND] {platform}: {url}")
