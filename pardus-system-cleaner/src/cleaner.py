import os
import shutil
import subprocess
from src.utils import get_size, format_size
from typing import List, Dict, Any, Tuple

class SystemCleaner:
    def __init__(self):
        self.scan_results = []
        # Categories to scan
        # (Name, Path, IsSystem, Description)
        self.categories = [
            ("Apt Önbelleği", "/var/cache/apt/archives", True, "İndirilmiş paket dosyaları"),
            ("Eskimiş Loglar", "/var/log", True, "Sistem günlük dosyaları (eski)"),
            ("Küçük Resim Önbelleği", os.path.expanduser("~/.cache/thumbnails"), False, "Dosya yöneticisi önizlemeleri"),
            ("Mozilla Önbelleği", os.path.expanduser("~/.cache/mozilla"), False, "Firefox tarayıcı önbelleği"),
            ("Chrome Önbelleği", os.path.expanduser("~/.cache/google-chrome"), False, "Chrome tarayıcı önbelleği")
        ]

    def scan(self) -> List[Dict[str, Any]]:
        """
        Scans the defined categories and returns a list of dictionaries:
        {'category': str, 'path': str, 'size_str': str, 'size_bytes': int, 'system': bool, 'desc': str}
        """
        results = []
        for name, path, is_system, desc in self.categories:
            if os.path.exists(path):
                size_bytes = get_size(path)
                # Only offer to clean if size > 0 (or some threshold) to reduce noise
                if size_bytes > 0:
                    results.append({
                        'category': name,
                        'path': path,
                        'size_str': format_size(size_bytes),
                        'size_bytes': size_bytes,
                        'system': is_system,
                        'desc': desc
                    })
        self.scan_results = results
        return results

    def is_safe_to_delete(self, path: str) -> bool:
        """
        Safety check: ensure we are not deleting critical system paths.
        This acts as a whitelist mechanism.
        """
        # Forbidden paths (prefixes)
        forbidden = ["/bin", "/boot", "/dev", "/etc", "/lib", "/proc", "/sys", "/usr/bin", "/usr/lib", "/usr/sbin"]
        
        # Explicitly allowed prefixes for System cleaning
        allowed_system = ["/var/cache/apt/archives", "/var/log"]
        
        # Explicitly allowed prefixes for User cleaning
        allowed_user = [os.path.expanduser("~/.cache")]

        path = os.path.abspath(path)

        # 1. Check strict forbidden list
        for f in forbidden:
            if path.startswith(f):
                return False
        
        # 2. Check if it matches an allowed category prefix
        is_allowed = False
        for a in allowed_system + allowed_user:
            if path.startswith(a):
                is_allowed = True
                break
        
        return is_allowed

    def clean(self, selected_items: List[Dict[str, Any]]) -> Tuple[int, int, List[str]]:
        """
        Performs actual cleaning.
        Returns: (success_count, fail_count, list_of_error_messages)
        """
        success_count = 0
        fail_count = 0
        errors = []

        for item in selected_items:
            path = item['path']
            is_system = item['system']

            if not self.is_safe_to_delete(path):
                msg = f"GÜVENLİK UYARISI: {path} silinemez (izin verilmeyen yol)."
                print(msg)
                errors.append(msg)
                fail_count += 1
                continue

            success = False
            error_msg = None

            if is_system:
                success, error_msg = self._clean_system(path)
            else:
                success, error_msg = self._clean_user(path)

            if success:
                success_count += 1
            else:
                fail_count += 1
                if error_msg:
                    errors.append(error_msg)
                    
        return success_count, fail_count, errors

    def _clean_user(self, path: str) -> Tuple[bool, str]:
        """
        Cleans user paths. Returns (Bool Success, String ErrorMsg).
        """
        try:
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    for f in files:
                        try:
                            os.remove(os.path.join(root, f))
                        except Exception as e:
                            return False, f"Dosya silinemedi {f}: {e}"
            return True, None
        except Exception as e:
            msg = f"Kullanıcı temizliği başarısız ({path}): {e}"
            print(msg)
            return False, msg

    def _clean_system(self, path: str) -> Tuple[bool, str]:
        """
        Uses pkexec to clean system paths. Returns (Bool Success, String ErrorMsg).
        """
        cmd = []
        
        if path == "/var/cache/apt/archives":
            cmd = ["pkexec", "apt-get", "clean"]
        elif path == "/var/log":
            bash_cmd = "find /var/log -type f -regex '.*\\.\\(gz\\|[0-9]+\\)$' -delete"
            cmd = ["pkexec", "sh", "-c", bash_cmd]
        else:
            return False, f"Bilinmeyen sistem yolu: {path}"

        try:
            print(f"Executing system clean: {cmd}")
            subprocess.run(cmd, check=True)
            return True, None
        except subprocess.CalledProcessError as e:
            # e.returncode 126 or 127 or 1 usually means auth failed or cancelled
            if e.returncode in [126, 127]:
                return False, f"Yetkilendirme iptal edildi veya reddedildi: {path}"
            return False, f"Sistem temizliği hata kodu {e.returncode}: {path}"
        except Exception as e:
            return False, f"Beklenmeyen hata ({path}): {e}"



