import socket, random, sys                              # Socket: built in library for network handeling like TCP or UDP
sys.path.append("..")                                   # sys: just appends through ".." the root parent directory
from protocol import get_my_ip                          # we import all these function I already made in the protocol file
from tcp_handler import register_with_server, deregister_with_server

# ----------- Global constants -----------
# Server:
SERVER_IP = "127.0.0.1"                                 # 127.0.0.1 is the IP of the device it is running on, needs to be chaneged
SERVER_TCP_PORT = 10000                                 # TCP does all the admin tasks (Registration, De-Registration, Update Info, Publish Subjects of Interest)
SERVER_UDP_PORT = 20000                                 # UDP to publish, receive, and comment messages
# Client:
CLIENT_NAME = "UserXX"                                  # This has to be a unique name
CLIENT_IP = get_my_ip()                                 # We get this IP with the helper funtion inide the protocol file
CLIENT_TCP_PORT = random.randint(50000, 55000)          # These are random ports that the client creats for UDP or TCP, they are given to the server
CLIENT_UDP_PORT = random.randint(60000, 65000)          #       and the server saves them during registration to be used later on.

def main_menu():
    while True:
        print("\n" + "---------------------------------")
        print("       CLIENT MAIN MENU")
        print("---------------------------------")
        print("1. Update Address Info")
        print("2. Update Subjects of Interest")
        print("3. Publish News")
        print("4. Comment on News")
        print("5. De-register")
        print("6. Exit Program")
        print("---------------------------------")
        
        choice = input("Select an option (1-6): ").strip()
        
        if choice == '1':
            print("\n[CLIENT] Triggering Update Info...")
            
            
        elif choice == '2':
            print("\n[CLIENT] Triggering Update Subjects...")
            
            
        elif choice == '3':
            print("\n[CLIENT] Triggering Publish News...")
           
            
        elif choice == '4':
            print("\n[CLIENT] Triggering Comment...")
            
            
        elif choice == '5':
            print("\n[CLIENT] Triggering De-registration...")
            deregister_with_server(SERVER_IP, SERVER_TCP_PORT, CLIENT_NAME)
            
            break # Exits the menu after deregistering
            
        elif choice == '6':
            print("\n[CLIENT] Shutting down...")
            break # Exits the program
            
        else:
            print("\n[CLIENT] Invalid choice. Please enter a number from 1 to 6.")

if __name__ == "__main__":                              # Main function, only calls our register_with_server() function for now
    print("CLIENT STARTED:")
                                                        # We use .strip() to remove any accidental spaces the user might type
    custom_ip = input(f"Enter Server IP [Press Enter to use default {SERVER_IP}]: ").strip()
    if custom_ip:                                       # Checks if the user didnt just type nothing and press enter
        SERVER_IP = custom_ip
                                                        # Same idea as the IP
    custom_name = input(f"Enter your Unique Name [Press Enter to use default {CLIENT_NAME}]: ").strip()
    if custom_name:
        CLIENT_NAME = custom_name
        
    print(f"\n[CLIENT CONFIG] Name: {CLIENT_NAME} | Target Server: {SERVER_IP}")

    while True:                                         # Asking client if they want to register
        action = input("\nDo you want to register with the server now? (y/n): ").strip().lower()
        
        if action == 'y':
            register_with_server( SERVER_IP, SERVER_TCP_PORT, CLIENT_NAME, CLIENT_IP, CLIENT_TCP_PORT, CLIENT_UDP_PORT )
            main_menu()                                 # Calls main menu after first handshake
            break
        elif action == 'n':
            print("[CLIENT] Registration skipped. Shutting down...")
            break                                       # Breaks out of the loop and ends the script
        else:
            print("[CLIENT] Invalid input. Please type 'y' for yes or 'n' for no.")
