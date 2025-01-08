import socket
import threading
import time
from typing import Dict, List, Optional

class TicTacToeGame:
    """
    A class representing a single Tic-Tac-Toe game instance.
    Handles game logic, board state, and dynamic player management.
    """
    def __init__(self, game_id: int):
        """
        Initialize a new game instance.
        
        Args:
            game_id (int): Unique identifier for the game
        """
        self.game_id = game_id
        self.min_players = 2
        self.board_size = 3  # Initial board size
        self.board = [[' ' for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.players: List[tuple] = []  # List of (connection, address, symbol) tuples
        self.current_turn = 0
        self.game_active = True
        self.game_started = False
        self.symbols = ['X', 'O', '∆', '#', '@', '&', '%', '*', '+', '£', '€', '¥', '§', '¢', '¤']  # Extended symbols
        self.last_move = None
        self.FORMAT = 'utf-8'
        self.lock = threading.Lock()  # Add lock for thread safety

    def resize_board(self, new_size: int):
        """Resize the board while preserving existing moves."""
        with self.lock:
            new_board = [[' ' for _ in range(new_size)] for _ in range(new_size)]
            # Copy existing moves to new board
            for i in range(min(len(self.board), new_size)):
                for j in range(min(len(self.board[0]), new_size)):
                    new_board[i][j] = self.board[i][j]
            self.board = new_board
            self.board_size = new_size

    def add_player(self, conn, addr) -> bool:
        """Add a new player to the game and resize board if necessary."""
        with self.lock:
            if not self.game_active:
                return False
            if len(self.players) >= len(self.symbols):
                return False
                
            self.players.append((conn, addr, self.symbols[len(self.players)]))
            
            # Calculate new board size
            new_size = (len(self.players) + 1) * 2
            if new_size > self.board_size:
                self.resize_board(new_size)
                
            # Start game if minimum players reached
            if len(self.players) >= self.min_players and not self.game_started:
                self.game_started = True
                
            return True

    def make_move(self, player_idx: int, row: int, col: int) -> bool:
        """Make a move on the board."""
        with self.lock:
            if not all(isinstance(x, int) for x in [player_idx, row, col]):
                return False
                
            if (not self.game_active or 
                not self.game_started or
                self.current_turn != player_idx or 
                not (0 <= row < self.board_size and 0 <= col < self.board_size) or 
                self.board[row][col] != ' '):
                return False
            
            self.board[row][col] = self.players[player_idx][2]
            self.last_move = (row, col)
            self.current_turn = (self.current_turn + 1) % len(self.players)
            return True

    def check_winner(self) -> Optional[str]:
        """Check if there's a winner or if the game is a draw."""
        if not self.last_move:
            return None
            
        row, col = self.last_move
        symbol = self.board[row][col]
        
        # Check all possible directions
        directions = [
            [(0, 1), (0, -1)],  # Horizontal
            [(1, 0), (-1, 0)],  # Vertical
            [(1, 1), (-1, -1)], # Diagonal
            [(1, -1), (-1, 1)]  # Anti-diagonal
        ]
        
        for dir_pair in directions:
            count = 1
            for dx, dy in dir_pair:
                for i in range(1, 3):
                    new_row, new_col = row + dx*i, col + dy*i
                    if (0 <= new_row < self.board_size and 
                        0 <= new_col < self.board_size and 
                        self.board[new_row][new_col] == symbol):
                        count += 1
                    else:
                        break
            if count >= 3:
                return symbol

        # Check for draw
        if all(self.board[i][j] != ' ' 
               for i in range(self.board_size) 
               for j in range(self.board_size)):
            return 'DRAW'
        
        return None

class GameServer:
    """
    Main server class that handles multiple game instances and client connections.
    """
    def __init__(self, host: str = '127.0.0.1', port: int = 5000):
        """Initialize the game server."""
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.games: Dict[int, TicTacToeGame] = {}
        self.next_game_id = 1
        self.FORMAT = 'utf-8'
        self.active = True

    def start(self):
        """Start the server and listen for incoming connections."""
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(10)
            print(f"[LISTENING] Server is listening on {self.host}")

            while self.active:
                try:
                    conn, addr = self.server_socket.accept()
                    thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                    thread.daemon = True
                    thread.start()
                    print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")
                except socket.error as e:
                    print(f"[ERROR] Socket error: {e}")
                    continue
                
        except Exception as e:
            print(f"[CRITICAL ERROR] {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up server resources."""
        self.active = False
        for game in self.games.values():
            for conn, _, _ in game.players:
                try:
                    conn.close()
                except:
                    pass
        self.server_socket.close()

    def handle_client(self, conn: socket.socket, addr):
        """Handle individual client connections."""
        print(f"[NEW CONNECTION] {addr} connected.")
        
        try:
            conn.send("Welcome to Tic-Tac-Toe! Choose:\n1. Create new game\n2. Join existing game".encode(self.FORMAT))
            choice = conn.recv(1024).decode(self.FORMAT)

            if choice == "1":
                self.handle_new_game(conn, addr)
            elif choice == "2":
                self.handle_join_game(conn, addr)
            else:
                conn.send("Invalid choice".encode(self.FORMAT))
                return

        except Exception as e:
            print(f"[ERROR] {addr}: {e}")
        finally:
            conn.close()

    def handle_new_game(self, conn: socket.socket, addr):
        """Handle creation of a new game."""
        try:
            game = TicTacToeGame(self.next_game_id)
            self.games[self.next_game_id] = game
            game.add_player(conn, addr)
            conn.send(f"Created game {self.next_game_id}. Waiting for at least one more player...\n".encode(self.FORMAT))
            self.next_game_id += 1
            
            self.handle_game(game, conn)
            
        except ValueError as e:
            conn.send(f"Invalid input: {str(e)}".encode(self.FORMAT))

    def handle_join_game(self, conn: socket.socket, addr):
        """Handle a client joining an existing game."""
        active_games = [game for game in self.games.values() if game.game_active]
        
        if not active_games:
            conn.send("No games available".encode(self.FORMAT))
            choice = conn.recv(1024).decode(self.FORMAT)
            if choice == "1":
                self.handle_new_game(conn, addr)
            return
        
        # Format game list
        games_info = []
        for game in active_games:
            games_info.append(f"Game {game.game_id} ({len(game.players)} players, Board: {game.board_size}x{game.board_size})")
        
        # Send the list of games
        conn.send(("\n".join(games_info)).encode(self.FORMAT))
        
        try:
            game_id_raw = conn.recv(1024).decode(self.FORMAT)
            if not game_id_raw.isdigit():
                conn.send("Invalid input: Please enter a number".encode(self.FORMAT))
                return
                
            game_id = int(game_id_raw)
            if game_id not in self.games:
                conn.send("Invalid game ID".encode(self.FORMAT))
                return
            
            game = self.games[game_id]
            if not game.add_player(conn, addr):
                conn.send("Cannot join game - game is inactive or full".encode(self.FORMAT))
                return
            
            # Start handling the game for this player
            self.handle_game(game, conn)
            
        except ValueError:
            conn.send("Invalid game ID format".encode(self.FORMAT))

    def handle_game(self, game: TicTacToeGame, player_conn: socket.socket):
        """Handle the main game loop for a specific player."""
        player_idx = next(i for i, (conn, _, _) in enumerate(game.players) if conn == player_conn)
        
        # Wait for minimum players to join if game hasn't started
        if not game.game_started:
            last_player_count = len(game.players)
            initial_message_sent = False
            
            while not game.game_started:
                try:
                    current_player_count = len(game.players)
                    if not initial_message_sent or current_player_count != last_player_count:
                        for conn, _, _ in game.players:
                            try:
                                message = f"Waiting for players... ({current_player_count}/{game.min_players} minimum)\n"
                                if current_player_count != last_player_count and last_player_count < current_player_count:
                                    message = f"New player joined! Need {game.min_players - current_player_count} more player(s) to start...\n"
                                conn.send(message.encode(self.FORMAT))
                            except:
                                continue
                        initial_message_sent = True
                        last_player_count = current_player_count
                    
                    time.sleep(1)
                    if not game.game_active:
                        return
                except:
                    return

        # Game loop
        last_board_state = {conn: None for conn, _, _ in game.players}
        
        while game.game_active:
            try:
                game_state = self.format_board(game)
                current_player_symbol = game.players[game.current_turn][2]
                status = f"\nCurrent turn: {current_player_symbol}\n"
                status += f"Players: {', '.join(symbol for _, _, symbol in game.players)}\n"
                status += f"Board size: {game.board_size}x{game.board_size}\n"
                
                current_state = game_state + status
                
                # Send updates to all players
                for conn, _, symbol in game.players:
                    try:
                        if conn not in last_board_state or last_board_state[conn] != current_state:
                            conn.send(current_state.encode(self.FORMAT))
                            if game.current_turn == next(i for i, (c, _, _) in enumerate(game.players) if c == conn):
                                conn.send("Your turn! Enter move (row,col):".encode(self.FORMAT))
                            else:
                                conn.send(f"Waiting for player {current_player_symbol}'s move...".encode(self.FORMAT))
                            last_board_state[conn] = current_state
                    except:
                        continue

                # Handle moves
                if game.current_turn == player_idx:
                    try:
                        move = player_conn.recv(1024).decode(self.FORMAT)
                        if not move:
                            raise ConnectionError("Empty response from client")
                            
                        try:
                            row, col = map(int, move.strip().split(','))
                        except:
                            player_conn.send("Invalid move format. Use 'row,col' (e.g., '1,2')".encode(self.FORMAT))
                            continue
                            
                        if game.make_move(player_idx, row, col):
                            last_board_state = {conn: None for conn in last_board_state}
                            winner = game.check_winner()
                            if winner:
                                game.game_active = False
                                self.broadcast_game_end(game, winner)
                        else:
                            player_conn.send("Invalid move. Try again.".encode(self.FORMAT))
                    except ConnectionError:
                        break
                        
                time.sleep(0.1)
                
            except Exception as e:
                print(f"[GAME ERROR] {e}")
                break

    def format_board(self, game: TicTacToeGame) -> str:
        """Format the game board for display."""
        result = "\nCurrent board:\n"
        for i in range(game.board_size):
            result += "|".join(f" {cell} " for cell in game.board[i]) + "\n"
            if i < game.board_size - 1:
                result += "-" * (4 * game.board_size - 1) + "\n"
        return result

    def broadcast_game_end(self, game: TicTacToeGame, winner: str):
        """Broadcast game end message to all players."""
        final_board = self.format_board(game)
        message = "\nGame Over! "
        if winner == 'DRAW':
            message += "It's a draw!"
        else:
            message += f"Player {winner} wins!"
            
        for conn, _, _ in game.players:
            try:
                conn.send((final_board + message).encode(self.FORMAT))
            except:
                continue

if __name__ == "__main__":
    server = GameServer()
    print("[STARTING] Server is starting...")
    server.start()