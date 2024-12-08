from django.urls import re_path

from play_game import consumers

websocket_urlpatterns = [
    re_path(r'ws/game/(?P<room_name>\w+)/$', consumers.PvPGameConsumer.as_asgi()),
]
