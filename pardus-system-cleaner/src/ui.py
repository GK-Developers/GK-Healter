import os
import gi
import threading
from typing import List, Dict, Any, Optional

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk

from src.cleaner import SystemCleaner
from src.history_manager import HistoryManager
from src.settings_manager import SettingsManager
import datetime

class MainWindow(Gtk.Window):
    """
    Main application window for the Pardus System Cleaner.
    Handles UI events, signal connections, and interacts with the SystemCleaner logic.
    """
    def __init__(self) -> None:
        """
        Initializes the MainWindow by loading the UI from XML and connecting signals.
        """
        # We don't call super() init here because we are loading from XML
        # Instead, we pull the window object from the builder.
        
        self.cleaner: SystemCleaner = SystemCleaner()
        self.history_manager: HistoryManager = HistoryManager()
        self.settings_manager: SettingsManager = SettingsManager()
        self.scan_data: List[Dict[str, Any]] = []
        self.current_cleaning_info: Dict[str, Any] = {}
        self.is_auto_maintenance_run: bool = False

        # Load XML
        builder = Gtk.Builder()
        ui_path = os.path.join(os.path.dirname(__file__), "../resources/main_window.ui")
        builder.add_from_file(ui_path)

        # Get Main Window
        self.window: Gtk.Window = builder.get_object("main_window")
        self.window.connect("destroy", Gtk.main_quit)
        
        # Get Objects
        self.info_bar: Gtk.InfoBar = builder.get_object("info_bar")
        self.info_label: Gtk.Label = builder.get_object("info_label")
        self.treeview: Gtk.TreeView = builder.get_object("treeview")
        self.store: Gtk.ListStore = builder.get_object("file_list_store")
        self.summary_label: Gtk.Label = builder.get_object("summary_label")
        self.btn_scan: Gtk.Button = builder.get_object("btn_scan")
        self.btn_clean: Gtk.Button = builder.get_object("btn_clean")
        self.btn_about: Gtk.Button = builder.get_object("btn_about")

        # History Objects
        self.history_treeview: Gtk.TreeView = builder.get_object("history_treeview")
        self.history_store: Gtk.ListStore = builder.get_object("history_list_store")
        self.notebook: Gtk.Notebook = builder.get_object("notebook")
        self.btn_settings: Gtk.Button = builder.get_object("btn_settings")

        # Settings Objects
        self.settings_dialog: Gtk.Dialog = builder.get_object("settings_dialog")
        self.switch_auto_maintenance: Gtk.Switch = builder.get_object("switch_auto_maintenance")
        self.lbl_last_maintenance: Gtk.Label = builder.get_object("lbl_last_maintenance")

        # Get Dialogs
        self.about_dialog: Gtk.AboutDialog = builder.get_object("about_dialog")
        self.clean_confirm_dialog: Gtk.MessageDialog = builder.get_object("clean_confirm_dialog")

        # Status Icon (programmatic addition to InfoBar)
        self.status_icon = Gtk.Image()
        info_content = self.info_bar.get_content_area()
        # Add icon at the start of the box
        info_content.pack_start(self.status_icon, False, False, 0)
        info_content.reorder_child(self.status_icon, 0)
        self.status_icon.show()

        # Connect Signals
        builder.connect_signals(self)
        
        # Initial History Load
        self.populate_history()

        # Load Settings UI
        self._sync_settings_ui()

        self.window.show_all()

        # Check for auto maintenance after a short delay
        GLib.timeout_add(1000, self.check_auto_maintenance)

    def _sync_settings_ui(self) -> None:
        """Syncs the settings dialog with values from SettingsManager."""
        self.switch_auto_maintenance.set_active(self.settings_manager.get("auto_maintenance_enabled"))
        last_date = self.settings_manager.get("last_maintenance_date")
        if last_date:
            self.lbl_last_maintenance.set_text(last_date)
        else:
            self.lbl_last_maintenance.set_text("Hiç yapılmadı")

    def check_auto_maintenance(self) -> bool:
        """Checks if auto-maintenance is due and prompts the user."""
        if self.settings_manager.is_maintenance_due():
            # Run a background scan for SAFE items only
            thread = threading.Thread(target=self.run_auto_scan_thread)
            thread.daemon = True
            thread.start()
        return False # Only run once

    def run_auto_scan_thread(self) -> None:
        """Background scan for safe maintenance items."""
        results = self.cleaner.scan()
        # Filter for SAFE items as per requirements
        safe_categories = [
            "Apt Önbelleği", 
            "Arşivlenmiş ve Sistem Günlükleri", 
            "Sistem Hata Dökümleri", 
            "Küçük Resim Önbelleği", 
            "Mozilla Önbelleği", 
            "Chrome Önbelleği"
        ]
        
        safe_items = [item for item in results if item['category'] in safe_categories]
        
        if safe_items:
            total_bytes = sum(item['size_bytes'] for item in safe_items)
            from src.utils import format_size
            total_freed_str = format_size(total_bytes)
            GLib.idle_add(self.show_auto_maintenance_prompt, safe_items, total_freed_str)

    def show_auto_maintenance_prompt(self, safe_items: List[Dict[str, Any]], total_freed_str: str) -> None:
        """Prompts user to perform automatic maintenance."""
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Güvenli Otomatik Bakım Zamanı"
        )
        dialog.format_secondary_text(
            f"Sisteminizde yaklaşık {total_freed_str} gereksiz dosya bulundu.\n\n"
            "Güvenli otomatik bakım yapılsın mı?\n"
            "(Sadece önbellek ve eski günlük dosyaları temizlenecektir.)"
        )
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            self.is_auto_maintenance_run = True
            self.info_label.set_text("Otomatik bakım yapılıyor...")
            # Reuse regular cleaning thread logic
            # We need to reconstruction current_cleaning_info
            categories = [item['category'] for item in safe_items]
            self.current_cleaning_info = {
                'categories': categories,
                'total_freed_str': total_freed_str,
                'is_auto': True
            }
            thread = threading.Thread(target=self.run_clean_thread, args=(safe_items,))
            thread.daemon = True
            thread.start()

    def on_settings_clicked(self, widget: Gtk.Button) -> None:
        self._sync_settings_ui()
        self.settings_dialog.show_all()

    def on_settings_close_clicked(self, widget: Gtk.Button) -> None:
        self.settings_dialog.hide()

    def on_auto_maintenance_toggled(self, switch: Gtk.Switch, gparam: Any) -> None:
        self.settings_manager.set("auto_maintenance_enabled", switch.get_active())

    def populate_history(self) -> None:
        """
        Loads cleaning history from the HistoryManager and populates the history treeview.
        """
        self.history_store.clear()
        entries = self.history_manager.get_all_entries()
        for entry in entries:
            self.history_store.append([
                entry.get("date", ""),
                entry.get("categories", ""),
                entry.get("total_freed", ""),
                entry.get("status", "")
            ])

    def on_cell_toggled(self, widget: Gtk.CellRendererToggle, path: str) -> None:
        """
        Callback for when a checkbox in the treeview is toggled.
        Updates the model and recalculates the summary.
        """
        self.store[path][0] = not self.store[path][0]
        self.update_summary()

    def update_summary(self) -> None:
        """
        Calculates the total size of selected items and updates the summary label.
        Controls the clean button sensitivity.
        """
        total_bytes = 0
        for row in self.store:
            if row[0]: # If checked
                total_bytes += row[4]
        
        mb = total_bytes / (1024 * 1024)
        self.summary_label.set_text(f"Toplam Kazanç: {mb:.2f} MB")
        self.btn_clean.set_sensitive(total_bytes > 0)

    def on_scan_clicked(self, widget: Gtk.Button) -> None:
        """
        Callback for the 'Scan' button. Initiates the system scan in a separate thread.
        """
        self.btn_scan.set_sensitive(False)
        self.store.clear()
        self.info_label.set_text("Sistem taranıyor, lütfen bekleyin...")
        self.info_bar.set_message_type(Gtk.MessageType.INFO)
        
        # Start scanning in a separate thread to keep UI responsive
        thread = threading.Thread(target=self.run_scan_thread)
        thread.daemon = True
        thread.start()

    def run_scan_thread(self) -> None:
        """
        Executed in a background thread. Performs the scan.
        """
        results = self.cleaner.scan()
        GLib.idle_add(self.on_scan_finished, results)

    def on_scan_finished(self, results: List[Dict[str, Any]]) -> None:
        """
        Callback invoked on the main thread when scanning is complete.
        Populates the treeview with results.
        """
        self.store.clear()
        for item in results:
            # Checkbox, Category, Desc, Size Str, Size Bytes, Path, System
            self.store.append([
                True, 
                item['category'], 
                item['desc'], 
                item['size_str'], 
                item['size_bytes'],
                item['path'],
                item['system']
            ])
        
        self.update_summary()
        self.btn_scan.set_sensitive(True)
        
        if not results:
            self.info_bar.set_message_type(Gtk.MessageType.WARNING)
            self.status_icon.set_from_icon_name("dialog-warning-symbolic", Gtk.IconSize.BUTTON)
            self.info_label.set_markup("<span weight='bold'>Temizlenecek öğe bulunamadı.</span>")
        else:
            self.info_bar.set_message_type(Gtk.MessageType.INFO)
            self.status_icon.set_from_icon_name("dialog-information-symbolic", Gtk.IconSize.BUTTON)
            self.info_label.set_markup("<span weight='bold'>Tarama tamamlandı.</span> Silinecek öğeleri seçin.")

    def on_clean_clicked(self, widget: Gtk.Button) -> None:
        """
        Callback for the 'Clean' button. Confirms action and starts cleaning.
        """
        to_clean = []
        for row in self.store:
            if row[0]: # Checked
                to_clean.append({
                    'path': row[5],
                    'system': row[6]
                })

        # Update dialog text
        self.clean_confirm_dialog.format_secondary_text(
            f"{len(to_clean)} kategori temizlenecek. Devam etmek istiyor musunuz?"
        )
        
        # Store current cleaning info for history logging
        categories = []
        total_bytes = 0
        for row in self.store:
            if row[0]:
                categories.append(row[1])
                total_bytes += row[4]
        
        from src.utils import format_size
        self.current_cleaning_info = {
            'categories': categories,
            'total_freed_str': format_size(total_bytes)
        }

        response = self.clean_confirm_dialog.run()
        self.clean_confirm_dialog.hide()
        
        if response == Gtk.ResponseType.OK:
            self.info_label.set_text("Temizleniyor...")
            # Threaded clean
            thread = threading.Thread(target=self.run_clean_thread, args=(to_clean,))
            thread.daemon = True
            thread.start()

    def run_clean_thread(self, to_clean: List[Dict[str, Any]]) -> None:
        """
        Executed in a background thread. Performs the cleaning operation.
        """
        success_count, fail_count, errors = self.cleaner.clean(to_clean)
        GLib.idle_add(self.on_clean_finished, success_count, fail_count, errors)

    def on_clean_finished(self, success_count: int, fail_count: int, errors: List[str]) -> None:
        """
        Callback invoked on the main thread when cleaning is complete.
        Refreshes the scan and shows errors if any.
        """
        self.on_scan_clicked(None) # Refresh
        
        if fail_count > 0:
            self.info_bar.set_message_type(Gtk.MessageType.ERROR)
            self.status_icon.set_from_icon_name("dialog-error-symbolic", Gtk.IconSize.BUTTON)
            error_text = "\n".join(errors)
            dialog = Gtk.MessageDialog(
                transient_for=self.window,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Bazı İşlemler Başarısız Oldu",
            )
            dialog.format_secondary_text(f"{fail_count} hata oluştu:\n\n{error_text}")
            dialog.run()
            dialog.destroy()
            self.info_label.set_markup(f"Temizlik tamamlandı ancak <span foreground='red'>{fail_count} hata</span> oluştu.")
            status = "Kısmi" if success_count > 0 else "Başarısız"
        else:
            self.info_bar.set_message_type(Gtk.MessageType.INFO)
            self.status_icon.set_from_icon_name("emblem-ok-symbolic", Gtk.IconSize.BUTTON)
            self.info_label.set_markup(f"<b>Sistem başarıyla temizlendi!</b> {success_count} işlem yapıldı.")
            status = "Başarılı"

        # Log to history
        if self.current_cleaning_info:
            is_auto = self.current_cleaning_info.get('is_auto', False)
            label_suffix = " (Otomatik bakım)" if is_auto else ""
            
            categories_str = ", ".join(self.current_cleaning_info['categories']) + label_suffix
            
            # Note: add_entry expects a list of categories normally, but let's check history_manager
            # Actually history_manager.py:add_entry(categories: List[str], ...) joins them.
            # I'll update it to handle the label properly or just pass the modified list.
            
            cats = list(self.current_cleaning_info['categories'])
            if is_auto:
                cats.append("Otomatik bakım")

            self.history_manager.add_entry(
                cats,
                self.current_cleaning_info['total_freed_str'],
                status
            )
            
            if is_auto:
                # Update last maintenance date
                now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.settings_manager.set("last_maintenance_date", now_str)
                self.is_auto_maintenance_run = False

            self.populate_history()
            self.current_cleaning_info = {}

    def on_about_clicked(self, widget: Gtk.Button) -> None:
        """
        Callback for the 'About' button. Shows the about dialog.
        """
        self.about_dialog.run()
        self.about_dialog.hide()

