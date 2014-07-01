from gnshelpers import *


@match_event(host="foo")
def on_event(event):
    if int(event['service']) % 100 == 0:
        email.send_event("alexanderk@yandex-team.ru", event)
