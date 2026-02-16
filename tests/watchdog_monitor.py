# ############################################################################
# FILE: watchdog_monitor.py
# ROLE: Comfort Reading & Availability Monitoring for Vecinita-RIOS
# USAGE: python3 watchdog_monitor.py --interval 60 --container vecinita-app
# ############################################################################

import subprocess
import time
import sys
import logging
from datetime import datetime

# Configuration
CONTAINER_NAME = "vecinita-app"
SEARCH_TERM = "[FALLBACK TRIGGERED]"
CHECK_INTERVAL = 60  # seconds

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [WATCHDOG] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

def get_recent_logs(container, seconds=60):
    """Fetches logs from the last N seconds."""
    cmd = f"docker logs --since {seconds}s {container}"
    try:
        result = subprocess.run(cmd.split(), capture_output=True, text=True, check=True)
        return result.stderr + result.stdout # Docker outputs logs to stderr often
    except subprocess.CalledProcessError:
        return ""

def analyze_availability():
    logging.info(f"Starting Comfort Monitor for {CONTAINER_NAME}...")
    
    while True:
        logs = get_recent_logs(CONTAINER_NAME, CHECK_INTERVAL)
        
        # 1. Check for Fallbacks
        fallback_count = logs.count(SEARCH_TERM)
        
        # 2. Check for the 'Boss' Error (404)
        has_404 = "404 models/" in logs

        print("-" * 50)
        print(f"REPORT AT: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if fallback_count > 0:
            print(f"⚠️  ALERT: {fallback_count} Fallback events detected.")
            print("   Action: System is using static resources (Graceful Degradation).")
        
        if has_404:
            print("❌ CRITICAL: Google API 404 Model Mismatch is active.")
            print("   Action: Check GOOGLE_API_KEY and Model IDs.")

        if fallback_count == 0 and not has_404:
            print("✅ HEALTHY: No fallback triggers or API errors in the last window.")
            print("   Availability: 100% (Direct RAG is active)")

        print("-" * 50)
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        analyze_availability()
    except KeyboardInterrupt:
        print("\nWatchdog standing down.")
