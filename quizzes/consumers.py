import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import QuizAttempt, QuizSession


class RoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.group_name = f"room_{self.room_id}"

        if not self.user.is_authenticated:
            await self.close()
            return

        has_access = await self.check_access()
        if not has_access:
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        await self.set_status("in_progress")
        await self.send_participants_to_group()

    async def disconnect(self, code):
        if not self.user.is_authenticated:
            return

        await self.set_status("left")
        await self.send_participants_to_group()
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_participants_to_group(self):
        participants = await self.get_participants()
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "participants_update",
                "participants": participants,
            }
        )

    async def participants_update(self, event):
        await self.send(text_data=json.dumps({
            "action": "participants",
            "participants": event["participants"],
        }))

    @database_sync_to_async
    def set_status(self, status):
        student = getattr(self.user, "profile_student", None)
        if student is None:
            return

        QuizAttempt.objects.filter(session_id=self.room_id, student=student).update(status=status)

    @database_sync_to_async
    def get_participants(self):
        attempts = QuizAttempt.objects.filter(session_id=self.room_id,status="in_progress").select_related("student__user")

        participants = []
        for attempt in attempts:
            participants.append({
                "id": attempt.student.id,
                "name": attempt.student.user.full_name,
            })

        return participants

    @database_sync_to_async
    def check_access(self):
        room = QuizSession.objects.filter(id=self.room_id).first()

        if room is None:
            return False

        if self.user.is_superuser:
            return True

        mentor = getattr(self.user, "profile_mentor", None)
        if mentor is not None and room.mentor_id == mentor.id:
            return True

        student = getattr(self.user, "profile_student", None)
        if student is not None:
            return QuizAttempt.objects.filter(session=room, student=student).exists()

        return False