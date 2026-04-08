import sys
import os
import threading
from collections import deque
from datetime import datetime

sys.path.append("..")
from client import Client


# ============================================================================
# LOG MANAGEMENT
# ============================================================================
class LogCapture:
    def __init__(self, max_logs=20):
        # double ended queue to store logs with a maximum length to prevent memory issues
        # 20 by default
        self.logs = deque(maxlen=max_logs)
        # Keep a reference to the original stdout so we can write prompts and user input without switching sys.stdout
        self.original_stdout = sys.stdout
    
    def write(self, message):
        #remove whitespace-only messages to avoid cluttering the log with empty lines
        if message.strip():
            #add details
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {message.strip()}"
            self.logs.append(log_entry)

        # Also write the message to the original stdout so it appears in the console for user input and prompts
        self.original_stdout.write(message)
    
    def flush(self):
        # Flush the original stdout to ensure all prompts and user input are displayed immediately
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
                "Update Server IP Address",
                "Change the IP address of the server you want to connect to",
                self.run_update_server_ip
            ),
            MenuOption(
                "Register with Server",
                "Connect to server and register your client",
                self.run_register
            ),
            MenuOption(
                "Deregister from Server",
                "Connect to server and deregister your client",
                self.run_deregister
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

    def run_update_server_ip(self):
        print("[LOG] Update Server IP Address - Enter details:")
        new_ip = self.get_input("Enter new server IP address: ")
        self.client.server_ip = new_ip
        print(f"[LOG] Updated server IP address to {self.client.server_ip}")
        self.pause_for_input()
    
    def run_register(self):
        print("[LOG] Starting registration...")
        name = self.get_input("Enter your name: ")
        self.client.register_with_server(name)
        self.pause_for_input()

    def run_deregister(self):
        print("[LOG] Starting deregistration...")
        self.client.deregister_with_server()
        self.pause_for_input()
    
    # Automatically passes current ip, tcp and udp ports to client request_update method
    def run_update(self):
        print("[LOG] Update connection information - Enter details:")
        name = self.get_input("Enter name: ")
        self.client.request_update(name)
        print("[LOG] Send update request to the server.")

    # Asks user to input desired subjects separated by commas, and passes to relevant client.py method
    def run_subjects(self):
        print("[LOG] Update subjects of interest - Enter details:")
        
        subjects = self.get_input("Enter subjects separated by commas: ")
        subjects_list = subjects.split(",")
        cleaned_list = []
        # Strips each subject and appends it to a cleaned list to be passed to client method
        for subject in subjects_list:
            subject = subject.strip()
            if subject:
              cleaned_list.append(subject)
        
        # If user enters at least one string as a subject it is passed to the relevant client method
        if cleaned_list:
            self.client.request_subjects_update(cleaned_list)
            print("[LOG] Sent subjects request to server.")
        else:
            print("[ERROR] Missing required fields")
        
        self.pause_for_input()

    def run_publish(self):
        print("[LOG] Publish News - Enter details:")
        
        subject = self.get_input("Enter subject: ")
        title = self.get_input("Enter message title: ")
        text = self.get_input("Enter message text: ")
        
        # must have all fields filled
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
    
    def render_screen(self):
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
        print("Enter the option number and press ENTER to select")
        print("=" * 80)
        
        sys.stdout = self.log_capture
    
    def get_menu_selection(self):
        selection = self.get_input("Select an option number: ")
        #remove whitespace-only inputs to prevent errors and accidental selections
        if not selection.strip():
            return None
        #return number input if valid
        if selection.isdigit():
            index = int(selection) - 1
            if 0 <= index < len(self.menu_options):
                self.current_selection = index
                return self.current_selection
        print("[ERROR] Invalid selection. Please enter a number from the menu.")
        self.pause_for_input()
        return None

    def run(self):
        print("[LOG] Client UI started. Use the menu number to select options.")
        
        #loop until the running == false
        while self.running:
            self.render_screen()
            
            selected_index = self.get_menu_selection()
            if selected_index is not None:
                selected = self.menu_options[selected_index]
                print(f"\n[ACTION] Selected: {selected.name}")
                selected.func()
        
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
