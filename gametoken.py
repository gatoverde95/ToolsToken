#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import subprocess
import threading
import os
import json
import locale
from translations import get_translation, get_available_translations

class GameTokenApp:
    def __init__(self):
        self.is_processing = False
        self.current_process = None
        self.progress_timeout_id = None
        self.config_dir = os.path.expanduser("~/.config/gametoken")
        self.config_file = os.path.join(self.config_dir, "config.json")
        self.load_config()
        
        # Configure translation
        self._ = get_translation(self.config.get('language'))
        
        # Define packages
        self.emulators = [
            {'name': 'melonDS', 'package': 'melonDS', 'desc': self._('Nintendo DS Emulator'), 'icon': '🎮'},
            {'name': 'DuckStation', 'package': 'duckstation', 'desc': self._('PlayStation 1 Emulator'), 'icon': '🎮'},
            {'name': 'PPSSPP', 'package': 'ppsspp', 'desc': self._('PSP Emulator'), 'icon': '🎮'},
            {'name': 'Flycast', 'package': 'flycast', 'desc': self._('Dreamcast Emulator'), 'icon': '🎮'},
            {'name': 'BigPEmu', 'package': 'bigpemu', 'desc': self._('Multi System Emulator'), 'icon': '🎮'},
            {'name': "Rosalie's Mupen GUI", 'package': 'rosalie-mg', 'desc': self._('N64 Emulator GUI'), 'icon': '🎮'},
            {'name': 'Snes9x', 'package': 'snes9x', 'desc': self._('Super Nintendo Emulator'), 'icon': '🎮'}
        ]

        self.games = [
            {'name': 'Pico8 Games', 'package': 'pico8-games', 'desc': self._('Collection of Pico-8 Games'), 'icon': '🕹️'},
            {'name': 'SuperTux 2', 'package': 'supertux2', 'desc': self._('2D Jump\'n Run Game'), 'icon': '🕹️'},
            {'name': 'SuperTuxKart', 'package': 'supertuxkart', 'desc': self._('3D Racing Game'), 'icon': '🕹️'},
            {'name': 'Wine + Q4Wine + WineTricks', 'package': 'wine q4wine winetricks', 'desc': self._('Windows Compatibility Layer'), 'icon': '🍷'},
            {'name': 'Lutris', 'package': 'lutris', 'desc': self._('Game Platform'), 'icon': '🎮'},
            {'name': 'Freedoom 1+2', 'package': 'freedoom', 'desc': self._('Free Doom Game'), 'icon': '👾'},
            {'name': 'GNOME 2048', 'package': 'gnome-2048', 'desc': self._('2048 Puzzle Game'), 'icon': '🎲'},
            {'name': 'Prism Launcher', 'package': 'prismlauncher', 'desc': self._('Minecraft Launcher'), 'icon': '⛏️'},
            {'name': 'Heroic Games Launcher', 'package': 'heroic', 'desc': self._('Epic Games Launcher'), 'icon': '🎮'}
        ]
        
        self.create_ui()
        self.check_all_packages()
        
    def load_config(self):
        """Load configuration from file"""
        default_config = {
            'language': locale.getdefaultlocale()[0] or 'en_US',
            'window_size': [800, 800]
        }
        
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = {**default_config, **json.load(f)}
            else:
                self.config = default_config
                self.save_config()
        except Exception:
            self.config = default_config
    
    def save_config(self):
        """Save configuration"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
        except Exception:
            pass
    
    def create_ui(self):
        """Create user interface"""
        # Main window
        self.window = Gtk.Window()
        self.window.set_title("GameToken")
        self.window.set_default_size(*self.config['window_size'])
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.connect("destroy", self.on_destroy)
        self.window.connect("size-allocate", self.on_window_resize)
        
        # Set icon
        for icon_name in ["applications-games", "input-gaming", "applications-all"]:
            try:
                self.window.set_icon_name(icon_name)
                break
            except Exception:
                continue
        
        # Main layout
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.window.add(main_vbox)
        
        # Create menu and content
        self.create_menu(main_vbox)
        self.create_content(main_vbox)
    
    def create_menu(self, parent):
        """Create menu bar"""
        menubar = Gtk.MenuBar()
        
        # System menu
        system_menu = Gtk.Menu()
        system_item = Gtk.MenuItem(label=self._("System"))
        system_item.set_submenu(system_menu)
        
        # Add menu items
        for label, callback in [
            (self._("Update System"), self.update_system),
            (self._("Language"), None),
            (self._("Quit"), self.on_destroy)
        ]:
            if label == self._("Language"):
                lang_item = Gtk.MenuItem(label=label)
                lang_submenu = Gtk.Menu()
                lang_item.set_submenu(lang_submenu)
                
                for code, info in get_available_translations().items():
                    lang_option = Gtk.MenuItem(label=info['native'])
                    lang_option.connect("activate", self.change_language, code)
                    lang_submenu.append(lang_option)
                
                system_menu.append(lang_item)
            else:
                menu_item = Gtk.MenuItem(label=label)
                menu_item.connect("activate", callback)
                system_menu.append(menu_item)
        
        # Help menu
        help_menu = Gtk.Menu()
        help_item = Gtk.MenuItem(label=self._("Help"))
        help_item.set_submenu(help_menu)
        
        about_item = Gtk.MenuItem(label=self._("About"))
        about_item.connect("activate", self.show_about)
        help_menu.append(about_item)
        
        menubar.append(system_item)
        menubar.append(help_item)
        parent.pack_start(menubar, False, False, 0)
    
    def create_content(self, parent):
        """Create main content area"""
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.content_box.set_margin_left(15)
        self.content_box.set_margin_right(15)
        self.content_box.set_margin_top(10)
        self.content_box.set_margin_bottom(10)
        
        # Header
        self.create_header()
        
        # Emulators section
        emulators_label = Gtk.Label()
        emulators_label.set_markup(f"<span size='16000' weight='bold'>{self._('Emulators')}</span>")
        emulators_label.set_halign(Gtk.Align.START)
        self.content_box.pack_start(emulators_label, False, False, 10)
        
        # Emulators grid
        self.emulators_grid = Gtk.Grid()
        self.emulators_grid.set_row_spacing(10)
        self.emulators_grid.set_column_spacing(10)
        self.emulators_grid.set_column_homogeneous(True)
        self.create_package_cards(self.emulators, self.emulators_grid)
        self.content_box.pack_start(self.emulators_grid, False, False, 0)
        
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.content_box.pack_start(separator, False, False, 10)
        
        # Games section
        games_label = Gtk.Label()
        games_label.set_markup(f"<span size='16000' weight='bold'>{self._('Games')}</span>")
        games_label.set_halign(Gtk.Align.START)
        self.content_box.pack_start(games_label, False, False, 10)
        
        # Games grid
        self.games_grid = Gtk.Grid()
        self.games_grid.set_row_spacing(10)
        self.games_grid.set_column_spacing(10)
        self.games_grid.set_column_homogeneous(True)
        self.create_package_cards(self.games, self.games_grid)
        self.content_box.pack_start(self.games_grid, False, False, 0)
        
        # Progress bar and status
        self.create_progress_bar()
        self.status_label = Gtk.Label()
        self.status_label.set_text(self._("Ready"))
        self.content_box.pack_start(self.status_label, False, False, 0)
        
        scrolled.add(self.content_box)
        parent.pack_start(scrolled, True, True, 0)
    
    def create_header(self):
        """Create header section"""
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        icon_label = Gtk.Label()
        icon_label.set_markup("<span size='20000'>🎮</span>")
        
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        title_label = Gtk.Label()
        title_label.set_markup(f"<span size='16000' weight='bold'>{self._('GameToken')}</span>")
        title_label.set_halign(Gtk.Align.START)
        
        subtitle_label = Gtk.Label()
        subtitle_label.set_text(self._("Gaming Package Manager"))
        subtitle_label.set_halign(Gtk.Align.START)
        
        title_box.pack_start(title_label, False, False, 0)
        title_box.pack_start(subtitle_label, False, False, 0)
        
        header_box.pack_start(icon_label, False, False, 0)
        header_box.pack_start(title_box, True, True, 0)
        
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        
        self.content_box.pack_start(header_box, False, False, 0)
        self.content_box.pack_start(separator, False, False, 0)
    
    def create_package_cards(self, packages, grid):
        """Create package cards"""
        for i, package in enumerate(packages):
            card = self.create_package_card(package)
            row = i // 3
            col = i % 3
            grid.attach(card, col, row, 1, 1)
    
    def create_package_card(self, package):
        """Create individual package card"""
        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.IN)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        vbox.set_margin_left(10)
        vbox.set_margin_right(10)
        vbox.set_margin_top(8)
        vbox.set_margin_bottom(8)
        
        # Header with icon and name
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        icon_label = Gtk.Label()
        icon_label.set_markup(f"<span size='14000'>{package['icon']}</span>")
        
        name_label = Gtk.Label()
        name_label.set_markup(f"<span weight='bold'>{package['name']}</span>")
        name_label.set_ellipsize(3)
        
        header_box.pack_start(icon_label, False, False, 0)
        header_box.pack_start(name_label, True, True, 0)
        
        # Status and description
        package['status_label'] = Gtk.Label()
        package['status_label'].set_text(self._("Checking..."))
        
        desc_label = Gtk.Label()
        desc_label.set_text(package['desc'])
        desc_label.set_line_wrap(True)
        desc_label.set_max_width_chars(20)
        
        # Buttons
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        btn_box.set_homogeneous(True)
        
        package['install_btn'] = Gtk.Button(label=self._("Install"))
        package['install_btn'].connect("clicked", self.install_package, package)
        package['install_btn'].get_style_context().add_class("suggested-action")
        
        package['remove_btn'] = Gtk.Button(label=self._("Remove"))
        package['remove_btn'].connect("clicked", self.remove_package, package)
        package['remove_btn'].get_style_context().add_class("destructive-action")
        
        btn_box.pack_start(package['install_btn'], True, True, 0)
        btn_box.pack_start(package['remove_btn'], True, True, 0)
        
        # Pack everything
        for widget in [header_box, package['status_label'], desc_label, btn_box]:
            vbox.pack_start(widget, False, False, 0)
        
        frame.add(vbox)
        return frame

    def create_progress_bar(self):
        """Create progress bar"""
        self.progress_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        
        self.progress_label = Gtk.Label()
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(False)
        
        # Progress controls
        progress_controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        self.cancel_btn = Gtk.Button()
        self.cancel_btn.set_size_request(32, 32)
        self.cancel_btn.set_tooltip_text(self._("Cancel"))
        self.cancel_btn.connect("clicked", self.cancel_process)
        
        # Try to set cancel icon
        for icon_name in ["process-stop", "gtk-stop"]:
            try:
                cancel_icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.SMALL_TOOLBAR)
                self.cancel_btn.set_image(cancel_icon)
                break
            except Exception:
                continue
        else:
            self.cancel_btn.set_label("✕")
        
        progress_controls_box.pack_start(self.cancel_btn, False, False, 0)
        progress_controls_box.pack_start(self.progress_bar, True, True, 0)
        
        self.progress_box.pack_start(self.progress_label, False, False, 0)
        self.progress_box.pack_start(progress_controls_box, False, False, 0)
        
        self.content_box.pack_start(self.progress_box, False, False, 0)
        self.progress_box.hide()

    def start_progress_animation(self):
        """Start progress bar animation"""
        def pulse_progress():
            if self.is_processing:
                self.progress_bar.pulse()
                return True
            return False
        
        self.progress_timeout_id = GLib.timeout_add(100, pulse_progress)
    
    def stop_progress_animation(self):
        """Stop progress bar animation"""
        if self.progress_timeout_id:
            GLib.source_remove(self.progress_timeout_id)
            self.progress_timeout_id = None
        self.progress_bar.set_fraction(0)
    
    def check_all_packages(self):
        """Check status of all packages"""
        def check_thread():
            for package in self.emulators + self.games:
                self.check_package_status(package)
        
        thread = threading.Thread(target=check_thread)
        thread.daemon = True
        thread.start()
    
    def check_package_status(self, package):
        """Check if a package is installed"""
        try:
            packages = package['package'].split()
            installed = True
            for pkg in packages:
                result = subprocess.run(['dpkg', '-l', pkg], 
                                    capture_output=True, text=True, check=False)
                if result.returncode != 0 or 'ii' not in result.stdout:
                    installed = False
                    break
            GLib.idle_add(self.update_package_status, package, installed)
        except Exception:
            GLib.idle_add(self.update_package_status, package, False)
    
    def update_package_status(self, package, installed):
        """Update visual package status"""
        if installed:
            package['status_label'].set_markup(f"<span color='green'>✅ {self._('Installed')}</span>")
            package['install_btn'].set_sensitive(False)
            package['remove_btn'].set_sensitive(True)
        else:
            package['status_label'].set_markup(f"<span color='red'>❌ {self._('Not installed')}</span>")
            package['install_btn'].set_sensitive(True)
            package['remove_btn'].set_sensitive(False)
    
    def show_progress(self, show=True):
        """Show/hide progress bar"""
        if show:
            self.progress_box.show_all()
            self.emulators_grid.set_sensitive(False)
            self.games_grid.set_sensitive(False)
            self.start_progress_animation()
        else:
            self.stop_progress_animation()
            self.progress_box.hide()
            self.emulators_grid.set_sensitive(True)
            self.games_grid.set_sensitive(True)
    
    def run_package_operation(self, operation, package, install=True):  #pylint: disable=unused-argument
        """Generic package operation handler"""
        if self.is_processing:
            return
        
        def operation_thread(): 
            self.is_processing = True
            GLib.idle_add(self.show_progress, True)
            
            try:
                action = self._("Installing {}...") if install else self._("Removing {}...")
                GLib.idle_add(self.progress_label.set_text, action.format(package['name']))
                
                packages = package['package'].split()
                if install:
                    apt_cmd = 'apt-fast' if self.check_apt_fast() else 'apt'
                    cmd = ['pkexec', apt_cmd, 'install', '-y'] + packages
                else:
                    cmd = ['pkexec', 'apt', 'remove', '-y'] + packages
                
                self.current_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.current_process.communicate()
                
                if self.current_process.returncode == 0:
                    success_msg = self._('installed successfully') if install else self._('removed successfully')
                    GLib.idle_add(self.status_label.set_text, f"✅ {package['name']} {success_msg}")
                    GLib.idle_add(self.update_package_status, package, install)
                else:
                    error_msg = self._('Error installing') if install else self._('Error removing')
                    GLib.idle_add(self.status_label.set_text, f"❌ {error_msg} {package['name']}")
                    
            except Exception as e:
                GLib.idle_add(self.status_label.set_text, f"❌ {self._('Error')}: {str(e)}")
            finally:
                self.is_processing = False
                self.current_process = None
                GLib.idle_add(self.show_progress, False)
        
        thread = threading.Thread(target=operation_thread)
        thread.daemon = True
        thread.start()
    
    def install_package(self, widget, package):
        """Install package"""
        #pylint: disable=unused-argument
        self.run_package_operation("install", package, True)
    
    def remove_package(self, widget, package):
        """Remove package"""
        #pylint: disable=unused-argument
        self.run_package_operation("remove", package, False)
    
    def update_system(self, widget=None):
        """Update system"""
        #pylint: disable=unused-argument
        if self.is_processing:
            return
        
        def update_thread():
            self.is_processing = True
            GLib.idle_add(self.show_progress, True)
            
            try:
                GLib.idle_add(self.progress_label.set_text, self._("Updating system..."))
                
                apt_cmd = 'apt-fast' if self.check_apt_fast() else 'apt'
                cmd = ['pkexec', apt_cmd, 'update']
                
                self.current_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.current_process.communicate()
                
                if self.current_process.returncode == 0:
                    GLib.idle_add(self.status_label.set_text, f"✅ {self._('System updated successfully')}")
                else:
                    GLib.idle_add(self.status_label.set_text, f"❌ {self._('Error updating system')}")
                    
            except Exception as e:
                GLib.idle_add(self.status_label.set_text, f"❌ {self._('Error')}: {str(e)}")
            finally:
                self.is_processing = False
                self.current_process = None
                GLib.idle_add(self.show_progress, False)
        
        thread = threading.Thread(target=update_thread)
        thread.daemon = True
        thread.start()
    
    def check_apt_fast(self):
        """Check if apt-fast is available"""
        try:
            subprocess.run(['which', 'apt-fast'], check=True, capture_output=True)
            return True
        except Exception:
            return False
    
    def cancel_process(self, widget):
        """Cancel current process"""
        #pylint: disable=unused-argument
        if self.current_process and self.is_processing:
            try:
                self.current_process.terminate()
                try:
                    self.current_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.current_process.kill()
                    self.current_process.wait()
            except Exception:
                pass
            
            self.status_label.set_text(f"⚠️ {self._('Process cancelled')}")
            self.is_processing = False
            self.current_process = None
            self.show_progress(False)
    
    def change_language(self, widget, lang_code):
        """Change language"""
        #pylint: disable=unused-argument
        self.config['language'] = lang_code
        self.save_config()
        
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=self._("Language changed")
        )
        dialog.format_secondary_text(self._("Please restart the application to apply changes."))
        dialog.run()
        dialog.destroy()
    
    def show_about(self, widget):
        """Show about dialog"""
        #pylint: disable=unused-argument
        about = Gtk.AboutDialog()
        about.set_transient_for(self.window)
        about.set_program_name("GameToken")
        about.set_version("1.0")
        about.set_comments(self._("Gaming Package Manager for Linux"))
        about.set_copyright("© 2025 CuerdOS")
        about.set_license_type(Gtk.License.GPL_3_0)
        
        try:
            about.set_logo_icon_name("applications-games")
        except Exception:
            pass
        
        about.run()
        about.destroy()
    
    def on_window_resize(self, window, allocation):
        """Handle window resize"""
        #pylint: disable=unused-argument
        self.config['window_size'] = [allocation.width, allocation.height]
        self.save_config()
    
    def on_destroy(self, widget=None):
        """Handle application close"""
        #pylint: disable=unused-argument
        if self.current_process and self.is_processing:
            try:
                self.current_process.terminate()
                try:
                    self.current_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.current_process.kill()
            except Exception:
                pass
        if self.progress_timeout_id:
            GLib.source_remove(self.progress_timeout_id)
        Gtk.main_quit()
    
    def run(self):
        """Run application"""
        self.window.show_all()
        self.progress_box.hide()
        Gtk.main()

if __name__ == "__main__":
    app = GameTokenApp()
    app.run()