#!/usr/bin/env python3
"""
Claude "Absolutely Right" Watcher
Monitors Claude conversation logs and tracks when Claude agrees with you.
"""
import os
import json
import time
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

# Configuration via environment or defaults
CLAUDE_PROJECTS_BASE = os.environ.get("CLAUDE_PROJECTS", os.path.expanduser("~/.claude/projects"))
PATTERN = os.environ.get("PATTERN", r"You(?:'re| are) absolutely right")
PATTERN_RIGHT = os.environ.get("PATTERN_RIGHT", r"You(?:'re| are) right")
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", "2"))

# Data files
DATA_DIR = os.path.expanduser("~/.absolutelyright")
COUNTER_FILE = os.path.join(DATA_DIR, "total_count.txt")
PROJECT_COUNTS_FILE = os.path.join(DATA_DIR, "project_counts.json")
DAILY_COUNTS_FILE = os.path.join(DATA_DIR, "daily_counts.json")
DAILY_RIGHT_COUNTS_FILE = os.path.join(DATA_DIR, "daily_right_counts.json")
PROCESSED_IDS_FILE = os.path.join(DATA_DIR, "processed_ids.json")

def ensure_data_dir():
    """Ensure data directory exists"""
    os.makedirs(DATA_DIR, exist_ok=True)

def load_processed_ids():
    """Load set of already processed message IDs"""
    if os.path.exists(PROCESSED_IDS_FILE):
        try:
            with open(PROCESSED_IDS_FILE, "r") as f:
                return set(json.load(f))
        except:
            pass
    return set()

def save_processed_ids(ids_set):
    """Save processed message IDs"""
    with open(PROCESSED_IDS_FILE, "w") as f:
        json.dump(list(ids_set), f)

def load_project_counts():
    """Load per-project counts"""
    if os.path.exists(PROJECT_COUNTS_FILE):
        try:
            with open(PROJECT_COUNTS_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_project_counts(counts):
    """Save per-project counts"""
    with open(PROJECT_COUNTS_FILE, "w") as f:
        json.dump(counts, f, indent=2)

def load_daily_counts():
    """Load daily counts"""
    if os.path.exists(DAILY_COUNTS_FILE):
        try:
            with open(DAILY_COUNTS_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_daily_counts(counts):
    """Save daily counts"""
    with open(DAILY_COUNTS_FILE, "w") as f:
        json.dump(counts, f, indent=2)

def load_daily_right_counts():
    """Load daily right counts"""
    if os.path.exists(DAILY_RIGHT_COUNTS_FILE):
        try:
            with open(DAILY_RIGHT_COUNTS_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_daily_right_counts(counts):
    """Save daily right counts"""
    with open(DAILY_RIGHT_COUNTS_FILE, "w") as f:
        json.dump(counts, f, indent=2)

def upload_to_api(api_url, secret, date_str, count, right_count=None):
    """Upload counts to API"""
    if not api_url:
        return False
        
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

def get_counter():
    """Get current total counter value"""
    if os.path.exists(COUNTER_FILE):
        try:
            with open(COUNTER_FILE, "r") as f:
                return int(f.read().strip() or 0)
        except:
            pass
    return 0

def set_counter(value):
    """Set total counter value"""
    with open(COUNTER_FILE, "w") as f:
        f.write(str(value))

def scan_jsonl_file(filepath, processed_ids, project_name, pattern, pattern_right):
    """Scan a JSONL file for new matches"""
    new_matches = []
    
    try:
        with open(filepath, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    
                    # Only check assistant messages
                    if entry.get("type") != "assistant":
                        continue
                    
                    # Get unique ID for this message
                    msg_id = entry.get("uuid") or entry.get("requestId")
                    if not msg_id or msg_id in processed_ids:
                        continue
                    
                    # Look for the pattern in message content
                    if "message" in entry:
                        message = entry["message"]
                        if "content" in message:
                            for content_item in message.get("content", []):
                                if isinstance(content_item, dict) and content_item.get("type") == "text":
                                    text = content_item.get("text", "")
                                    
                                    # Get timestamp first
                                    timestamp = entry.get("timestamp", "")
                                    if timestamp:
                                        entry_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                                        time_str = entry_time.strftime("%H:%M:%S")
                                        date_str = entry_time.strftime("%Y-%m-%d")
                                    else:
                                        time_str = "unknown"
                                        date_str = datetime.now().strftime("%Y-%m-%d")
                                    
                                    # Check both patterns
                                    is_absolutely = pattern.search(text)
                                    is_right = pattern_right.search(text)
                                    
                                    if is_absolutely or is_right:
                                        new_matches.append({
                                            "id": msg_id,
                                            "time": time_str,
                                            "date": date_str,
                                            "text": text.strip()[:100],
                                            "project": project_name,
                                            "is_absolutely": bool(is_absolutely),
                                            "is_right": bool(is_right)
                                        })
                                        
                except json.JSONDecodeError:
                    continue
                except Exception:
                    continue
    
    except Exception:
        pass
    
    return new_matches

def get_project_display_name(project_dir_name):
    """Convert project directory name to display name"""
    # Remove common prefixes for cleaner display
    name = project_dir_name
    for prefix in ["-Users-", "-home-", "-var-"]:
        if name.startswith(prefix):
            # Find the second dash to skip username
            parts = name.split("-", 3)
            if len(parts) > 3:
                name = parts[3]
            break
    return name

def main():
    """Main watcher loop"""
    ensure_data_dir()
    
    # Check for upload parameters from command line
    api_url = None
    api_secret = None
    
    for i, arg in enumerate(sys.argv):
        if arg == "--upload" and i + 1 < len(sys.argv):
            api_url = sys.argv[i + 1]
            if i + 2 < len(sys.argv) and not sys.argv[i + 2].startswith("--"):
                api_secret = sys.argv[i + 2]
            break
    
    print("Claude 'Absolutely Right' Watcher")
    print("=" * 50)
    print(f"Watching: {CLAUDE_PROJECTS_BASE}")
    print(f"Data directory: {DATA_DIR}")
    print(f"Patterns: absolutely right, right")
    if api_url:
        print(f"API URL: {api_url}")
    print("-" * 50)
    
    # Compile patterns
    pattern = re.compile(PATTERN, re.IGNORECASE)
    pattern_right = re.compile(PATTERN_RIGHT, re.IGNORECASE)
    
    # Initialize
    processed_ids = load_processed_ids()
    project_counts = load_project_counts()
    daily_counts = load_daily_counts()
    daily_right_counts = load_daily_right_counts()
    total_counter = get_counter()
    
    print(f"Current total count: {total_counter}")
    if project_counts:
        print("Per-project counts:")
        for project, count in sorted(project_counts.items()):
            print(f"  {project}: {count}")
    
    # Upload today's data on startup if API is configured
    if api_url:
        today = datetime.now().strftime("%Y-%m-%d")
        today_count = daily_counts.get(today, 0)
        today_right_count = daily_right_counts.get(today, 0)
        print(f"Uploading today's counts: absolutely={today_count}, right={today_right_count}")
        if upload_to_api(api_url, api_secret, today, today_count, today_right_count):
            print("  ✓ Upload successful")
        else:
            print("  ✗ Upload failed")
    
    print("-" * 50)
    
    if not os.path.exists(CLAUDE_PROJECTS_BASE):
        print(f"Error: Claude projects directory not found at {CLAUDE_PROJECTS_BASE}")
        print("Set CLAUDE_PROJECTS environment variable to your Claude projects path")
        return
    
    try:
        while True:
            # Check all project directories
            new_absolutely_matches = 0
            new_right_matches = 0
            
            for project_dir in Path(CLAUDE_PROJECTS_BASE).iterdir():
                if project_dir.is_dir() and not project_dir.name.startswith('.'):
                    project_name = get_project_display_name(project_dir.name)
                    
                    # Scan all JSONL files in this project
                    for jsonl_file in project_dir.glob("*.jsonl"):
                        matches = scan_jsonl_file(jsonl_file, processed_ids, project_name, pattern, pattern_right)
                        
                        for match in matches:
                            # Add to processed IDs
                            processed_ids.add(match["id"])
                            
                            # Update counts based on match type
                            date_str = match["date"]
                            
                            if match["is_absolutely"]:
                                new_absolutely_matches += 1
                                if project_name not in project_counts:
                                    project_counts[project_name] = 0
                                project_counts[project_name] += 1
                                
                                if date_str not in daily_counts:
                                    daily_counts[date_str] = 0
                                daily_counts[date_str] += 1
                            
                            if match["is_right"]:
                                new_right_matches += 1
                                if date_str not in daily_right_counts:
                                    daily_right_counts[date_str] = 0
                                daily_right_counts[date_str] += 1
                            
                            # Print notification
                            match_type = "ABSOLUTELY RIGHT" if match["is_absolutely"] else "RIGHT"
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] {match_type} in {project_name}: {match['text']}")
            
            if new_absolutely_matches > 0 or new_right_matches > 0:
                # Update total counter (only for absolutely right)
                if new_absolutely_matches > 0:
                    total_counter += new_absolutely_matches
                    set_counter(total_counter)
                
                # Save all state
                save_project_counts(project_counts)
                save_processed_ids(processed_ids)
                save_daily_counts(daily_counts)
                save_daily_right_counts(daily_right_counts)
                
                print(f"Updated: absolutely +{new_absolutely_matches} (total: {total_counter}), right +{new_right_matches}")
                
                # Upload to API if configured
                if api_url:
                    today = datetime.now().strftime("%Y-%m-%d")
                    today_count = daily_counts.get(today, 0)
                    today_right_count = daily_right_counts.get(today, 0)
                    if upload_to_api(api_url, api_secret, today, today_count, today_right_count):
                        print(f"  ✓ Uploaded to API: absolutely={today_count}, right={today_right_count}")
            
            time.sleep(CHECK_INTERVAL)
    
    except KeyboardInterrupt:
        print("\n" + "-" * 50)
        print("Stopping watcher...")
        print(f"Final total count: {total_counter}")
        if project_counts:
            print("Final per-project counts:")
            for project, count in sorted(project_counts.items()):
                print(f"  {project}: {count}")

if __name__ == "__main__":
    main()