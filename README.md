![](https://github.com/LineHealth/pigeon/blob/develop/banner.png)

Separating business logic from the user interface is great. It not only separates the code, it allows you to develop each part of your software using different tools which should be the most approriate ones for the task. But ending with two applications, say, the command-line (CLI) application and the graphical user interface (GUI), also means you need to create a communication channel between them so they operate together.

**Pigeon** allows you to do that in a very straight forward way, using very **simple concepts** on top of a **client-server architecture**.

![](https://github.com/LineHealth/pigeon/blob/develop/diagram.png)

Pigeon in six steps:

1. PigeonServer sends data to PigeonClients in JSON format
2. The only possible data sent by PigeonServer: <code>messages</code>
3. Messages are JSON objects with only two elements: <code>text</code> and <code>metadata</code>. Text is the message's text, metadata may be a text label so the message's purpose can be easily identified by a PigeonClient.
4. PigeonServer can <code>ask</code> questions: it waits for a <code>reply</code> after sending a <code>message</code>
5. PigeonClient can <code>call</code> functions/methods declared on a PigeonServer
6. PigeonClient sends data to a PigeonServer in serial format (just plain text terminated with <code>\r\n</code>, indicating the function/method's name and its (named) arguments)

#### Bindings

At the moment, Pigeon offers tools only for Python, but it should be easily implemented in other languages.

Python installation:
```
git clone https://github.com/LineHealth/pigeon
cd pigeon/python
python setup.py install
```

#### Example (Python)

##### Server
```python
class Server(PigeonServer):

    def rpc_greeting(self, text):
        self.message("Hello %s!" % text, meta="hello")
        while self.ask("Do you want me to say it again?", meta="question") == "yes":
            self.message("Hello again %s!" % text, meta="hello_again")

server = Server()
server.connect("localhost", 1234)
server.run(True)
```
##### Client
```python
class Client(PigeonClient):

    def handle_message(self, message):
        meta = message["meta"]
        text = message["text"]
        print("%20s | %s" % (meta, text))

client = Client()
client.connect("localhost", 1234)

print("Type your name: ")
text = raw_input()
client.send_data("greeting text=%s" % text)

while True:
    reply_text = raw_input()
    client.send_data("reply text=%s" % reply_text)

    if reply_text != "yes":
        break

client.disconnect()
```
