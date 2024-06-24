import socket
import select
import protocol


# make sure our user has a name, so that they can't run commands without one
def is_named(my_socket, client_names):
    for entry in client_names:
        if client_names[entry] == my_socket:
            return True
    return False


# invalid or unrecognized command response, used in case an unknown command or a command without the proper parameters
def invalid_command(current_socket):
    return "invalid or unrecognized command!", current_socket


# deals with the name command, assigns the client a name
def name(current_socket, client_names, data):
    # parse data to obtain one word name, all the rest is ignored
    client_name = data.split(protocol.SEPARATOR, 1)[0]
    # make sure no special characters, as defined in the protocol, are in the name
    for ch in client_name:
        if ch in protocol.SPECIAL_CHARS:
            return f"A name may not contains the following characters {protocol.SPECIAL_CHARS}", current_socket
    # confirm that no one else has taken that name already
    for entry in client_names:
        if entry == client_name:
            return f"A client with name \'{client_name}\' already exists!", current_socket
    # assign the name to the new client
    client_names[client_name] = current_socket
    return f"Hello {client_name}", current_socket


# deals with the get_names command. retrieves all users names and sends them to the user
def get_names(current_socket, client_names):
    response = ""
    for entry in client_names:
        response += entry + protocol.SEPARATOR
    return response, current_socket


# deals with the msg command. parses the data attached and sends it to the addressed user if exists
def msg(current_socket, client_names, data):
    # seperate msg data from addressee
    parsed_data = data.split(protocol.SEPARATOR, 1)
    dest_name = parsed_data[0]
    # make sure there is any data to send
    if len(parsed_data) < 2:
        return invalid_command(current_socket)

    dest_socket = None
    sender_name = None
    # find the destination socket if it exists and to save time retrieve sender's name in same loop
    for entry in client_names:
        if entry == dest_name:
            dest_socket = client_names[dest_name]
        if client_names[entry] == current_socket:
            sender_name = entry
    if dest_socket is None:
        return f"{dest_name} does not exist on the server", current_socket

    return f"{sender_name} sent {parsed_data[1]}", dest_socket


# handle a client's message to the server
def handle_client_request(current_socket, clients_names, data):
    # get the first word, ie the command
    parsed_data = data.split(protocol.SEPARATOR, 1)
    command = parsed_data[0]
    # check if our user has given himself a name
    named = is_named(current_socket, clients_names)
    # run the name command provided we havent been named already and that a name was attached
    if command == "NAME" and not named and len(parsed_data) >= 2:
        reply, dest_socket = name(current_socket, clients_names, parsed_data[1])
    # run the get_names command
    elif command == "GET_NAMES":
        reply, dest_socket = get_names(current_socket, clients_names)
    # send a message provided more data was attached and on the condition we were already named
    elif command == "MSG" and named and len(parsed_data) >= 2:
        reply, dest_socket = msg(current_socket, clients_names, parsed_data[1])
    # give an unrecognized command error
    else:
        reply, dest_socket = invalid_command(current_socket)

    return reply, dest_socket


def print_client_sockets(client_sockets):
    for c in client_sockets:
        print("\t", c.getpeername())


def main():
    print("Setting up server...")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((protocol.SERVER_IP, protocol.SERVER_PORT))
    server_socket.listen()
    print("Listening for clients...")
    client_sockets = []
    messages_to_send = []
    clients_names = {}
    while True:
        read_list = client_sockets + [server_socket]
        ready_to_read, ready_to_write, in_error = select.select(read_list, client_sockets, [])
        for current_socket in ready_to_read:
            if current_socket is server_socket:
                client_socket, client_address = server_socket.accept()
                print("Client joined!\n", client_address)
                client_sockets.append(client_socket)
                print_client_sockets(client_sockets)
            else:
                print("Data from client\n")
                # in case the user disconnects abruptly we'll catch the error and act as if the client disconnected
                # gracefully.
                try:
                    data = protocol.get_message(current_socket)
                except ConnectionResetError:
                    data = ""
                if data == "":
                    print("Connection closed\n")
                    for entry in clients_names.keys():
                        if clients_names[entry] == current_socket:
                            sender_name = entry
                            clients_names.pop(sender_name)
                            break
                    client_sockets.remove(current_socket)
                    current_socket.close()
                else:
                    print(data)
                    (response, dest_socket) = handle_client_request(current_socket, clients_names, data)
                    messages_to_send.append((dest_socket, response))

        # write to everyone (note: only ones which are free to read...)
        for message in messages_to_send:
            current_socket, data = message
            if current_socket in ready_to_write:
                response = protocol.create_msg(data)
                current_socket.send(response)
                messages_to_send.remove(message)


if __name__ == '__main__':
    main()
