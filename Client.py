import socket
import sys

def Help():
    print(f"Usage: {sys.argv[0]} [IP] [PORT]")
    print("Enter no arguments for IP/PORT prompt input")
    exit()

def StartClient():
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
        while True:
            msgData = str(input("Msg >> "))
            if msgData == "/exit":
                print("[*] Killing Connection. . .")
                break
            clientsocket.send(msgData.encode())
    except Exception as e:
        print(f"Error: {e}")

def main():
    StartClient()

if __name__ == "__main__":
    main()