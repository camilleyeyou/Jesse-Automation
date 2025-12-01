#!/usr/bin/env python3
"""
Jesse A. Eisenbalm Automation CLI
Command-line tool for managing LinkedIn automation
"""

import os
import sys
import argparse
import asyncio
import requests
from pathlib import Path
from datetime import datetime

# Default API URL
API_BASE = os.getenv("API_BASE", "http://localhost:8001")


def print_box(title: str, content: str = None):
    """Print a formatted box"""
    width = 60
    print("\n" + "═" * width)
    print(f"  {title}")
    print("═" * width)
    if content:
        print(content)


def format_time(iso_str: str) -> str:
    """Format ISO timestamp for display"""
    if not iso_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return iso_str


def cmd_status(args):
    """Get automation status"""
    try:
        r = requests.get(f"{API_BASE}/api/automation/status", timeout=10)
        r.raise_for_status()
        data = r.json()
        
        scheduler = data.get("scheduler", {})
        queue = data.get("queue", {})
        linkedin = data.get("linkedin", {})
        
        print_box("📊 AUTOMATION STATUS")
        
        # Scheduler status
        running = "🟢 Running" if scheduler.get("running") else "🔴 Stopped"
        print(f"\n  Scheduler: {running}")
        
        schedule = scheduler.get("schedule", {})
        print(f"  Schedule:  {schedule.get('hour', 9):02d}:{schedule.get('minute', 0):02d} {schedule.get('timezone', 'America/New_York')}")
        
        next_run = scheduler.get("next_run")
        print(f"  Next Run:  {format_time(next_run)}")
        
        # Queue status
        print(f"\n  Queue:")
        print(f"    Pending:          {queue.get('pending', 0)}")
        print(f"    Published Today:  {queue.get('published_today', 0)}")
        print(f"    Published Week:   {queue.get('published_this_week', 0)}")
        
        # LinkedIn status
        configured = "✅ Yes" if linkedin.get("configured") else "❌ No"
        mock = " (MOCK)" if linkedin.get("mock") else ""
        print(f"\n  LinkedIn: {configured}{mock}")
        
        print()
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to API. Is the server running?")
        print(f"   Tried: {API_BASE}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def cmd_start(args):
    """Start the scheduler"""
    try:
        r = requests.post(f"{API_BASE}/api/automation/scheduler/start", timeout=10)
        r.raise_for_status()
        print("✅ Scheduler started")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def cmd_stop(args):
    """Stop the scheduler"""
    try:
        r = requests.post(f"{API_BASE}/api/automation/scheduler/stop", timeout=10)
        r.raise_for_status()
        print("✅ Scheduler stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def cmd_schedule(args):
    """Set or view schedule"""
    try:
        if args.hour is not None:
            # Set schedule
            payload = {
                "hour": args.hour,
                "minute": args.minute or 0,
                "timezone": args.timezone or "America/New_York",
                "enabled": True
            }
            r = requests.post(f"{API_BASE}/api/automation/schedule", json=payload, timeout=10)
            r.raise_for_status()
            data = r.json()
            print(f"✅ Schedule set: {args.hour:02d}:{args.minute or 0:02d} {args.timezone or 'America/New_York'}")
            print(f"   Next run: {format_time(data.get('next_run'))}")
        else:
            # View schedule
            r = requests.get(f"{API_BASE}/api/automation/schedule", timeout=10)
            r.raise_for_status()
            data = r.json()
            
            print_box("📅 SCHEDULE")
            print(f"\n  Time:     {data['hour']:02d}:{data['minute']:02d}")
            print(f"  Timezone: {data['timezone']}")
            print(f"  Enabled:  {'Yes' if data['enabled'] else 'No'}")
            print(f"  Next Run: {format_time(data.get('next_run'))}")
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def cmd_post(args):
    """Trigger immediate post"""
    try:
        r = requests.post(f"{API_BASE}/api/automation/post-now", timeout=10)
        r.raise_for_status()
        print("✅ Post triggered! Check status for results.")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def cmd_generate(args):
    """Generate new content"""
    try:
        print("🔄 Generating content...")
        payload = {
            "num_posts": args.count or 1,
            "add_to_queue": not args.no_queue
        }
        r = requests.post(f"{API_BASE}/api/automation/generate-content", json=payload, timeout=120)
        r.raise_for_status()
        data = r.json()
        
        print_box("✨ CONTENT GENERATED")
        print(f"\n  Total:    {data['total_posts']}")
        print(f"  Approved: {data['approved_posts']}")
        print(f"  Queued:   {data['added_to_queue']}")
        
        # Show posts
        for post in data.get("posts", []):
            status = "✅" if post["status"] == "approved" else "❌"
            score = post.get("average_score", 0)
            print(f"\n  {status} Post (Score: {score:.1f}/10)")
            print(f"     {post['content'][:80]}...")
            if post.get("image_url"):
                print(f"     📷 Image: {post['image_url']}")
        
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def cmd_queue(args):
    """View queue"""
    try:
        r = requests.get(f"{API_BASE}/api/automation/queue", params={"limit": args.limit or 10}, timeout=10)
        r.raise_for_status()
        data = r.json()
        
        stats = data.get("stats", {})
        posts = data.get("posts", [])
        
        print_box("📬 POST QUEUE")
        print(f"\n  Pending: {stats.get('pending', 0)} | Failed: {stats.get('failed', 0)}")
        
        if posts:
            for i, post in enumerate(posts[:10], 1):
                status = {"pending": "⏳", "publishing": "🔄", "failed": "❌"}.get(post.get("status"), "?")
                content = post.get("content", "")[:60]
                print(f"\n  {i}. {status} {content}...")
                if post.get("image_url"):
                    print(f"     📷 Has image")
        else:
            print("\n  Queue is empty")
        
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def cmd_history(args):
    """View published history"""
    try:
        r = requests.get(f"{API_BASE}/api/automation/history", params={"limit": args.limit or 10}, timeout=10)
        r.raise_for_status()
        data = r.json()
        
        posts = data.get("posts", [])
        
        print_box("📜 PUBLISHED HISTORY")
        
        if posts:
            for post in posts[:10]:
                status = "✅" if post.get("status") == "success" else "❌"
                time = format_time(post.get("published_at"))
                content = post.get("content", "")[:50]
                print(f"\n  {status} {time}")
                print(f"     {content}...")
                if post.get("linkedin_post_id"):
                    print(f"     🔗 {post['linkedin_post_id']}")
        else:
            print("\n  No published posts yet")
        
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def cmd_linkedin(args):
    """Check LinkedIn status"""
    try:
        r = requests.get(f"{API_BASE}/api/automation/linkedin/status", timeout=10)
        r.raise_for_status()
        data = r.json()
        
        print_box("🔗 LINKEDIN STATUS")
        
        configured = "✅ Yes" if data.get("configured") else "❌ No"
        mock = " (MOCK MODE)" if data.get("mock") else ""
        print(f"\n  Configured: {configured}{mock}")
        
        if args.test:
            print("  Testing connection...")
            r = requests.post(f"{API_BASE}/api/automation/linkedin/test", timeout=15)
            test_data = r.json()
            
            if test_data.get("success"):
                print(f"  ✅ Connected as: {test_data.get('name', 'Unknown')}")
            else:
                print(f"  ❌ Connection failed: {test_data.get('error', 'Unknown error')}")
        
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Jesse A. Eisenbalm LinkedIn Automation CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python automation.py status              # View full status
  python automation.py schedule --hour 9   # Set daily post at 9 AM
  python automation.py start               # Start scheduler
  python automation.py generate            # Generate new content
  python automation.py post                # Post immediately
  python automation.py queue               # View queue
  python automation.py history             # View published posts
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Status command
    subparsers.add_parser("status", help="Get automation status")
    
    # Start command
    subparsers.add_parser("start", help="Start the scheduler")
    
    # Stop command
    subparsers.add_parser("stop", help="Stop the scheduler")
    
    # Schedule command
    schedule_parser = subparsers.add_parser("schedule", help="Set or view schedule")
    schedule_parser.add_argument("--hour", type=int, help="Hour (0-23)")
    schedule_parser.add_argument("--minute", type=int, default=0, help="Minute (0-59)")
    schedule_parser.add_argument("--timezone", default="America/New_York", help="Timezone")
    
    # Post command
    subparsers.add_parser("post", help="Trigger immediate post")
    
    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate new content")
    gen_parser.add_argument("--count", "-n", type=int, default=1, help="Number of posts")
    gen_parser.add_argument("--no-queue", action="store_true", help="Don't add to queue")
    
    # Queue command
    queue_parser = subparsers.add_parser("queue", help="View queue")
    queue_parser.add_argument("--limit", "-l", type=int, default=10, help="Number of posts to show")
    
    # History command
    history_parser = subparsers.add_parser("history", help="View published history")
    history_parser.add_argument("--limit", "-l", type=int, default=10, help="Number of posts to show")
    
    # LinkedIn command
    linkedin_parser = subparsers.add_parser("linkedin", help="Check LinkedIn status")
    linkedin_parser.add_argument("--test", "-t", action="store_true", help="Test connection")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # Route to command handler
    commands = {
        "status": cmd_status,
        "start": cmd_start,
        "stop": cmd_stop,
        "schedule": cmd_schedule,
        "post": cmd_post,
        "generate": cmd_generate,
        "queue": cmd_queue,
        "history": cmd_history,
        "linkedin": cmd_linkedin,
    }
    
    handler = commands.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
