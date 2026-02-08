import territorialbot

class HelperBot:
    def __init__(self, nickname, friend_name, bot_index):
        self.bot_index = bot_index
        self.bases_count = 0
        self.target = None
        self.nickname = nickname
        self.friend_name = friend_name
        self.friend_id = None
        self.has_joined_room = False
        self.have_base = False

        self.bot = territorialbot.Client(nickname, logging=False)
        self.bot.setup_callbacks(
            lobby_update_callback=self.on_lobby_update,
            game_event_callback=self.game_event_callback,
            game_scene_callback=self.game_scene_callback,
            private_event_callback=self.private_event_callback,
            disconnect_callback=self.on_disconnect
        )
        
        self.bot.start()

    def on_disconnect(self, bot, outdated):
        print(f"{self.nickname} disconnected by server")

    def on_lobby_update(self, bot:territorialbot.Client, rooms):
        if self.has_joined_room == False:
            self.has_joined_room = True
            room_id = rooms[0]["id"]
            bot.send_join_room(room_id)
            print(f"{self.nickname} joined {room_id}")

    def game_scene_callback(self, bot, players, url):
        for player in players:
            nickname = player["nickname"]
            if nickname == self.friend_name:
                self.friend_id = player["id"]
                print(f"Friend {nickname} found with id {self.friend_id}")

    def game_event_callback(self, bot, buf:territorialbot.Buffer, id, sender):
        if sender == self.friend_id:
            print("Friend event", id)
            if id == 0:
                if self.have_base == False:
                    if self.bot_index == self.bases_count:
                        self.have_base = True
                        pos = buf.decode_bits(22)
                        self.bot.send_set_base(pos)

                        print(f"Set base for {self.nickname}")

                        buf.read_offset -= 22
                self.bases_count += 1
            elif id == 1:
                percentage = buf.decode_bits(10)
                target = buf.decode_bits(10)

                print("Copy friend attack", target, percentage)

                self.attack(target, percentage)

                buf.read_offset -= 20
            elif id == 6:
                emoji = buf.decode_bits(10)

                buf.read_offset -= 10
                print("Friend set emoji", emoji)

    def private_event_callback(self, bot, buf:territorialbot.Buffer, id, sender):
        if sender != self.friend_id:
            return

        if id == 12:
            emoji = buf.decode_bits(10)
            print(f"Private emoji for {self.nickname}: {emoji}")
            if emoji == 1022: # help
                self.bot.send_money(self.friend_id, 400)
            elif emoji == 697: # copy attack
                if self.target != None:
                    self.attack(self.target, 200)
        elif id == 13:
            self.bot.send_clan_request(sender)
        elif id == 14:
            self.target = buf.decode_bits(9)
            self.attack(self.target, 100)

            print("Apply friend attack", self.target)

        print("Private event", id)

    def attack(self, target, percentage):
        self.bot.send_attack(percentage, target)

    @staticmethod
    def create_bots(amount, nick, friend_name):
        for i in range(amount):
            bot = HelperBot(f"{nick} ({i})", friend_name, i)

HelperBot.create_bots(3, "kuzheren's b0t", "kuzheren")
