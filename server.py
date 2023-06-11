import asyncio
import threading
from concurrent import futures

import grpc

from proto import server_pb2, server_pb2_grpc


class MafiaServicer(server_pb2_grpc.MafiaServiceServicer):
    def __init__(self):
        self.connected_players = []
        self.subscribers = []
        self.notifications = []
        self.mutex = threading.Lock()

    async def SetUsername(self, request, context):
        username = request.username

        self.mutex.acquire()
        self.connected_players.append(username)
        self.notifications.append(f"{username} joined the game\n")
        print(f"LOG_INFO: {self.notifications[-1]}")
        self.mutex.release()

        response = server_pb2.SetUsernameResponse(message=f"\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n"
                                                          f"Welcome to the game, {username}!\n"
                                                          f"~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
        return response

    async def QuitGame(self, request, context):
        username = request.username

        self.mutex.acquire()
        self.connected_players.remove(username)
        self.notifications.append(f"{username} left the game\n")
        print(f"LOG_INFO: {self.notifications[-1]}")
        self.mutex.release()

        response = server_pb2.QuitResponse(message=f"\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n"
                                                   f"You successfully left the game, {username}!\n"
                                                   f"~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
        return response

    async def GetConnectedPlayers(self, request, context):
        response = server_pb2.GetConnectedPlayersResponse(players=self.connected_players)
        return response

    async def SubscribeToNotifications(self, request, context):
        notification_number = len(self.notifications)
        while True:
            await asyncio.sleep(0.5)
            while notification_number < len(self.notifications):
                notification = server_pb2.PlayerNotification(message=self.notifications[notification_number])
                yield notification
                notification_number += 1


async def run():
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    server_pb2_grpc.add_MafiaServiceServicer_to_server(MafiaServicer(), server)
    server.add_insecure_port('[::]:9000')
    await server.start()
    print("Server started...")
    await server.wait_for_termination()


if __name__ == '__main__':
    asyncio.run(run())
