import time

import grpc
import asyncio

import server_pb2
import server_pb2_grpc


async def get_connected_players(stub):
    request = server_pb2.GetConnectedPlayersRequest()
    response = await stub.GetConnectedPlayers(request)
    return response.players


async def get_replies_count(stub):
    request = server_pb2.GetRepliesCountRequest()
    response = await stub.GetRepliesCount(request)
    return response.replies_count


async def player_initialization(stub):
    current_players = await get_connected_players(stub)

    my_username = input("Enter your username: ")
    while my_username.strip() in current_players or my_username.strip() in ['mafia', 'officer', 'citizen', 'ghost', '']:
        if my_username.strip() in current_players:
            my_username = input("This username is already taken, please try again: ")
        elif my_username.strip() == '':
            my_username = input("Empty lines are not valid names! Please try again: ")
        else:
            my_username = input("Don't choose misleading names! Please try again: ")

    request = server_pb2.SetUsernameRequest(username=my_username)
    response = await stub.SetUsername(request)
    print(response.message)
    return my_username, current_players


async def subscribe_to_notifications(stub):
    request = server_pb2.SubscribeToNotificationsRequest()
    async for response in stub.SubscribeToNotifications(request):
        await asyncio.sleep(0.1)
        print(f"{response.message}", flush=True)


async def game(stub, my_username):
    players_count = len(await get_connected_players(stub))
    while players_count != 4:
        await asyncio.sleep(0.1)
        players_count = len(await get_connected_players(stub))
    await asyncio.sleep(0.75)

    print(f"\n~~~~~~~~~~~~~~~~~~\n"
          f"STARTING THE GAME!\n"
          f"~~~~~~~~~~~~~~~~~~\n")

    greeting = input(f"Hello, players! Greet each other: ")
    request = server_pb2.SendMessageRequest(username=my_username, message=greeting)
    response = await stub.SendMessage(request)

    replies_count = await get_replies_count(stub)
    while replies_count != 0:
        await asyncio.sleep(0.1)
        replies_count = await get_replies_count(stub)
    await asyncio.sleep(0.75)

    alive = await get_connected_players(stub)

    while True:
        request = server_pb2.RoleRequest(username=my_username)
        response = await stub.Role(request)
        my_role = response.message

        print(f"\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n"
              f"The night is starting, brace yourselves...\nYour role: {my_role}\n"
              f"~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")

        if my_role == 'mafia':
            print(f"Alive players: {alive}")
            choice = input("Choose your victim: ")
            while choice not in alive or choice == my_username:
                if choice not in alive:
                    choice = input("Please choose one of the still alive players: ")
                else:
                    choice = input("Noo don't kill yourself! Please try again: ")

            request = server_pb2.SendMessageRequest(username=my_role, message=choice)
            response = await stub.SendMessage(request)

        if my_role == 'officer':
            print(f"Alive players: {alive}")
            choice = input("Choose your suspect: ")

            while choice not in alive or choice == my_username:
                if choice not in alive:
                    choice = input("Please choose one of the still alive players: ")
                else:
                    choice = input("You are the officer! Please try again: ")

            request = server_pb2.SendMessageRequest(username=my_role, message=choice)
            response = await stub.SendMessage(request)

        if my_role == 'citizen' or my_role == 'ghost':
            print("Sleepy time (ᴗ_ ᴗ )")

            request = server_pb2.SendMessageRequest(username=my_role, message="sleeping")
            response = await stub.SendMessage(request)

        replies_count = await get_replies_count(stub)
        while replies_count != 0:
            await asyncio.sleep(0.1)
            replies_count = await get_replies_count(stub)
        await asyncio.sleep(0.75)

        request = server_pb2.MorningAfterRequest()
        response = await stub.MorningAfter(request)
        print(response.message)

        killed = response.message.split("'")[1]
        alive.remove(killed)
        if my_username == killed:
            my_role = 'ghost'
            my_message = 'ghost'
        else:
            my_message = input(f"Your message: ")

        request = server_pb2.SendMessageRequest(username=my_username, message=my_message)
        response = await stub.SendMessage(request)

        replies_count = await get_replies_count(stub)
        while replies_count != 0:
            await asyncio.sleep(0.1)
            replies_count = await get_replies_count(stub)
        await asyncio.sleep(0.75)

        print(f"\nAlive players: {alive}")
        if my_role == "ghost":
            print(f"Voting time! Sadly you are dead :(")
            vote = my_username
        else:
            vote = input(f"Voting time! Choose wisely: ")
            while vote not in alive or vote == my_username:
                if vote not in alive:
                    vote = input("Please choose one of the still alive players: ")
                else:
                    vote = input("You can't vote against yourself! Please try again: ")

        request = server_pb2.SendMessageRequest(username="", message=vote)
        response = await stub.SendMessage(request)

        replies_count = await get_replies_count(stub)
        while replies_count != 0:
            await asyncio.sleep(0.1)
            replies_count = await get_replies_count(stub)
        await asyncio.sleep(0.75)

        request = server_pb2.VotedRequest()
        response = await stub.Voted(request)
        print(response.message, end='')

        time.sleep(1.5)
        print(".", end='', flush=True)
        time.sleep(1.5)
        print(".", end='', flush=True)
        time.sleep(1.5)
        print(".\n\n", end='', flush=True)

        request = server_pb2.NewRequest()
        response = await stub.New(request)


async def run():
    channel = grpc.aio.insecure_channel('localhost:9000')
    stub = server_pb2_grpc.MafiaServiceStub(channel)

    my_username, current_players = await player_initialization(stub)
    print(f"Current number of players: {len(current_players) + 1}")
    if len(current_players) != 3:
        print(f"Waiting for {4 - (len(current_players) + 1)} more to join...\n")

    tasks = [subscribe_to_notifications(stub), game(stub, my_username)]
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(run())
