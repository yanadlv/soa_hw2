import grpc
from random import randint
import asyncio
import threading
from concurrent import futures

import server_pb2
import server_pb2_grpc


class MafiaServicer(server_pb2_grpc.MafiaServiceServicer):
    def __init__(self):
        self.mutex = threading.Lock()
        self.notifications = []
        self.connected_players = []
        self.subscribers = []
        self.roles = {}
        self.mafia = ''
        self.roles_left = ['mafia', 'officer', 'citizen', 'citizen']
        self.replies_count = 0
        self.last_kill = ''
        self.last_accusation = ''
        self.correct_votes = 0

    async def GetConnectedPlayers(self, request, context):
        response = server_pb2.GetConnectedPlayersResponse(players=self.connected_players)
        return response

    async def GetRepliesCount(self, request, context):
        response = server_pb2.GetRepliesCountResponse(replies_count=self.replies_count)
        return response

    async def SetUsername(self, request, context):
        username = request.username

        self.mutex.acquire()
        self.connected_players.append(username)
        self.notifications.append(f"> NOTIFICATION: {username} joined the game")
        print(f"LOG_INFO: {username} joined the game")
        self.mutex.release()

        response = server_pb2.SetUsernameResponse(message=f"\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n"
                                                          f"Welcome to the game, {username}!\n"
                                                          f"~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
        return response

    async def SubscribeToNotifications(self, request, context):
        notification_number = len(self.notifications)
        while True:
            await asyncio.sleep(0.1)
            while notification_number < len(self.notifications):
                notification = server_pb2.PlayerNotification(message=self.notifications[notification_number])
                yield notification
                notification_number += 1

    async def Role(self, request, context):
        self.mutex.acquire()
        assign_role = randint(0, len(self.roles_left) - 1)
        if self.roles_left[assign_role] == 'mafia':
            self.mafia = request.username
        self.roles[request.username] = self.roles_left[assign_role]
        self.roles_left.pop(assign_role)
        self.mutex.release()

        response = server_pb2.RoleResponse(message=self.roles[request.username])
        return response

    async def SendMessage(self, request, context):
        self.replies_count += 1
        self.replies_count %= 4

        if request.username not in ['mafia', 'officer', 'citizen', 'ghost', '']:
            if request.username not in self.roles or self.roles[request.username] != 'ghost':
                message = request.message
            else:
                message = "boo im a ghost"
            self.notifications.append("> " + request.username + ": " + message)
        elif request.username == 'mafia':
            self.last_kill = request.message
            self.roles[request.message] = 'ghost'
        elif request.username == 'officer':
            self.last_accusation = request.message
        elif request.username == '':
            if self.roles[request.message] == 'mafia':
                self.correct_votes += 1

        response = server_pb2.SendMessageResponse(message="")
        return response

    async def MorningAfter(self, request, context):
        bound = f"\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n"
        greeting = f"Good morning everyone!\n"
        result_mafia = (f"\nThis night '{self.last_kill}' got killed. They are now a ghost. "
                        f"They will not be able to write messages.\n")
        result_officer = f"\nThe officer guessed... "
        if self.roles[self.last_accusation] == 'mafia':
            result_officer += "Right.\n"
        else:
            result_officer += "Wrong.\n"
        discussion = "\nPlease discuss the night! You will then vote."

        message = bound + greeting + result_mafia + result_officer + discussion + bound
        response = server_pb2.MorningAfterResponse(message=message)
        return response

    async def Voted(self, request, context):
        bound = f"\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n"
        if self.correct_votes == 2:
            result = "MAFIA LOST!"
        else:
            result = "MAFIA WON!"
        message = f"The votes were counted... " + result
        reveal = f"\n'{self.mafia}' was the mafia\n"
        ending = f"\nCongratulations and thank you for playing!"
        new_game = f"\nStarting new game"

        message = bound + message + reveal + ending + bound + new_game
        response = server_pb2.VotedResponse(message=message)
        return response

    async def New(self, request, context):
        self.roles = {}
        self.mafia = ''
        self.roles_left = ['mafia', 'officer', 'citizen', 'citizen']
        self.replies_count = 0
        self.last_kill = ''
        self.last_accusation = ''
        self.correct_votes = 0
        response = server_pb2.NewResponse(message="cool")
        return response


async def run():
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    server_pb2_grpc.add_MafiaServiceServicer_to_server(MafiaServicer(), server)
    server.add_insecure_port('[::]:9000')
    await server.start()
    print("Server started...")
    await server.wait_for_termination()


if __name__ == '__main__':
    asyncio.run(run())
