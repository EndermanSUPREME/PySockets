import socket
import sys
import threading

CONNECTIONENDED = False

def Help():
    print(f"Usage: {sys.argv[0]} [IP] [PORT]")
    print("Enter no arguments for IP/PORT prompt input")
    exit()

def ListenToServer(server):
    global CONNECTIONENDED
    try:
        while not CONNECTIONENDED:
            recvBuffer = server.recv(64)  # Buffer size
            if len(recvBuffer) > 0:
                # Clear the current input line
                sys.stdout.write("\033[2K\r")  # Clear line and move cursor to start
                sys.stdout.flush()

                # Print the received message
                print(f"{recvBuffer.decode()}")
                
                # Reprint the input prompt at the bottom
                sys.stdout.write("Msg >> ")
                sys.stdout.flush()
    except Exception as e:
        CONNECTIONENDED = True

def StartClient():
    global CONNECTIONENDED
    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverIP = ""
    serverPORT = 0

    for a in sys.argv:
        if str(a) == "help" or str(a) == "--help" or str(a) == "-h":
            Help()

    if (len(sys.argv) == 3):
        serverIP = str(sys.argv[1])
        serverPORT = int(sys.argv[2])
    else:
        Help()

    try:
        clientsocket.connect((serverIP, serverPORT))

        # Turn on listener
        serverListener = threading.Thread(target=ListenToServer, args=[clientsocket])

        while True:
            # Test connection
            clientsocket.send(b'')

            if serverListener.is_alive() == False:
                serverListener.start()

            msgData = str(input()).lstrip()

            sys.stdout.write("\033[2K") # Erase the entire line
            sys.stdout.write("\r") # Move cursor back to the start of the line
            sys.stdout.flush()

            if msgData == "/exit":
                CONNECTIONENDED = True
                clientsocket.send(b'\n')
                clientsocket.close()
                print("[*] Killing Connection. . .")
                break

            if len(msgData) > 0 and msgData.isspace() == False:
                clientsocket.send(msgData.encode())
            else:
                sys.stdout.write("\033[F\033[K")
                sys.stdout.write("Msg >> ")
                sys.stdout.flush()

        if serverListener.is_alive():
            serverListener.join()
    except Exception as e:
        CONNECTIONENDED = True
        clientsocket.close()
        print(f"Error: {e}")

def main():
    StartClient()

if __name__ == "__main__":
    main()