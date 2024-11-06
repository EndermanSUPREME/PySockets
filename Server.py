import threading, socket, sys, os
import sqlite3
import hashlib

RUNNING = True
SALT = os.urandom(16) # Generate Random salt on Start

class ConnectedClient:
    def __init__(self, conn, addr, auth):
        self.conn = conn
        self.addr = addr
        self.auth = auth
        self.username = ""
        self.passwd = ""

    def GetAddress(self):
        return self.addr
    def GetConnection(self):
        return self.conn
    
    def SetAuth(self, status):
        self.auth = status
    def IsAuth(self):
        return self.auth
    
    def SetUsername(self, username):
        self.username = username
    def GetUsername(self):
        return self.username
    
    def SetPasswd(self, passwd):
        self.passwd = passwd
    def GetPasswd(self):
        return self.passwd

# Array of connected clients
ConnectedClients = []

def GetNetworkIP():
    try:
        # Create a dummy socket connection to get the IP address
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # Connect to a public IP (it doesn't have to be reachable)
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception as e:
        print(f"Error: {e}")
        return None
    
def HashPasswd(passwd):
    global SALT
    HashObj = hashlib.sha256(SALT + passwd.encode())
    return str(SALT.hex() + ":" + HashObj.hexdigest())  # Return salt and hash
    
def AttemptAuthentication(username,passwd):
    # Create or Open an Existing db file
    conn = sqlite3.connect('creds.db')
    cursor = conn.cursor()

    # Create a table if it doesn't exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL)''')
    
    passwdHash = HashPasswd(passwd)

    # Clear the current input line
    sys.stdout.write("\033[2K\r")  # Clear line and move cursor to start
    sys.stdout.flush()
    print(f"Auth: {username}|{passwdHash}")

    # Execute a SELECT query
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    userCheck = cursor.fetchone()  # Fetch one result

    # Check if a username exists
    if userCheck:
        cursor.execute("SELECT username FROM users WHERE username = ? AND password = ?", (username,passwdHash))
        passwdCheck = cursor.fetchone()  # Fetch one result
        if passwdCheck:
            # Clear the current input line
            sys.stdout.write("\033[2K\r")  # Clear line and move cursor to start
            sys.stdout.flush()
            print(f"New User Logged in: {username}")
            return "User Logged in Successfully.\n"
        else:
            return "Username or Password is Incorrect.\n"
    else:
        # try to register a new user
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, passwdHash))
            conn.commit()

            # Clear the current input line
            sys.stdout.write("\033[2K\r")  # Clear line and move cursor to start
            sys.stdout.flush()
            print(f"New User Registered: {username}")

            return "User Registered Successfully.\n"
        except sqlite3.IntegrityError:
            print(f"Username: {username} already Exists.")

def ConnectClient(connection, address, ClientData):
    global RUNNING,ConnectedClients

    # Clear the current input line
    sys.stdout.write("\033[2K\r")  # Clear line and move cursor to start
    sys.stdout.flush()
    print(f"[*] Incoming Connection from {address}")

    sys.stdout.write("cmd [/exit - quit] >> ")
    sys.stdout.flush()

    try:
        while RUNNING:
            recvBuffer = connection.recv(64) # size of recv bytes we allow

            if RUNNING == False:
                break

            # When a user is not authenticated they cannot
            # talk to others on the server that are connected and auth'd
            if ClientData.IsAuth() == False:
                if len(ClientData.GetUsername()) == 0:
                    ClientData.SetUsername(recvBuffer.decode())
                    ClientData.SetPasswd("ATTEMPT")
                    connection.sendall(str(f"Enter Passwd for {ClientData.GetUsername()}:").encode())
                else:
                    # When authenticating the Username has been set and the Passwd
                    # is set to a filler so we can take the recv buffer and use it
                    # in a query against the sqlite3 db
                    ClientData.SetPasswd(recvBuffer.decode())
                    authResp = AttemptAuthentication(ClientData.GetUsername(), ClientData.GetPasswd())
                    if "Successfully" in authResp:
                        ClientData.SetAuth(True)
                    else:
                        ClientData.SetUsername("")
                        ClientData.SetPasswd("")
                        ClientData.SetAuth(False)
                    # Send the Auth resp to the connected user
                    connection.sendall(authResp.encode())
            else:
                if len(recvBuffer) > 0:
                    # Clear the current input line
                    sys.stdout.write("\033[2K\r")  # Clear line and move cursor to start
                    sys.stdout.flush()

                    if recvBuffer.decode() == "\n":
                        loggoutMsg = f"[*] {ClientData.GetUsername()} Disconnected"
                        print(loggoutMsg)

                        # Send message to everyone that is authenticated
                        for conn in ConnectedClients:
                            if conn.IsAuth() and conn.GetConnection() != connection:
                                conn.GetConnection().sendall(loggoutMsg.encode())

                        # Remove Disconnected User
                        ConnectedClients.remove(ClientData)

                        # Reprint the input prompt at the bottom
                        sys.stdout.write("cmd [/exit - quit] >> ")
                        sys.stdout.flush()
                        connection.close()
                        break

                    recvMessage = f"{ClientData.GetUsername()} >> {recvBuffer.decode()}"
                    print(recvMessage)

                    # Reprint the input prompt at the bottom
                    sys.stdout.write("cmd [/exit - quit] >> ")
                    sys.stdout.flush()

                    # Send message to everyone
                    for conn in ConnectedClients:
                        if conn.IsAuth():
                            conn.GetConnection().sendall(recvMessage.encode())
    except Exception as e:
        return None

def KillConnect():
    try:
        fakeSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        fakeSocket.connect((GetNetworkIP(), 8888))
    except:
        return None

def RunServer():
    try:
        global RUNNING,ConnectedClients
        hostname = socket.gethostname()
        IPAddr = GetNetworkIP()
        PORT = 8888

        print(f"Your Computer Name is: {hostname}")
        print(f"Your Computer IP Address is: {IPAddr}")

        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.bind((str(IPAddr), PORT))
        serversocket.listen(5) # become a server socket, maximum 5 connections
        print(f"[+] Server Active | {IPAddr}:{PORT}")

        sys.stdout.write("cmd [/exit - quit] >> ")
        sys.stdout.flush()

        while RUNNING:
            # When a connection is captured we sent it to
            # run in a different thread to allow multi-user
            connection, address = serversocket.accept()
            if RUNNING == False:
                break

            connection.sendall(str("Welcome to the Server!\n").encode())
            connection.sendall(str("Enter Username:").encode())

            clientSession = ConnectedClient(connection,address, False)
            clientThread = threading.Thread(target=ConnectClient, name='ClientThread', args=[connection,address,clientSession])
            ConnectedClients.append(clientSession) # Add Session into Array
            clientThread.start()

        # Initiate Shutdown
        serversocket.close()
        for conn in ConnectedClients:
            print(f"[*] Disconnecting -> {conn.GetUsername()}")
            serverMsg = "Server has been Closed!\n"
            conn.GetConnection().sendall(serverMsg.encode())
            conn.GetConnection().close()
    except Exception as e:
        print(f"Error: {e}")

    print("[*] Server Session Ended!")

def main():
    global RUNNING,SALT
    print("[*] Preparing Threads. . .")
    serverThread = threading.Thread(target=RunServer, name='ServerThread')
    serverThread.start() # start thread

    while True:
        msg = str(input()).lstrip()
        if msg == "/exit":
            RUNNING = False
            KillConnect()
            break

        if len(msg) == 0 or msg.isspace():
            sys.stdout.write("\033[F\033[K")
            sys.stdout.write("cmd [/exit - quit] >> ")
            sys.stdout.flush()
        else:
            sys.stdout.write("cmd [/exit - quit] >> ")
            sys.stdout.flush()

    serverThread.join() # wait for thread to finish
    print("End Of Program. . .")

if __name__ == "__main__":
    main()