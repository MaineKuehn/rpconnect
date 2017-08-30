import builtins
import logging
import socket
import json
import threading


def read_socket(source_socket, num_bytes):
    message = b""
    while True:
        chunk = source_socket.recv(num_bytes - len(message))
        message += chunk
        if not chunk or len(message) == num_bytes:
            return message


def read_message(source_socket):
    message_length = int.from_bytes(read_socket(source_socket, 16), 'little')
    raw_message = read_socket(source_socket, message_length)
    return raw_message.decode()


def send_message(target_socket, message: str):
    raw_message = message.encode()
    target_socket.sendall(len(raw_message).to_bytes(16, 'little'))
    target_socket.sendall(raw_message)


def remote_call(host: str, port: int, name: str, *args, **kwargs):
    """
    Dispatch a call to a :py:class:`RpcServer` at ``host``

    :param host: host to connect to
    :param port: port on host the server is listening add
    :param name: name a payload is registered with the server
    :param args: positional arguments for the payload
    :param kwargs: keyword arguments for the payload
    """
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.connect((host, port))
    data = {'name': name, 'args': args, 'kwargs': kwargs}
    message = json.dumps(data)
    send_message(serversocket, message)
    raw_result = read_message(serversocket)
    serversocket.close()
    reply = json.loads(raw_result)
    if reply['type'] == 'error':
        if isinstance(getattr(builtins, reply['exc_type'], None), Exception):
            raise getattr(builtins, reply['exc_type'])(reply['message'])
        raise ValueError('%s: %s' % (reply['exc_type'], reply['message']))
    elif reply['type'] == 'result':
        return reply['content']
    else:
        raise ValueError('malformed reply: %s' % reply)


class RpcServer(object):
    """
    Server to expose callables over TCP for remote procedure call

    :param port: port number to listen on
    :param interface: the interface to bind to, e.g. 'localhost'

    .. code::

        def pingpong(*args, **kwargs):
            return args, kwargs

        with RpcServer(23000) as server:
            server.register(pingpong)
            server.run()
    """
    def __init__(self, port: int, interface: str=''):
        self.port = port
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind((interface, port))
        self._payloads = {}  # name => callable
        self._socket.listen(5)

    def register_payload(self, payload: callable, name: str=None):
        """
        Register a callable under a given name

        :param name: name to register the payload with
        :param payload: callable to register
        :return:
        """
        if name is None:
            name = payload.__name__
        self._payloads[name] = payload

    def run(self):
        """Run the server, blocking until interrupted"""
        while True:
            (clientsocket, address) = self._socket.accept()
            logging.info('new connection: %s', address)
            # TODO: register these?
            connection_thread = threading.Thread(target=self.handle_connection, args=(clientsocket, address))
            connection_thread.start()

    def handle_connection(self, clientsocket, address):
        logging.info('[%s] handling connection', address)
        try:
            message = read_message(clientsocket)
            data = json.loads(message)
            payload_name = data['name']
            payload_args = data['args']
            payload_kwargs = data['kwargs']
            logging.debug('[%s]: %s(*%s, **%s)', address, payload_name, payload_args, payload_kwargs)
            result = self._payloads[payload_name](*payload_args, **payload_kwargs)
            send_message(clientsocket, self._format_result(result))
            logging.debug('[%s]: %s', address, result)
        except Exception as err:
            logging.exception('[%s]: Exception', address)
            send_message(clientsocket, self._format_exception(err))
        clientsocket.close()

    @staticmethod
    def _format_exception(err, message=''):
        data = {'type': 'error', 'exc_type': err.__class__.__name__, 'message': message or str(err)}
        return json.dumps(data)

    @staticmethod
    def _format_result(result):
        data = {'type': 'result', 'content': result}
        return json.dumps(data)

    def dispatch_call(self, data):
        payload_name = data['name']
        payload_args = data['args']
        payload_kwargs = data['kwargs']
        return self._payloads[payload_name](*payload_args, **payload_kwargs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.error('__exit__: %s %s', exc_type, exc_val)
        self.close()
        return False

    def close(self):
        self._socket.close()

    def __del__(self):
        self.close()

__all__ = ['remote_call', 'RpcServer']
