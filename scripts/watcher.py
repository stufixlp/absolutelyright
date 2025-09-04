#!/usr/bin/env python3
"""
Claude "Absolutely Right" Watcher
Monitors Claude conversation logs and tracks when Claude agrees with you.
"""
import os
import json
import time
import re
from datetime import datetime
from pathlib import Path

# Configuration
CONFIG_FILE = os.path.expanduser("~/.absolutelyright_config.json")

# Default configuration
DEFAULT_CONFIG = {
    "claude_projects_base": os.path.expanduser("~/.claude/projects"),
    "check_interval": 2,
    "pattern": r"You(?:'re| are) absolutely right"
}

# Data files
DATA_DIR = os.path.expanduser("~/.absolutelyright")
COUNTER_FILE = os.path.join(DATA_DIR, "total_count.txt")
PROJECT_COUNTS_FILE = os.path.join(DATA_DIR, "project_counts.json")
DAILY_COUNTS_FILE = os.path.join(DATA_DIR, "daily_counts.json")
PROCESSED_IDS_FILE = os.path.join(DATA_DIR, "processed_ids.json")

def load_config():
    """Load configuration from file or use defaults"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                # Merge with defaults for any missing keys
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception as e:
            print(f"Error loading config: {e}")
    return DEFAULT_CONFIG.copy()

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

def scan_jsonl_file(filepath, processed_ids, project_name, pattern):
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
                                    if pattern.search(text):
                                        timestamp = entry.get("timestamp", "")
                                        if timestamp:
                                            entry_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                                            time_str = entry_time.strftime("%H:%M:%S")
                                            date_str = entry_time.strftime("%Y-%m-%d")
                                        else:
                                            time_str = "unknown"
                                            date_str = datetime.now().strftime("%Y-%m-%d")
                                        
                                        new_matches.append({
                                            "id": msg_id,
                                            "time": time_str,
                                            "date": date_str,
                                            "text": text.strip()[:100],
                                            "project": project_name
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
    # Load configuration
    config = load_config()
    ensure_data_dir()
    
    print("Claude 'Absolutely Right' Watcher")
    print("=" * 50)
    print(f"Watching: {config['claude_projects_base']}")
    print(f"Data directory: {DATA_DIR}")
    print(f"Pattern: {config['pattern']}")
    print("-" * 50)
    
    # Compile pattern
    pattern = re.compile(config["pattern"], re.IGNORECASE)
    
    # Initialize
    processed_ids = load_processed_ids()
    project_counts = load_project_counts()
    daily_counts = load_daily_counts()
    total_counter = get_counter()
    
    print(f"Current total count: {total_counter}")
    if project_counts:
        print("Per-project counts:")
        for project, count in sorted(project_counts.items()):
            print(f"  {project}: {count}")
    print("-" * 50)
    
    if not os.path.exists(config["claude_projects_base"]):
        print(f"Error: Claude projects directory not found at {config['claude_projects_base']}")
        print("Create a config file at ~/.absolutelyright_config.json with the correct path.")
        return
    
    try:
        while True:
            # Check all project directories
            new_total_matches = 0
            
            for project_dir in Path(config["claude_projects_base"]).iterdir():
                if project_dir.is_dir() and not project_dir.name.startswith('.'):
                    project_name = get_project_display_name(project_dir.name)
                    
                    # Scan all JSONL files in this project
                    for jsonl_file in project_dir.glob("*.jsonl"):
                        matches = scan_jsonl_file(jsonl_file, processed_ids, project_name, pattern)
                        
                        for match in matches:
                            # Add to processed IDs
                            processed_ids.add(match["id"])
                            
                            # Update counts
                            new_total_matches += 1
                            if project_name not in project_counts:
                                project_counts[project_name] = 0
                            project_counts[project_name] += 1
                            
                            # Update daily count
                            date_str = match["date"]
                            if date_str not in daily_counts:
                                daily_counts[date_str] = 0
                            daily_counts[date_str] += 1
                            
                            # Print notification
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] NEW in {project_name}: {match['text']}")
            
            if new_total_matches > 0:
                # Update total counter
                total_counter += new_total_matches
                set_counter(total_counter)
                
                # Save all state
                save_project_counts(project_counts)
                save_processed_ids(processed_ids)
                save_daily_counts(daily_counts)
                
                print(f"Updated total count: {total_counter} (+{new_total_matches})")
            
            time.sleep(config["check_interval"])
    
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