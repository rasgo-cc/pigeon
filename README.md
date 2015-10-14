![](https://github.com/LineHealth/pigeon/blob/develop/banner.png)

![](https://github.com/LineHealth/pigeon/blob/develop/diagram.png)

## Example (Python)

### Server
```python
class Server(PigeonServer):

    def rpc_greeting(self, text):
        self.message("Hello %s!" % text, meta="hello")
        while self.ask("Do you want me to say it again?", meta="question") == "yes":
            self.message("Hello again %s!" % text, meta="hello_again")
            continue

server = Server()
server.connect("localhost", 1234)
server.run(True)
```
### Client
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
