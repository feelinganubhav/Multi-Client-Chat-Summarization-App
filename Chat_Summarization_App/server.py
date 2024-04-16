import socket
import threading
from transformers import pipeline


# Connection Data
host = ''
port = 55555


# Load the summarization pipeline
summarizer = pipeline("summarization", model="lidiya/bart-large-xsum-samsum")

# Starting Server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

print("\nServer is Listening...")

# Lists For Clients and Their Nicknames
clients = []
nicknames = []
dialogue_history = []  # To store all dialogues

# Sending Messages To All Connected Clients
def broadcast(message):
    for client in clients:
        client.send(message)

# Handling Messages From Clients
def handle(client):
    while True:
        try:
            # Receiving Message
            message = client.recv(1024)
            if message:
                # Split message into name and text
                name, text = message.decode('ascii').split(': ', 1)
                print(f"{name}: {text}")  # Print Name: Message to server
                broadcast(message)  # Broadcast message to all clients
                if text.startswith("/summarize"):
                    summarize_dialogue(client)  # Summarize dialogue if requested
                else:
                    dialogue_history.append(message.decode('ascii'))  # Add dialogue to history
        except:
            # Removing And Closing Clients
            index = clients.index(client)
            clients.remove(client)
            client.close()
            nickname = nicknames[index]
            broadcast('{} left!'.format(nickname).encode('ascii'))
            nicknames.remove(nickname)
            if not clients:
                summarize_dialogue_end()  # Summarize dialogue at the end of the chat..
            break

# Function to summarize the entire dialogue using Google Natural Language API
def summarize_dialogue(client):
    if len(dialogue_history) < 1:
        response = "No dialogue to summarize."
    else:
        # Concatenate all dialogues into a single string
        all_text = '\n'.join(dialogue_history)
        # Call the Natural Language API to summarize the text
        response = summarizer(all_text, max_length=100, min_length=10, do_sample=False)[0]['summary_text']

    print("Summary:", response)
    # Broadcast summary message to the client
    client.send(f"Summary: {response}".encode('ascii'))

# Function to summarize the entire dialogue using Google Natural Language API
def summarize_dialogue_end():
    if len(dialogue_history) < 1:
        response = "No dialogue to summarize."
    else:
        # Concatenate all dialogues into a single string
        all_text = '\n'.join(dialogue_history)
        # Call the Natural Language API to summarize the text
        response = summarizer(all_text, max_length=300, min_length=100, do_sample=False)[0]['summary_text']

    print("Summary:", response)
    # # Broadcast summary message to the client
    # client.send(f"Summary: {response}".encode('ascii'))

# Receiving / Listening Function
def receive():
    while True:
        # Accept Connection
        client, address = server.accept()
        print("Connected with {}".format(str(address)))

        # Request And Store Nickname
        client.send('NAME'.encode('ascii'))
        nickname = client.recv(1024).decode('ascii')
        nicknames.append(nickname)
        clients.append(client)

        # Print And Broadcast Nickname
        print("Nickname is {}".format(nickname))
        broadcast("{} joined!".format(nickname).encode('ascii'))
        client.send('Connected to server!'.encode('ascii'))

        # Start Handling Thread For Client
        thread = threading.Thread(target=handle, args=(client,))
        thread.start()

# Start the receiving function
receive()
