# Tic-Tac-Toe Online Game

## Introduction
This project implements an online **Tic-Tac-Toe** game to demonstrate programming skills and provide a deeper understanding of the **transport and application layers** (layers 4-5). The game utilizes a **client-server architecture** to manage communication between multiple clients and the server.

### Key Features:
- Multi-client support with concurrent games.
- Dynamic game board sizes based on the number of players.
- Real-time game updates and user interaction.
- Expandable gameplay to support multiple players.

---

## Game Rules
- Standard Tic-Tac-Toe rules apply for 2 players, using a 3x3 grid.
- For 3 players, the grid size expands to 4x4, and players need 3 marks in a row (horizontal, vertical, or diagonal) to win.
- Each player is assigned a unique symbol:
  - Player 1: **X**
  - Player 2: **O**
  - Player 3: **∆**
- For more than 3 players, the board size becomes (x + 1)^2 with the same winning condition of 3 marks in a row.

---

### Server Side
- Implemented using **sockets** to support a multi-client Tic-Tac-Toe game.
- Manages game sessions and client connections.
- Handles validation of moves and determines game outcomes (winner or draw).
- Supports multiple concurrent games between different groups of players.

### Client Side
- Connects to the server to start playing.
- Provides a user-friendly interface for gameplay.
- Allows users to:
  - Request a list of available games.
  - Join an existing game or create a new one.
  - View real-time updates of the game state.
  - Exit the game and disconnect gracefully.

---

## Usage
1. Launch the server to host games.
2. Connect clients to the server.
3. Players can either create a new game or join an existing one.
4. Make moves using the user interface and track the game state in real-time.
5. The game ends when a player wins or a draw is declared.
6. Players can leave and join new games as needed.

---

## License
This project is licensed under the MIT License. See the LICENSE file for details.

---
