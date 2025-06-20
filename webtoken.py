#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import subprocess
import threading
import os
import json
import locale
from translations import get_translation

class WebTokenApp:
    def __init__(self):
        self.is_processing = False
        self.current_process = None
        self.progress_timeout_id = None
        self.config_dir = os.path.expanduser("~/.config/webtoken")
        self.config_file = os.path.join(self.config_dir, "config.json")
        self.load_config()
        self._ = get_translation(self.config.get('language'))
        
        # Define packages with repo requirements
        self.packages = [
            {'name': 'Brave', 'package': 'brave-browser', 'desc': self._('Privacy-focused browser'), 'icon': '🦁', 'repo': 'brave-keyring'},
            {'name': 'Vivaldi', 'package': 'vivaldi-stable', 'desc': self._('Feature-rich browser'), 'icon': '🎭'},
            {'name': 'Thorium', 'package': 'thorium-browser', 'desc': self._('Fast minimalist browser'), 'icon': '⚡', 'repo': 'thorium-repo'},
            {'name': 'Falkon', 'package': 'falkon', 'desc': self._('KDE web browser'), 'icon': '🦅'},
            {'name': 'Firefox', 'package': 'firefox', 'desc': self._('Mozilla Firefox'), 'icon': '🔥'},
            {'name': 'Floorp', 'package': 'floorp', 'desc': self._('Firefox-based browser'), 'icon': '🌊'},
            {'name': 'Transmission', 'package': 'transmission-qt', 'desc': self._('BitTorrent client'), 'icon': '⬇️', 'alt_package': 'transmission-gtk', 'alt_desc': 'GTK'},
            {'name': 'Motrix', 'package': 'motrix', 'desc': self._('Download manager'), 'icon': '📥'},
            {'name': 'Min Browser', 'package': 'min', 'desc': self._('Minimalist web browser'), 'icon': '🌙'},
            {'name': 'Chromium', 'package': 'chromium-browser', 'desc': self._('Open source web browser'), 'icon': '🔵'},
            {'name': 'Materialgram', 'package': 'materialgram', 'desc': self._('Telegram client'), 'icon': '💬'},
            {'name': 'Telegram Desktop', 'package': 'telegram-desktop', 'desc': self._('Telegram client'), 'icon': '✈️'},
            {'name': 'Warpinator', 'package': 'warpinator', 'desc': self._('File sharing tool'), 'icon': '📤'},
            {'name': 'KDE Connect', 'package': 'kdeconnect', 'desc': self._('Device connectivity'), 'icon': '🔗'}
        ]
        
        self.create_ui()
        self.check_all_packages()

    def load_config(self):
        default = {'language': locale.getdefaultlocale()[0] or 'en_US', 'window_size': [900, 650]}
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = {**default, **json.load(f)}
            else:
                self.config = default
                self.save_config()
        except:
            self.config = default

    def save_config(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
        except:
            pass

    def create_ui(self):
        self.window = Gtk.Window()
        self.window.set_title("WebToken")
        self.window.set_default_size(*self.config['window_size'])
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.connect("destroy", self.on_destroy)
        self.window.connect("size-allocate", self.on_window_resize)
        
        # Set system icon
        for icon in ["web-browser", "internet-web-browser", "browser", "applications-internet"]:
            try:
                self.window.set_icon_name(icon)
                break
            except:
                continue

        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.window.add(main_vbox)
        self.create_menu(main_vbox)
        self.create_content(main_vbox)

    def create_menu(self, parent):
        menubar = Gtk.MenuBar()
        
        # System menu
        system_menu = Gtk.Menu()
        system_item = Gtk.MenuItem(label=self._("System"))
        system_item.set_submenu(system_menu)
        
        update_item = Gtk.MenuItem(label=self._("Update System"))
        update_item.connect("activate", self.update_system)
        system_menu.append(update_item)
        
        # Language submenu
        lang_item = Gtk.MenuItem(label=self._("Language"))
        lang_submenu = Gtk.Menu()
        lang_item.set_submenu(lang_submenu)
        
        from translations import TRANSLATIONS
        for code, info in TRANSLATIONS.items():
            lang_option = Gtk.MenuItem(label=info['native'])
            lang_option.connect("activate", self.change_language, code)
            lang_submenu.append(lang_option)
        
        system_menu.append(lang_item)
        
        quit_item = Gtk.MenuItem(label=self._("Quit"))
        quit_item.connect("activate", self.on_destroy)
        system_menu.append(quit_item)
        
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
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.content_box.set_margin_left(15)
        self.content_box.set_margin_right(15)
        self.content_box.set_margin_top(10)
        self.content_box.set_margin_bottom(10)
        
        self.create_header()
        self.create_packages_grid()
        self.create_progress_bar()
        
        self.status_label = Gtk.Label()
        self.status_label.set_text(self._("Ready"))
        
        self.content_box.pack_start(self.packages_grid, True, True, 0)
        self.content_box.pack_start(self.status_label, False, False, 0)
        
        scrolled.add(self.content_box)
        parent.pack_start(scrolled, True, True, 0)

    def create_header(self):
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        icon_label = Gtk.Label()
        icon_label.set_markup("<span size='20000'>🌐</span>")
        
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        title_label = Gtk.Label()
        title_label.set_markup(f"<span size='16000' weight='bold'>{self._('WebToken')}</span>")
        title_label.set_halign(Gtk.Align.START)
        
        subtitle_label = Gtk.Label()
        subtitle_label.set_text(self._("Web & Communication Manager"))
        subtitle_label.set_halign(Gtk.Align.START)
        
        title_box.pack_start(title_label, False, False, 0)
        title_box.pack_start(subtitle_label, False, False, 0)
        
        header_box.pack_start(icon_label, False, False, 0)
        header_box.pack_start(title_box, True, True, 0)
        
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        
        self.content_box.pack_start(header_box, False, False, 0)
        self.content_box.pack_start(separator, False, False, 0)

    def create_packages_grid(self):
        self.packages_grid = Gtk.Grid()
        self.packages_grid.set_row_spacing(10)
        self.packages_grid.set_column_spacing(10)
        self.packages_grid.set_column_homogeneous(True)
        
        for i, package in enumerate(self.packages):
            card = self.create_package_card(package)
            row = i // 3
            col = i % 3
            self.packages_grid.attach(card, col, row, 1, 1)

    def create_package_card(self, package):
        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.IN)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        vbox.set_margin_left(10)
        vbox.set_margin_right(10)
        vbox.set_margin_top(8)
        vbox.set_margin_bottom(8)
        
        # Header
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
        
        # Special handling for packages with alternatives
        if 'alt_package' in package:
            package['alt_btn'] = Gtk.Button(label=package.get('alt_desc', self._("Alt")))
            package['alt_btn'].connect("clicked", self.install_alt_package, package)
            btn_box.pack_start(package['alt_btn'], True, True, 0)
        
        btn_box.pack_start(package['install_btn'], True, True, 0)
        btn_box.pack_start(package['remove_btn'], True, True, 0)
        
        for widget in [header_box, package['status_label'], desc_label, btn_box]:
            vbox.pack_start(widget, False, False, 0)
        
        frame.add(vbox)
        return frame

    def create_progress_bar(self):
        self.progress_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        
        self.progress_label = Gtk.Label()
        self.progress_bar = Gtk.ProgressBar()
        
        progress_controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        self.cancel_btn = Gtk.Button(label="✕")
        self.cancel_btn.set_size_request(32, 32)
        self.cancel_btn.set_tooltip_text(self._("Cancel"))
        self.cancel_btn.connect("clicked", self.cancel_process)
        
        progress_controls.pack_start(self.cancel_btn, False, False, 0)
        progress_controls.pack_start(self.progress_bar, True, True, 0)
        
        self.progress_box.pack_start(self.progress_label, False, False, 0)
        self.progress_box.pack_start(progress_controls, False, False, 0)
        
        self.content_box.pack_start(self.progress_box, False, False, 0)
        self.progress_box.hide()

    def start_progress_animation(self):
        def pulse():
            if self.is_processing:
                self.progress_bar.pulse()
                return True
            return False
        self.progress_timeout_id = GLib.timeout_add(100, pulse)

    def stop_progress_animation(self):
        if self.progress_timeout_id:
            GLib.source_remove(self.progress_timeout_id)
            self.progress_timeout_id = None
        self.progress_bar.set_fraction(0)

    def check_all_packages(self):
        def check_thread():
            for package in self.packages:
                self.check_package_status(package)
        threading.Thread(target=check_thread, daemon=True).start()

    def check_package_status(self, package):
        try:
            result = subprocess.run(['dpkg', '-l', package['package']], capture_output=True, text=True, check=False)
            installed = result.returncode == 0 and 'ii' in result.stdout
            GLib.idle_add(self.update_package_status, package, installed)
        except:
            GLib.idle_add(self.update_package_status, package, False)

    def update_package_status(self, package, installed):
        if installed:
            package['status_label'].set_markup(f"<span color='green'>✅ {self._('Installed')}</span>")
            package['install_btn'].set_sensitive(False)
            package['remove_btn'].set_sensitive(True)
            if 'alt_btn' in package:
                package['alt_btn'].set_sensitive(False)
        else:
            package['status_label'].set_markup(f"<span color='red'>❌ {self._('Not installed')}</span>")
            package['install_btn'].set_sensitive(True)
            package['remove_btn'].set_sensitive(False)
            if 'alt_btn' in package:
                package['alt_btn'].set_sensitive(True)

    def show_progress(self, show=True):
        if show:
            self.progress_box.show_all()
            self.packages_grid.set_sensitive(False)
            self.start_progress_animation()
        else:
            self.stop_progress_animation()
            self.progress_box.hide()
            self.packages_grid.set_sensitive(True)

    def run_package_operation(self, package, install=True, alt_package=False):
        if self.is_processing:
            return

        def operation_thread():
            self.is_processing = True
            GLib.idle_add(self.show_progress, True)
            
            try:
                pkg_name = package['alt_package'] if alt_package else package['package']
                action = self._("Installing {}") if install else self._("Removing {}")
                GLib.idle_add(self.progress_label.set_text, action.format(package['name']))
                
                if install:
                    # Check and install repo if needed
                    if 'repo' in package and not self.check_repo(package['repo']):
                        self.install_repo(package['repo'])
                    
                    apt_cmd = 'apt-fast' if self.check_apt_fast() else 'apt'
                    cmd = ['pkexec', apt_cmd, 'install', '-y', pkg_name]
                else:
                    cmd = ['pkexec', 'apt', 'remove', '-y', pkg_name]
                
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
        
        threading.Thread(target=operation_thread, daemon=True).start()

    def install_package(self, widget, package):  #pylint: disable=unused-argument
        self.run_package_operation(package, True)

    def install_alt_package(self, widget, package):  #pylint: disable=unused-argument
        self.run_package_operation(package, True, alt_package=True)

    def remove_package(self, widget, package):  #pylint: disable=unused-argument
        self.run_package_operation(package, False)

    def check_repo(self, repo_name):
        try:
            result = subprocess.run(['dpkg', '-l', repo_name], capture_output=True, check=False)
            return result.returncode == 0
        except:
            return False

    def install_repo(self, repo_name):
        try:
            cmd = ['pkexec', 'apt', 'install', '-y', repo_name]
            subprocess.run(cmd, check=True)
        except:
            pass

    def update_system(self, widget=None):  #pylint: disable=unused-argument
        if self.is_processing:
            return
        
        def update_thread():
            self.is_processing = True
            GLib.idle_add(self.show_progress, True)
            
            try:
                GLib.idle_add(self.progress_label.set_text, "Updating system...")
                
                apt_cmd = 'apt-fast' if self.check_apt_fast() else 'apt'
                cmd = ['pkexec', apt_cmd, 'update']
                
                self.current_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.current_process.communicate()
                
                if self.current_process.returncode == 0:
                    GLib.idle_add(self.status_label.set_text, f"✅ {self._('System updated successfully')}")
                else:
                    GLib.idle_add(self.status_label.set_text, "❌ Error updating system")
                    
            except Exception as e:
                GLib.idle_add(self.status_label.set_text, f"❌ {self._('Error')}: {str(e)}")
            finally:
                self.is_processing = False
                self.current_process = None
                GLib.idle_add(self.show_progress, False)
        
        threading.Thread(target=update_thread, daemon=True).start()

    def check_apt_fast(self):
        try:
            subprocess.run(['which', 'apt-fast'], check=True, capture_output=True)
            return True
        except:
            return False

    def cancel_process(self, widget):  #pylint: disable=unused-argument
        if self.current_process and self.is_processing:
            try:
                self.current_process.terminate()
                try:
                    self.current_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.current_process.kill()
                    self.current_process.wait()
            except:
                pass
            
            self.status_label.set_text(f"⚠️ {self._('Process cancelled')}")
            self.is_processing = False
            self.current_process = None
            self.show_progress(False)

    def change_language(self, widget, lang_code):  #pylint: disable=unused-argument
        self.config['language'] = lang_code
        self.save_config()
        
        dialog = Gtk.MessageDialog(
            transient_for=self.window, flags=0, message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK, text=self._("Language changed")
        )
        dialog.format_secondary_text(self._("Please restart the application to apply changes."))
        dialog.run()
        dialog.destroy()

    def show_about(self, widget):  #pylint: disable=unused-argument
        about = Gtk.AboutDialog()
        about.set_transient_for(self.window)
        about.set_program_name("WebToken")
        about.set_version("1.0")
        about.set_comments(self._("Web & Communication Manager for Linux"))
        about.set_copyright("© 2025 CuerdOS")
        about.set_license_type(Gtk.License.GPL_3_0)
        
        try:
            about.set_logo_icon_name("internet-web-browser")
        except:
            pass
        
        about.run()
        about.destroy()

    def on_window_resize(self, window, allocation):  #pylint: disable=unused-argument
        self.config['window_size'] = [allocation.width, allocation.height]
        self.save_config()

    def on_destroy(self, widget=None):  #pylint: disable=unused-argument
        if self.current_process and self.is_processing:
            try:
                self.current_process.terminate()
                try:
                    self.current_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.current_process.kill()
            except:
                pass
        if self.progress_timeout_id:
            GLib.source_remove(self.progress_timeout_id)
        Gtk.main_quit()

    def run(self):
        self.window.show_all()
        self.progress_box.hide()
        Gtk.main()

if __name__ == "__main__":
    app = WebTokenApp()
    app.run()
