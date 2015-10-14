from pigeon.client import PigeonClient

class App(PigeonClient):

    def handle_message(self, message):
        meta = message["meta"]
        text = message["text"]
        print("%20s | %s" % (meta, text))

app = App()
app.connect("localhost", 1234)

print("Type your name: ")
text = raw_input()
app.send_data("greeting text=%s" % text)

while True:
    reply_text = raw_input()
    app.send_data("reply text=%s" % reply_text)

    if reply_text != "yes":
        break

app.disconnect()
