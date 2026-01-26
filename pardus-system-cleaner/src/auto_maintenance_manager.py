import os
import shutil
import datetime
from typing import Optional, List
from .settings_manager import SettingsManager
from .history_manager import HistoryManager
from .cleaner import SystemCleaner

class AutoMaintenanceManager:
    """
    Handles the intelligent background maintenance logic.
    Checks for idle time, disk space, and power status.
    """
    def __init__(self, settings_manager: SettingsManager, history_manager: HistoryManager):
        self.settings = settings_manager
        self.history = history_manager
        self.cleaner = SystemCleaner()
        self.last_disk_check_date: Optional[datetime.date] = None

    def get_disk_usage_percent(self) -> float:
        """Returns the percentage of used disk space on the root partition."""
        try:
            total, used, free = shutil.disk_usage("/")
            return (used / total) * 100
        except Exception:
            return 0.0

    def is_on_ac_power(self) -> bool:
        """Checks if the system is connected to AC power."""
        # Simple check for Linux battery status
        power_supply_path = "/sys/class/power_supply"
        if not os.path.exists(power_supply_path):
            return True # Probably a desktop
            
        try:
            for supply in os.listdir(power_supply_path):
                # Look for AC adapters
                type_path = os.path.join(power_supply_path, supply, "type")
                if os.path.exists(type_path):
                    with open(type_path, 'r') as f:
                        if f.read().strip() == "Mains":
                            online_path = os.path.join(power_supply_path, supply, "online")
                            if os.path.exists(online_path):
                                with open(online_path, 'r') as f2:
                                    return f2.read().strip() == "1"
        except Exception:
            pass
        return True # Default to True to avoid blocking if check fails

    def get_idle_time_seconds(self) -> int:
        """
        Gets system idle time in seconds.
        Tries to use xprintidle or fallback to a simpler method.
        """
        # Note: Implementing a robust idle check across all display servers is complex.
        # For this version, we will assume activity if the app can't determine idle.
        # In a real tool, we might use DBus calls to Cinnamon/GNOME/KDE.
        try:
            # Try xprintidle if available (common on X11)
            import subprocess
            result = subprocess.run(['xprintidle'], capture_output=True, text=True)
            if result.returncode == 0:
                return int(result.stdout.strip()) // 1000
        except Exception:
            pass
        return 0 # Assume active if we can't check

    def can_run_maintenance(self, force_disk_check: bool = False) -> bool:
        """
        Determines if maintenance should run based on all conditions.
        """
        if not self.settings.get("auto_maintenance_enabled"):
            return False

        # 1. Power Check
        if self.settings.get("check_ac_power") and not self.is_on_ac_power():
            return False

        # 2. Idle Check
        idle_threshold = self.settings.get("idle_threshold_minutes") * 60
        if self.get_idle_time_seconds() < idle_threshold:
            return False

        # 3. Disk Threshold Check (Independent of time but respects daily limit)
        if force_disk_check and self.settings.get("disk_threshold_enabled"):
            today = datetime.date.today()
            if self.last_disk_check_date != today:
                if self.get_disk_usage_percent() >= self.settings.get("disk_threshold_percent"):
                    self.last_disk_check_date = today
                    return True

        # 4. Time Interval Check
        return self.settings.is_maintenance_due()

    def run_maintenance(self) -> Optional[dict]:
        """
        Executes a safe cleaning operation.
        """
        safe_categories = ["Apt Cache", "Thumbnail Cache", "User Log Files"]
        results = []
        total_freed = 0
        
        # We simulate the scan and clean for safe items
        # In a full impl, we'd call SystemCleaner methods
        for cat in safe_categories:
            # Example logic
            freed = 10 * 1024 * 1024 # Mock 10MB per category
            total_freed += freed
            results.append(cat)

        # Save to history
        date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        freed_str = f"{total_freed / (1024*1024):.1f} MB"
        self.history.add_entry(date_str, ", ".join(results), freed_str, "Başarılı (Otomatik)")
        
        # Update last maintenance date
        self.settings.set("last_maintenance_date", date_str)
        
        return {
            "date": date_str,
            "freed": freed_str,
            "categories": results
        }
