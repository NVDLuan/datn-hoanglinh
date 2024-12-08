import asyncio
import json
import random

import aioredis
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings

from question.models import Question


class PvPGameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f"game_{self.room_name}"
        self.user = self.scope["user"]

        if not self.user.is_authenticated:
            await self.close()
            return

        self.redis = await aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        await self.redis.sadd(f"room:{self.room_name}:players", self.user.username)
        # thông báo đến phòng đã có người join vào
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_joined",
                "username": self.user.username,
                "message": f"{self.user.username} has joined the room."
            }
        )

    async def handle_start_game(self):
        players = await self.redis.smembers(f"room:{self.room_name}:players")
        if len(players) == 2:
            await self.redis.delete(f"room:{self.room_name}:questions")
            await self.redis.delete(f"room:{self.room_name}:answers")
            await self.start_game(players)
        else:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "There aren't enough people in the room to start playing!"
            }))

    async def get_topic_of_room(self):
        data = await self.redis.get(f"room_game:{self.room_name}")
        topics = json.loads(data).get('topics')
        time = json.loads(data).get('time')
        return topics, time

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
            await self.redis.srem(f"room:{self.room_name}:players", self.user.username)

            players = await self.redis.smembers(f"room:{self.room_name}:players")
            if len(players) == 1:
                remaining_player = list(players)[0]
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "game_over",
                        "winner": remaining_player,
                        "loser": self.user.username,
                        "reason": "opponent_left"
                    }
                )
                await self.end_game()

            elif len(players) == 0:
                await self.redis.delete(f"room:{self.room_name}:players")
                await self.redis.delete(f"room:{self.room_name}:state")
                await self.redis.delete(f"room:{self.room_name}:turn")
                await self.redis.delete(f"room:{self.room_name}:time_left")
        finally:
            await self.redis.close()

    async def start_game(self, players):

        # xóa phòng chờ
        await self.redis.delete(f"room_game:{self.room_name}")

        players = list(players)
        random.shuffle(players)
        first_player = players[0]

        topics, time = await self.get_topic_of_room()

        questions, answers = await self.get_question_in_topic(topics)

        await self.redis.rpush(f"room:{self.room_name}:questions", *questions)
        await self.redis.rpush(f"room:{self.room_name}:answers", *answers)
        # lưu chỉ số câu hỏi hiện tại
        await self.redis.set(f"room:{self.room_name}:current_question_index", 0)

        for player in players:
            await self.redis.hset(f"room:{self.room_name}:time_left", player, time)

        await self.redis.set(f"room:{self.room_name}:turn", first_player)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "game_start",
                "players": players,
                "message": f"Game started! {first_player} plays first.",
                "current_turn": first_player
            }
        )

        await self.send_question(first_player)

        # cho chạy ngầm việc đếm ngược thời gian
        asyncio.create_task(self.start_timer(first_player))

    async def question(self, event):
        """Gửi câu hỏi tới client."""
        await self.send(text_data=json.dumps({
            "type": "question",
            "question": event["question"]
        }))

    async def send_question(self, player):
        """Gửi câu hỏi hiện tại cho người chơi."""
        question_index = int(await self.redis.get(f"room:{self.room_name}:current_question_index"))
        question = await self.redis.lindex(f"room:{self.room_name}:questions", question_index)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "question",
                "player": player,
                "question": question
            }
        )

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            data = json.loads(text_data)
            action_type = data.get("action")

            if action_type == "submit":
                await self.handle_submission(data)

            if action_type == "start_game":
                await self.handle_start_game()

    async def handle_submission(self, data):
        print(self.user.username, data['answer'])
        players = await self.redis.smembers(f"room:{self.room_name}:players")
        current_turn = await self.redis.get(f"room:{self.room_name}:turn")
        question_index = int(await self.redis.get(f"room:{self.room_name}:current_question_index"))
        correct_answer = await self.redis.lindex(f"room:{self.room_name}:answers", question_index)

        if self.user.username != current_turn:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "Not your turn!"
            }))
            return

        user_answer = data.get("answer")
        print(correct_answer)
        if user_answer.lower().strip() != correct_answer.lower().strip():
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "Wrong answer! Try again."
            }))
            return

        # Lưu thời gian còn lại trước khi chuyển lượt
        time_left = await self.redis.hget(f"room:{self.room_name}:time_left", current_turn)
        await self.redis.hset(f"room:{self.room_name}:time_left", current_turn, time_left)

        opponent = [player for player in players if player != current_turn][0]

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "update_turn",
                "message": f"{self.user.username} answered correctly!",
                "correct_user": self.user.username,
                "next_turn": opponent
            }
        )
        await self.next_question()

    @database_sync_to_async
    def get_question_in_topic(self, topic):
        _questions = Question.objects.filter(topic_id__in=topic).all()
        list_question = [question.image.url for question in _questions]
        answers = [question.answer_text for question in _questions]
        return list_question, answers

    async def next_question(self):
        """Chuyển sang câu hỏi tiếp theo."""
        question_index = int(await self.redis.get(f"room:{self.room_name}:current_question_index"))
        total_questions = await self.redis.llen(f"room:{self.room_name}:questions")

        # Nếu còn câu hỏi, chuyển sang câu hỏi tiếp theo
        if question_index + 1 < total_questions:
            await self.redis.incr(f"room:{self.room_name}:current_question_index")
            players = await self.redis.smembers(f"room:{self.room_name}:players")
            current_turn = await self.redis.get(f"room:{self.room_name}:turn")
            next_player = [p for p in players if p != current_turn][0]

            # Gửi câu hỏi tiếp theo
            await self.send_question(next_player)

            # Chuyển lượt
            await self.redis.set(f"room:{self.room_name}:turn", next_player)
            asyncio.create_task(self.start_timer(next_player))
        else:
            # Hết câu hỏi => kết thúc game
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "game_over",
                    "winner": "Draw",  # Hoặc logic khác để xác định người thắng
                    "reason": "No more questions"
                }
            )
            await self.end_game()

    async def start_timer(self, player):
        """Tiếp tục đếm ngược thời gian còn lại cho người chơi."""
        time_left = int(await self.redis.hget(f"room:{self.room_name}:time_left", player))

        for _ in range(time_left):
            await asyncio.sleep(1)
            current_turn = await self.redis.get(f"room:{self.room_name}:turn")
            if current_turn != player:
                # Nếu lượt chơi thay đổi, dừng đếm ngược
                return

            time_left -= 1
            await self.redis.hset(f"room:{self.room_name}:time_left", player, time_left)

            if time_left == 0:
                # Hết thời gian
                await self.timeout_player(player)
                return

    async def timeout_player(self, player):
        players = await self.redis.smembers(f"room:{self.room_name}:players")
        opponent = [p for p in players if p != player][0]

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "game_over",
                "winner": opponent,
                "loser": player,
                "reason": "timeout"
            }
        )

        # Lấy danh sách user trong phòng
        # players = await self.redis.smembers(f"room:{self.room_name}:players")
        # # for player in players:
        #     # Tự động ngắt kết nối user
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        await self.close()

        await self.end_game()

    async def game_start(self, event):
        await self.send(text_data=json.dumps({
            "type": "start",
            "players": event["players"],
            "message": event["message"],
            "current_turn": event["current_turn"]
        }))

    async def update_turn(self, event):
        await self.send(text_data=json.dumps({
            "type": "turn",
            "message": event["message"],
            "correct_user": event["correct_user"],
            "next_turn": event["next_turn"]
        }))

    async def game_over(self, event):
        await self.send(text_data=json.dumps({
            "type": "end",
            "winner": event.get("winner", None),
            "loser": event.get("loser", None),
            "reason": event.get("reason")
        }))

    async def end_game(self):
        await self.redis.delete(f"room:{self.room_name}:players")
        await self.redis.delete(f"room:{self.room_name}:state")
        await self.redis.delete(f"room:{self.room_name}:turn")
        await self.redis.delete(f"room:{self.room_name}:time_left")
        await self.redis.delete(f"room:{self.room_name}:questions")
        await self.redis.delete(f"room:{self.room_name}:answers")

    async def user_joined(self, event):
        """Thông báo khi một user mới tham gia."""
        await self.send(text_data=json.dumps({
            "type": "user_joined",
            "username": event["username"],
            "message": event["message"]
        }))


class ExaminerGameConsumer(PvPGameConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f"game_{self.room_name}"
        self.user = self.scope["user"]

        if not self.user.is_authenticated:
            await self.close()
            return

        self.redis = await aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        await self.redis.sadd(f"room:{self.room_name}:players", self.user.username)
        # thông báo đến phòng đã có người join vào
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_joined",
                "username": self.user.username,
                "message": f"{self.user.username} has joined the room."
            }
        )
