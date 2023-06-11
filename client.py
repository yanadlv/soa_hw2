import grpc
import asyncio

from proto import server_pb2, server_pb2_grpc


async def set_username(stub):
    username = input("Enter your username: ")
    request = server_pb2.SetUsernameRequest(username=username)
    response = await stub.SetUsername(request)
    print(response.message)


async def quit_game(stub):
    username = input("\nEnter your username to confirm quitting: ")
    request = server_pb2.QuitRequest(username=username)
    response = await stub.QuitGame(request)
    print(response.message)


async def get_connected_players(stub):
    request = server_pb2.GetConnectedPlayersRequest()
    response = await stub.GetConnectedPlayers(request)
    print("\nCurrently connected players:")
    for player in response.players:
        print(player)


async def subscribe_to_notifications(stub):
    request = server_pb2.SubscribeToNotificationsRequest()
    responses = stub.SubscribeToNotifications(request)
    async for response in responses:
        print(f"> NOTIFICATION: {response.message}")


async def commands_loop(stub):
    task = asyncio.create_task(subscribe_to_notifications(stub))
    await asyncio.sleep(0.1)
    while True:
        request = input()
        if request == "PLAYERS":
            await get_connected_players(stub)
            print("\nReady for the next command: PLAYERS / REFRESH / QUIT\n")
        elif request == "REFRESH":
            await asyncio.sleep(0.1)
            print("\nReady for the next command: PLAYERS / REFRESH / QUIT\n")
        elif request == "QUIT":
            await quit_game(stub)
            print("Bye, hope to see you soon!")
            break
        else:
            print("\nSorry, incorrect command :(\nPlease try again\nAvailable commands: QUIT / REFRESH / PLAYERS\n")
    task.cancel()


async def run():
    channel = grpc.aio.insecure_channel('localhost:9000')
    stub = server_pb2_grpc.MafiaServiceStub(channel)

    await set_username(stub)
    print("Commands PLAYERS, REFRESH and QUIT are now available to enter at any time!\n")
    await asyncio.create_task(commands_loop(stub))


if __name__ == '__main__':
    asyncio.run(run())
