#!/usr/bin/env python3
"""
Claude "Absolutely Right" Backfill Script
Scans all historical Claude conversations and counts occurrences by date.
"""
import os
import json
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Configuration via environment or defaults
CLAUDE_PROJECTS_BASE = os.environ.get("CLAUDE_PROJECTS", os.path.expanduser("~/.claude/projects"))
PATTERN = os.environ.get("PATTERN", r"You(?:'re| are) absolutely right")
# For "You're right" without "absolutely"
PATTERN_RIGHT = os.environ.get("PATTERN_RIGHT", r"You(?:'re| are) right")

def upload_to_api(api_url, secret, date_str, count, right_count=None):
    """Upload counts to API"""
    try:
        data = {
            "day": date_str,
            "count": count
        }
        if secret:
            data["secret"] = secret
        if right_count is not None:
            data["right_count"] = right_count
            
        req = urllib.request.Request(
            f"{api_url}/api/set",
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                return True
            else:
                print(f"  API error for {date_str}: {response.status}")
    except Exception as e:
        print(f"  API error for {date_str}: {e}")
    return False

def scan_all_projects():
    """Scan all JSONL files and count by date"""
    pattern = re.compile(PATTERN, re.IGNORECASE)
    pattern_right = re.compile(PATTERN_RIGHT, re.IGNORECASE)
    
    daily_counts = defaultdict(int)
    daily_right_counts = defaultdict(int)
    total_messages = 0
    total_right_messages = 0
    project_breakdown = defaultdict(lambda: defaultdict(int))
    
    if not os.path.exists(CLAUDE_PROJECTS_BASE):
        print(f"Error: Projects directory not found at {CLAUDE_PROJECTS_BASE}")
        print("Set CLAUDE_PROJECTS env variable to your Claude projects path")
        return daily_counts, daily_right_counts, project_breakdown
    
    print("Scanning all Claude projects...")
    
    for project_dir in Path(CLAUDE_PROJECTS_BASE).iterdir():
        if project_dir.is_dir() and not project_dir.name.startswith('.'):
            # Clean up project name
            project_name = project_dir.name
            for prefix in ["-Users-", "-home-", "-var-"]:
                if project_name.startswith(prefix):
                    parts = project_name.split("-", 3)
                    if len(parts) > 3:
                        project_name = parts[3]
                    break
            
            for jsonl_file in project_dir.glob("*.jsonl"):
                try:
                    with open(jsonl_file, "r") as f:
                        for line in f:
                            try:
                                entry = json.loads(line)
                                
                                # Only check assistant messages
                                if entry.get("type") != "assistant":
                                    continue
                                
                                # Look for the pattern in message content
                                if "message" in entry:
                                    message = entry["message"]
                                    if "content" in message:
                                        for content_item in message.get("content", []):
                                            if isinstance(content_item, dict) and content_item.get("type") == "text":
                                                text = content_item.get("text", "")
                                                
                                                timestamp = entry.get("timestamp", "")
                                                if timestamp:
                                                    entry_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                                                    date_str = entry_time.strftime("%Y-%m-%d")
                                                else:
                                                    continue
                                                
                                                # Check "absolutely right"
                                                if pattern.search(text):
                                                    daily_counts[date_str] += 1
                                                    project_breakdown[date_str][project_name] += 1
                                                    total_messages += 1
                                                
                                                # Check "right" (including "absolutely right")
                                                if pattern_right.search(text):
                                                    daily_right_counts[date_str] += 1
                                                    total_right_messages += 1
                                                        
                            except json.JSONDecodeError:
                                continue
                            except Exception:
                                continue
                
                except Exception as e:
                    print(f"Error reading {jsonl_file}: {e}")
    
    print(f"Found {total_messages} 'absolutely right' across {len(daily_counts)} days")
    print(f"Found {total_right_messages} total 'right' across {len(daily_right_counts)} days")
    return daily_counts, daily_right_counts, project_breakdown

def main():
    """Main backfill process"""
    print("Claude 'Absolutely Right' Backfill")
    print("=" * 50)
    
    # Check for upload parameters
    api_url = None
    secret = None
    
    for i, arg in enumerate(sys.argv):
        if arg == "--upload" and i + 2 < len(sys.argv):
            api_url = sys.argv[i + 1]
            secret = sys.argv[i + 2]
            break
    
    # Show current settings
    print(f"Projects directory: {CLAUDE_PROJECTS_BASE}")
    print(f"Pattern: {PATTERN}")
    if api_url:
        print(f"Will upload to: {api_url}")
    print("-" * 50)
    
    # Scan all projects
    daily_counts, daily_right_counts, project_breakdown = scan_all_projects()
    
    if not daily_counts and not daily_right_counts:
        print("No data found.")
        return
    
    # Sort by date
    all_dates = set(daily_counts.keys()) | set(daily_right_counts.keys())
    sorted_dates = sorted(all_dates)
    
    print("\nDaily counts:")
    print("-" * 50)
    
    # Output format based on arguments
    if "--json" in sys.argv:
        # JSON output for piping to other tools
        output = {
            "total_absolutely": sum(daily_counts.values()),
            "total_right": sum(daily_right_counts.values()),
            "daily_absolutely": dict(daily_counts),
            "daily_right": dict(daily_right_counts),
            "by_date": {date: dict(project_breakdown[date]) for date in sorted_dates if date in project_breakdown}
        }
        print(json.dumps(output, indent=2))
    else:
        # Human-readable output
        for date in sorted_dates:
            abs_count = daily_counts.get(date, 0)
            right_count = daily_right_counts.get(date, 0)
            projects = project_breakdown.get(date, {})
            
            if len(projects) > 1:
                project_summary = ", ".join([f"{p}: {c}" for p, c in sorted(projects.items())])
                print(f"{date}: absolutely={abs_count:3d}, right={right_count:3d} ({project_summary})")
            else:
                print(f"{date}: absolutely={abs_count:3d}, right={right_count:3d}")
        
        print("-" * 50)
        print(f"Total 'absolutely right': {sum(daily_counts.values())}")
        print(f"Total 'right': {sum(daily_right_counts.values())}")
        
        # Upload to API if requested
        if api_url and secret:
            print("\n" + "-" * 50)
            print("Uploading to API...")
            success = 0
            failed = 0
            
            for date in sorted_dates:
                abs_count = daily_counts.get(date, 0)
                right_count = daily_right_counts.get(date, 0)
                
                # Only upload if there's data
                if abs_count > 0 or right_count > 0:
                    print(f"  Uploading {date}: absolutely={abs_count}, right={right_count}...", end=" ")
                    
                    if upload_to_api(api_url, secret, date, abs_count, right_count):
                        print("✓")
                        success += 1
                    else:
                        print("✗")
                        failed += 1
            
            print("-" * 50)
            print(f"Upload complete: {success} successful, {failed} failed")
            if success > 0:
                print(f"View at: {api_url}")
        
        # Save to local data directory
        data_dir = os.path.expanduser("~/.absolutelyright")
        os.makedirs(data_dir, exist_ok=True)
        
        daily_file = os.path.join(data_dir, "daily_counts.json")
        with open(daily_file, "w") as f:
            json.dump({
                "absolutely_right": dict(daily_counts),
                "right": dict(daily_right_counts)
            }, f, indent=2)
        
        print(f"\nSaved daily counts to: {daily_file}")

if __name__ == "__main__":
    main()