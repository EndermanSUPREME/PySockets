import threading, socket, sys

RUNNING = True

class ConnectedClient:
    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr
    def GetAddress(self):
        return self.addr
    def GetConnection(self):
        return self.conn
    
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

def ConnectClient(connection, address):
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

            if len(recvBuffer) > 0:
                # Clear the current input line
                sys.stdout.write("\033[2K\r")  # Clear line and move cursor to start
                sys.stdout.flush()

                if recvBuffer.decode() == "\n":
                    print(f"[*] {address} Disconnected")
                    # Remove Disconnected User
                    for conn in ConnectedClients:
                        if conn.GetConnection() == connection:
                            ConnectedClients.remove(conn)
                    # Reprint the input prompt at the bottom
                    sys.stdout.write("cmd [/exit - quit] >> ")
                    sys.stdout.flush()
                    break

                recvMessage = f"{address} >> {recvBuffer.decode()}"
                print(recvMessage)

                # Reprint the input prompt at the bottom
                sys.stdout.write("cmd [/exit - quit] >> ")
                sys.stdout.flush()

                # Send message to everyone
                for conn in ConnectedClients:
                    conn.GetConnection().sendall(recvMessage.encode())

    except Exception as e:
        return None

def KillConnect():
    try:
        clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientsocket.connect((GetNetworkIP(), 8888))
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
            connection.sendall(str("Welcome to the Server!").encode())
            clientThread = threading.Thread(target=ConnectClient, name='ClientThread', args=[connection, address])
            ConnectedClients.append(ConnectedClient(connection,address)) # Add Session into Array
            clientThread.start()

        # Initiate Shutdown
        serversocket.close()
        for conn in ConnectedClients:
            print(f"[*] Disconnecting -> {conn.GetAddress()}")
            serverMsg = "Server has been Closed!"
            conn.GetConnection().sendall(serverMsg.encode())
            conn.GetConnection().close()
    except Exception as e:
        print(f"Error: {e}")

    print("[*] Server Session Ended!")

def main():
    global RUNNING
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