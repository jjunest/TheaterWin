from django.conf.urls import url
from . import consumers


websocket_urlpatterns = [
    url(r'^ws/chatting_room/(?P<room_name>[^/]+)/$', consumers.ChatConsumer.as_asgi()),
]