import socket
import threading
import time
from typing import Optional

class TicTacToeClient:
    """
    Client class for the Tic-Tac-Toe game.
    Handles connection to server and user interaction.
    """
    def __init__(self, host: str = '127.0.0.1', port: int = 5000):
        """Initialize the client."""
        self.host = host
        self.port = port
        self.FORMAT = 'utf-8'
        self.game_active = True
        self.receive_thread: Optional[threading.Thread] = None

    def connect_to_server(self) -> Optional[socket.socket]:
        """Establish connection to the server."""
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.host, self.port))
            print("[CONNECTED] Connected to server")
            return client_socket
        except Exception as e:
            print(f"[ERROR] Could not connect to server: {e}")
            return None

    def handle_game_creation(self, client_socket: socket.socket) -> bool:
        """Handle creating a new game."""
        while True:
            players_count = input("Enter number of players (2-8): ")
            if players_count.isdigit() and 2 <= int(players_count) <= 8:
                break
            print("Invalid number. Please enter a number between 2 and 8.")
            
        client_socket.send(players_count.encode(self.FORMAT))
        print(f"Created new game for {players_count} players")
        return True

    def handle_game_joining(self, client_socket: socket.socket) -> bool:
        """Handle joining an existing game. Returns True if successful, False if need to retry."""
        available_games = client_socket.recv(1024).decode(self.FORMAT)
        print("\nAvailable games:")
        print(available_games)
        
        if "No games available" in available_games:
            print("No games available. Would you like to:")
            print("1. Create new game")
            print("2. Try joining again")
            print("3. Quit")
            
            while True:
                retry_choice = input("Enter your choice (1/2/3): ")
                if retry_choice in ['1', '2', '3']:
                    break
                print("Invalid choice. Please enter 1, 2, or 3.")

            if retry_choice == '3':
                return False
            elif retry_choice == '1':
                client_socket.send('1'.encode(self.FORMAT))
                return self.handle_game_creation(client_socket)
            else:  # retry_choice == '2'
                client_socket.send('2'.encode(self.FORMAT))
                return self.handle_game_joining(client_socket)

        while True:
            game_id = input("Enter game ID to join: ")
            if game_id.isdigit():
                break
            print("Invalid input. Please enter a number.")
            
        client_socket.send(game_id.encode(self.FORMAT))
        return True

    def receive_messages(self, client_socket: socket.socket):
        """Handle incoming messages from the server."""
        while self.game_active:
            try:
                message = client_socket.recv(1024).decode(self.FORMAT)
                if not message:
                    break
                
                print("\n" + message)
                
                if "Game Over" in message:
                    self.game_active = False
                    break
                    
            except Exception as e:
                print(f"[ERROR] {e}")
                self.game_active = False
                break

    def start(self):
        """Start the client and handle the main game loop."""
        while True:  # Main connection loop
            client_socket = self.connect_to_server()
            if not client_socket:
                break

            try:
                # Receive welcome message
                welcome_msg = client_socket.recv(1024).decode(self.FORMAT)
                print(welcome_msg)

                # Choose to create or join game
                while True:
                    choice = input("Enter your choice (1 or 2): ")
                    if choice in ['1', '2']:
                        break
                    print("Invalid choice. Please enter 1 or 2.")

                client_socket.send(choice.encode(self.FORMAT))

                # Handle game creation or joining
                success = False
                if choice == "1":
                    success = self.handle_game_creation(client_socket)
                else:
                    success = self.handle_game_joining(client_socket)

                if not success:
                    print("Returning to main menu...")
                    client_socket.close()
                    continue

                # Start receive thread
                self.game_active = True
                self.receive_thread = threading.Thread(target=self.receive_messages, args=(client_socket,))
                self.receive_thread.daemon = True
                self.receive_thread.start()

                # Main game loop for sending moves
                while self.game_active:
                    try:
                        move = input()
                        if move.lower() == 'quit':
                            break
                            
                        if ',' in move:
                            row, col = move.split(',')
                            if row.strip().isdigit() and col.strip().isdigit():
                                client_socket.send(move.encode(self.FORMAT))
                            else:
                                print("Invalid move format. Use numbers for row and column (e.g., '1,2')")
                        else:
                            print("Invalid move format. Use 'row,col' (e.g., '1,2')")
                            
                    except Exception as e:
                        print(f"[ERROR] {e}")
                        break

                if not self.game_active:
                    print("\nGame ended. Would you like to play again? (yes/no)")
                    if input().lower().startswith('y'):
                        client_socket.close()
                        continue
                    break

            except Exception as e:
                print(f"[ERROR] {e}")
            finally:
                client_socket.close()
                print("\n[DISCONNECTED] Disconnected from server")

            print("Would you like to reconnect? (yes/no)")
            if not input().lower().startswith('y'):
                break

if __name__ == "__main__":
    client = TicTacToeClient()
    print("[STARTING] Client is starting...")
    client.start()