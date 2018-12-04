from client import Client
import threading
import socket
import sys


PORT = 9876



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
            if command == 'quit':
                self.close_connection(id, nick)
            elif command == 'list':
                self.list_clients(id)
            elif command == 'nickname':
                new_nick = split_data[1]
                self.set_nick(id, new_nick)
            elif command == 'dm':
                nick = split_data[1]
                msg = str.encode(' '.join([s for s in split_data[2:]]) + '\n')
                print('dm=', msg)
                self.send_direct_message(nick, msg)
            else:
                # Bad command
                conn.sendall(str.encode('That is not a valid command.\n'))
        else:
            # This is a broadcast message
            [c.conn.sendall(data) for c in self.client_pool if len(self.client_pool)]


    def close_connection(self, id, nick):
        """Close the client connection"""
        msg = str.encode(f'{nick} has left the chat.\n')
        [c.conn.sendall(msg) for c in self.client_pool if len(self.client_pool)]
        for c in self.client_pool:
            if c.id == id:
                self.client_pool = [c for c in self.client_pool if c.id != id]
                c.conn.close()

    def list_clients(self, id):
        all_users = str.encode(', '.join([c.nick for c in self.client_pool]) + '\n')
        [c.conn.sendall(all_users) for c in self.client_pool if len(self.client_pool)]


    def set_nick(self, id, new_nick):
        for c in self.client_pool:
            if c.id == id:
                old_nick = c.nick
                c.nick = new_nick
                msg = str.encode(f'{old_nick} is now {new_nick}\n')
                [c.conn.sendall(msg) for c in self.client_pool if len(self.client_pool)]

    def send_direct_message(self, nick, msg):
        for c in self.client_pool:
            if c.nick == nick:
                c.conn.sendall(msg)

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
