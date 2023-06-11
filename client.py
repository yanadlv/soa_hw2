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
        print(f"> NOTIFICATION: {response.message}", flush=True)


async def commands_loop(stub):
    is_subscribed = False
    subscription_task = None
    while True:
        request = input()
        if request == "PLAYERS":
            await get_connected_players(stub)
            print("\nReady for the next command: QUIT / PLAYERS" +
                  (" / SUBSCRIBE" if not is_subscribed else "") + "\n")
        elif request == "SUBSCRIBE":
            is_subscribed = True
            print("\nYou are now subscribed to notifications")
            print("\nReady for the next command: QUIT / PLAYERS\n")
            if not subscription_task or subscription_task.done():
                subscription_task = asyncio.ensure_future(subscribe_to_notifications(stub))
        elif request == "QUIT":
            subscription_task.cancel()
            await quit_game(stub)
            print("Bye, hope to see you soon!")
            break
        else:
            print("\nSorry, incorrect command :(\nPlease try again\nAvailable commands: QUIT / PLAYERS" +
                  ("/ SUBSCRIBE" if not is_subscribed else "") + "\n")

        if subscription_task:
            await asyncio.sleep(0.5)


async def run():
    channel = grpc.aio.insecure_channel('localhost:9000')
    stub = server_pb2_grpc.MafiaServiceStub(channel)

    await set_username(stub)
    print("Commands PLAYERS, SUBSCRIBE, and QUIT are now available to enter at any time!\n")

    tasks = [commands_loop(stub), subscribe_to_notifications(stub)]
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(run())
