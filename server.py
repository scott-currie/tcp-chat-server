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
        """Run a thread for each connected client. Terminate on connection close.

        input: id (bytes) id of client
        input: nick (bytes) nick of associated client
        input: conn TCP connection object
        input: addr IPV4 address of client
        returns: none
        """
        print(f'{nick} connected at { addr[0] }:{ addr[1] }')
        while True:
            try:
                data = conn.recv(4096)
                self.parse(data, id, nick, conn, addr)
            except OSError:
                break

    def parse(self, data, id, nick, conn, addr):
        """Parse data input by client if it mapped to a command. Use the command
         to decide which function to run.

         input: id (bytes) id of client
         input: nick (bytes) nick of associated client
         input: conn TCP connection object
         input: addr IPV4 address of client
         returns: none
         """
        str_data = data.decode('utf-8').strip()
        split_data = str_data.split()

        if split_data and split_data[0].startswith('/'):
            command = split_data[0][1:]
            if command == 'quit':
                self.close_connection(id)
            elif command == 'list':
                self.list_clients(conn)
            elif command == 'nickname':
                if len(split_data) == 2 and len(split_data[1]):
                    new_nick = split_data[1]
                    if len(new_nick):
                        self.set_nick(id, new_nick)
                        nick = new_nick
                else:
                    conn.sendall(b'That is not a valid nick.\n')
            elif command == 'dm':
                if len(split_data) >= 3 and len(split_data[1]):
                    nick = split_data[1]
                    msg = str.encode(
                        ' '.join([s for s in split_data[2:]]) + '\n')
                    self.send_direct_message(nick, msg)
                else:
                    conn.sendall(b'Something went wrong. Try `/dm <nickname> <your message>`\n')
            else:
                # Bad command
                conn.sendall(str.encode('That is not a valid command.\n'))
        else:
            # This is a broadcast message
            if str_data:
                [c.conn.sendall(data)
                    for c in self.client_pool if len(self.client_pool)]

    def close_connection(self, id):
        """Close the client connection.

        input: id: uuid of the client
        input: nick: nick of the client
        returns: none
        """
        for c in self.client_pool:
            client = c if c.id == id else None
        msg = str.encode(f'{client.nick} has left the chat.\n')
        [c.conn.sendall(msg)
         for c in self.client_pool if len(self.client_pool)]
        for c in self.client_pool:
            if c.id == id:
                self.client_pool = [c for c in self.client_pool if c.id != id]
                c.conn.close()

    def list_clients(self, conn):
        """Show the requesting client a list of all clients.
        input: conn: requesting client's connection object
        returns: none
        """
        all_users = str.encode(
            ', '.join([c.nick for c in self.client_pool]) + '\n')
        conn.sendall(all_users)

    def set_nick(self, id, new_nick):
        """Change nick associated with the requesting client.

        input: id: uuid of requesting client
        input: new_nick: new nick to assign to requesting client
        returns: none
        """
        for c in self.client_pool:
            if c.id == id:
                old_nick = c.nick
                c.nick = new_nick
                msg = str.encode(f'{old_nick} is now {new_nick}\n')
                [c.conn.sendall(msg)
                 for c in self.client_pool if len(self.client_pool)]

    def send_direct_message(self, nick, msg):
        """Show message to a specific client identified by their nick.

        input: nick of client to show message to
        input: msg: message to show receiving client
        returns: none
        """
        for c in self.client_pool:
            if c.nick == nick:
                c.conn.sendall(msg)

    def run(self):
        """Start up the server.
        """
        print(f'Server running on { self.host }:{ self.port }.')

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
