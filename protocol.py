SERVER_PORT = 7777
SERVER_IP = "0.0.0.0"

# represented with the factor 10^(MAX_LENGTH-1)-1
MAX_LENGTH = 4


# saved in protocol so that all users can know what characters are allowed in a name
SPECIAL_CHARS = "!@#$%^&*()-_=+|[]{};:/?.\\"

# protocol-wide character that represents the separator in between a command and parameters
SEPARATOR = " "


# protocol-wide function to format all messages sent over the protocol, using the idea of max length
def create_msg(data):
    length = str(len(data))
    # if the message is too long we'll only send the first 10^(MAX_LENGTH-1)-1 digits
    if len(length) > MAX_LENGTH:
        data = data[:10 ** (MAX_LENGTH - 1) - 1]
    return (length.zfill(MAX_LENGTH) + data).encode()


# using the idea of max length we'll retrieve the exact message without dealing with blocking
def get_message(my_socket):
    message_length = my_socket.recv(MAX_LENGTH).decode()
    # in case "" was sent
    if message_length != "":
        return my_socket.recv(int(message_length)).decode()
    # return empty string
    return message_length
