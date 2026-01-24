import sys
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from src.ui import MainWindow

def main():
    app = MainWindow()
    # app.connect("destroy", Gtk.main_quit) # Handled inside MainWindow now
    Gtk.main()

if __name__ == "__main__":
    main()
