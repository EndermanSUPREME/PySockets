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
        while CONNECTIONENDED == False:
            recvBuffer = server.recv(64) # size of recv bytes we allow
            if len(recvBuffer) > 0:
                print(f"{recvBuffer.decode()}")
    except Exception as e:
        CONNECTIONENDED = True
        print("Enter /exit - quit")

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

            msgData = str(input("Msg >> "))
            if msgData == "/exit":
                CONNECTIONENDED = True
                print("[*] Killing Connection. . .")
                break
            clientsocket.send(msgData.encode())

        if serverListener.is_alive():
            serverListener.join()
    except Exception as e:
        CONNECTIONENDED = True
        print(f"Error: {e}")

def main():
    StartClient()

if __name__ == "__main__":
    main()