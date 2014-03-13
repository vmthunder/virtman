import socket
import eventlet
import requests

def main():
    #sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #sock.connect(('10.107.14.50', 8040))
    #eventlet.connect(('localhost', 8040))
    #print 'Haha'
    url = 'http://localhost:8040'
    print requests.get(url)

if __name__ == '__main__' :
    main()
