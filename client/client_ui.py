"""
Terminal User Interface for News Sharing Client
Navigate with UP/DOWN arrow keys, press ENTER to select
"""

import sys
import os
import io
import threading
import time
from collections import deque
from datetime import datetime

import client

# For cross-platform key handling
if sys.platform == "win32":
    import msvcrt
else:
    import tty
    import termios
    import select

sys.path.append("..")
from client import Client


# ============================================================================
# LOG MANAGEMENT
# ============================================================================
class LogCapture:
    def __init__(self, max_logs=20):
        self.logs = deque(maxlen=max_logs)
        self.original_stdout = sys.stdout
    
    def write(self, message):
        if message.strip():
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {message.strip()}"
            self.logs.append(log_entry)
        self.original_stdout.write(message)
    
    def flush(self):
        self.original_stdout.flush()
    
    def get_logs(self):
        return list(self.logs)


# ============================================================================
# MENU SYSTEM
# ============================================================================
class MenuOption:
    def __init__(self, name, description, func):
        self.name = name
        self.description = description
        self.func = func


class ClientUI:
    def __init__(self, client):
        self.client = client
        self.log_capture = LogCapture()
        sys.stdout = self.log_capture
        
        self.menu_options = [
            MenuOption(
                "Register with Server",
                "Connect to server and register your client",
                self.run_register
            ),
            MenuOption(
                "Update User Connection Information",
                "Connect to server and update your IP address, TCP port, and UDP port",
                self.run_update
            ),
            MenuOption(
                "Update Subjects of Interest",
                "Connect to server and update your subjects of interest list for news updates",
                self.run_subjects
            ),
            MenuOption(
                "Publish News",
                "Publish a news message to a subject",
                self.run_publish
            ),
            MenuOption(
                "Publish Comment",
                "Comment on an existing news message",
                self.run_comment
            ),
            MenuOption(
                "Exit",
                "Close the application",
                self.run_exit
            ),
        ]
        
        self.current_selection = 0
        self.running = True
    
    def run_register(self):
        print("[LOG] Starting registration...")
        name = self.get_input("Enter your name: ")
        self.client.register_with_server(name)
        self.pause_for_input()
    
    def run_update(self):
        print("[LOG] Updating connection information with current user values...")
        self.client.request_update()
        print("[LOG] Send update request to the server.")

    def run_subjects(self):
        print("[LOG] Update subjects of interest - Enter details:")
        
        subjects = self.get_input("Enter subjects separated by commas: ")
        subjects_list = subjects.split(",")
        cleaned_list = []
        for subject in subjects_list:
            subject = subject.strip()
            if subject:
              cleaned_list.append(subject)
        
        if cleaned_list:
            self.client.request_subjects_update(*cleaned_list)
            print("[LOG] Sent subjects request to server.")
        else:
            print("[ERROR] Missing required fields")
        
        self.pause_for_input()

    def run_publish(self):
        print("[LOG] Publish News - Enter details:")
        
        subject = self.get_input("Enter subject: ")
        title = self.get_input("Enter message title: ")
        text = self.get_input("Enter message text: ")
        
        if  subject and title and text:
            self.client.request_publish(subject, title, text)
            print("[LOG] Sent publish request to server.")
        else:
            print("[ERROR] Missing required fields")
        
        self.pause_for_input()
    
    def run_comment(self):
        print("[LOG] Publish Comment - Enter details:")

        subject = self.get_input("Enter subject: ")
        title = self.get_input("Enter message title: ")
        text = self.get_input("Enter comment text: ")
        
        if subject and title and text:
            self.client.publish_comment(subject, title, text)
            print("[LOG] Sent comment request to server.")
        else:
            print("[ERROR] Missing required fields")
        
        self.pause_for_input()
    
    def run_exit(self):
        self.running = False
        print("[LOG] Shutting down client...")
    
    def get_input(self, prompt):
        # Write prompt directly to original stdout without switching sys.stdout
        # This keeps sys.stdout redirected to LogCapture so background threads are still captured
        self.log_capture.original_stdout.write(prompt)
        self.log_capture.original_stdout.flush()
        result = input()
        return result
    
    def pause_for_input(self):
        # Write prompt directly to original stdout without switching sys.stdout
        # This keeps sys.stdout redirected to LogCapture so background threads are still captured
        self.log_capture.original_stdout.write("\nPress ENTER to continue...")
        self.log_capture.original_stdout.flush()
        input()
    
    def handle_key_press(self):
        if sys.platform == "win32":
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key == b'\xe0':  # Special key (like arrow keys)
                    key = msvcrt.getch()
                    if key == b'H':  # Up arrow
                        self.current_selection = (self.current_selection - 1) % len(self.menu_options)
                    elif key == b'P':  # Down arrow
                        self.current_selection = (self.current_selection + 1) % len(self.menu_options)
                elif key == b'\r':  # Enter
                    return True
                elif key == b'\x1b':  # Escape
                    self.running = False
        else:
            # Unix implementation
            if select.select([sys.stdin], [], [], 0.1)[0]:
                try:
                    old_settings = termios.tcgetattr(sys.stdin)
                    tty.setraw(sys.stdin.fileno())
                    key = sys.stdin.read(1)
                    if key == '\x1b':  # Escape sequence
                        next_key = sys.stdin.read(1)
                        if next_key == '[':
                            arrow_key = sys.stdin.read(1)
                            if arrow_key == 'A':  # Up arrow
                                self.current_selection = (self.current_selection - 1) % len(self.menu_options)
                            elif arrow_key == 'B':  # Down arrow
                                self.current_selection = (self.current_selection + 1) % len(self.menu_options)
                    elif key == '\r':  # Enter
                        return True
                finally:
                    termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_settings)
        
        return False
    
    def render_screen(self):
        """Render the entire screen"""
        os.system('cls' if sys.platform == "win32" else 'clear')
        
        sys.stdout = self.log_capture.original_stdout
        
        # Display logs
        print("=" * 80)
        print("LOG OUTPUT:")
        print("=" * 80)
        logs = self.log_capture.get_logs()
        for log in logs:
            print(log)
        print()
        
        # Display menu
        print("=" * 80)
        print("NEWS SHARING CLIENT MENU")
        print("=" * 80)
        for i, option in enumerate(self.menu_options):
            marker = ">>> " if i == self.current_selection else "    "
            print(f"{marker}[{i+1}] {option.name}")
            print(f"     {option.description}")
        print()
        print("Use UP/DOWN arrow keys to navigate, ENTER to select, ESC to quit")
        print("=" * 80)
        
        sys.stdout = self.log_capture
    
    def run(self):
        print("[LOG] Client UI started. Use arrow keys to navigate.")
        
        while self.running:
            self.render_screen()
            
            if self.handle_key_press():
                selected = self.menu_options[self.current_selection]
                if selected.name == "Exit":
                    selected.func()
                else:
                    print(f"\n[ACTION] Selected: {selected.name}")
                    selected.func()
            else:
                time.sleep(0.05)  # Small delay to reduce CPU usage
        
        sys.stdout = self.log_capture.original_stdout
        print("\n[LOG] Client UI closed.")


if __name__ == "__main__":
    clnt = Client()
    ui = ClientUI(clnt)

    # We want both the TCP and UDP listeners to run simultaneously without blocking each other.
    # So, we launch the TCP listener loop in its own background thread.
    # daemon=True means this thread will automatically be killed if we close the main program.
    threading.Thread(target=clnt.start_tcp_listener, daemon=True).start()
    
    # We launch the UDP listener loop in a second background thread.
    threading.Thread(target=clnt.start_udp_listener, daemon=True).start()
    
    try:
        ui.run()
    except KeyboardInterrupt:
        sys.stdout = ui.log_capture.original_stdout
        print("\n\n[INTERRUPT] Application terminated by user.")
        sys.exit(0)
