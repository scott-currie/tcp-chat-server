from client import Client
import threading
import socket
import sys


PORT = 9875



class ChatServer(threading.Thread):
    def __init__(self, port, host='localhost'):
        super().__init__(daemon=True)
        self.port = port
        self.host = host
        self.server = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
            socket.IPPROTO_TCP,
        )
        self.client_pool = []

        try:
            self.server.bind((self.host, self.port))
        except socket.error:
            print(f'Bind failed. { socket.error }')
            sys.exit()

        self.server.listen(10)

    def run_thread(self, id, nick, conn, addr):
        """
        """
        print(f'{nick} connected at { addr[0] }{ addr[1] }')
        while True:
            try:
                data = conn.recv(4096)
                self.parse(data, id, nick, conn, addr)
            except OSError:
                break

    def parse(self, data, id, nick, conn, addr):
        str_data = data.decode('utf-8')
        split_data = str_data.split()

        if split_data[0].startswith('/'):
            command = split_data[0][1:].strip()
            print('command=', command)
            if command == 'quit':
                self.close_connection(id, nick)
            elif command == 'list':
                print('list')
            elif command == 'nickname':
                pass
            elif command == 'dm':
                pass
            else:
                # Bad command
                pass
        else:
            # This is a broadcast message
            [c.conn.sendall(data) for c in self.client_pool if len(self.client_pool)]
            # pass


    def close_connection(self, id, nick):
        """Close the client connection"""
        # print('incoming id=', id)
        msg = str.encode(f'{nick} has left the chat.')
        [c.conn.sendall(msg) for c in self.client_pool if len(self.client_pool)]
        for c in self.client_pool:
            # print('checking against id', c.id)
            if c.id == id:
                # print('before remove', len(self.client_pool))
                # self.client_pool.remove(c)
                self.client_pool = [c for c in self.client_pool if c.id != id]
                # print('after remoe', len(self.client_pool))
                c.conn.close()
        # conn.close()


    def run(self):
        """
        """
        print(f'Server running on { self.host }{ self.port }.')

        while True:
            conn, addr = self.server.accept()
            client = Client(conn=conn, addr=addr)
            self.client_pool.append(client)
            threading.Thread(
                target=self.run_thread,
                args=(client.id, client.nick, client.conn, client.addr),
                daemon=True,
            ).start()


if __name__ == '__main__':
    server = ChatServer(PORT)

    try:
        server.run()
    except KeyboardInterrupt:
        [c.conn.close() for c in server.client_pool if len(server.client_pool)]
        sys.exit()
