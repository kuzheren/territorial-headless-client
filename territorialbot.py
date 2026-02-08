import websocket
import time
import numpy as np
import ssl
import random
from threading import Thread

LOBBY_ADDRESS = "wss://territorial.io/i31/"

# old challenge generator, used to be in july 2024 game version
class ChallengeGeneratorOld:
    def clamp(self, db, a9S, min_value, max_value):
        return min_value + (db * a9S + 137) % (max_value - min_value)

    def generate_challenge(self, low, high):
        result = 1

        def update_result(result, low, high, i):
            base_value = 65536
            mask_value = 16383

            multiplied = result * i
            masked = multiplied & mask_value
            eZ = base_value + masked

            for j in range(eZ):
                temp = result * low
                modded = temp % high
                result = 1 + modded

            return result

        for i in range(51):
            result = update_result(result, low, high, i)

            low = self.clamp(low, result, 16384, 65536)
            high = self.clamp(high, result, 262144, 1048576)

        result = result - 1
        return result & 65535

# new challenge generator for august 2024 game version
# variable names preserved from obfuscated js
class ChallengeGenerator:
    def clamp(self, b8, a24, min_value, max_value):
        return min_value + (b8 * a24 + 137) % (max_value - min_value)

    def generate_challenge(self, aEh, aEi):
        aEk = 1
        for h in range(11):
            aEk = self._update_result(aEk, aEh, aEi, h)
            aEh = self.clamp(aEh, aEk, 16384, 65536)
            aEi = self.clamp(aEi, aEk, 1 << 18, 1 << 20)
        return (aEk - 1) & 65535

    def _update_result(self, aEk, aEh, aEi, bJ):
        aL = 65536 + ((aEk * bJ + 7) & 16383)
        for _ in range(aL):
            aEk = 1 + (aEk * aEh) % aEi
        return aEk

class Buffer:
    def __init__(self, size=None, data=None):
        self.write_offset = 0
        self.read_offset = 0

        if data == None:
            self.buffer = np.zeros(size, dtype=np.uint8)
        else:
            self.buffer = np.frombuffer(data, dtype=np.uint8)

    @staticmethod
    def calculate_array_index(bit_index, element_size):
        return bit_index // element_size

    @staticmethod
    def bits_to_bytes(bits):
        return Buffer.calculate_array_index(bits, 8) + (bits % 8 > 0 if 1 else 0)

    def write_bits(self, bits_count, value):
        for i in range(self.write_offset, self.write_offset + bits_count):
            cj = Buffer.calculate_array_index(i, 8)
            self.buffer[cj] = ((value >> bits_count - (i - self.write_offset + 1)) & 1) << 7 - i % 8 | self.buffer[cj]
        self.write_offset += bits_count

    def decode_bits(self, bits_count):
        result = 0
        for i in range(self.read_offset, self.read_offset + bits_count):
            result |= (self.buffer[self.calculate_array_index(i, 8)] >> 7 - i % 8 & 1) << self.read_offset + bits_count - i - 1
        self.read_offset += bits_count
        return int(result)

    def write_str(self, string):
        for i in range(len(string)):
            self.write_bits(16, ord(string[i]))

    def read_str(self, length):
        chars = []
        for i in range(length):
            symbol = "?"
            try:
                symbol = chr(self.decode_bits(16))
            except:
                pass
            chars.append(symbol)
        
        result = "".join(chars)
        result = result.encode("utf-16", "surrogatepass").decode("utf-16", "surrogatepass")
        return result

class Client:
    def __init__(self, nickname, game_version=1050, logging=False, proxy_options=None, lobby_address=LOBBY_ADDRESS):
        self.connected = False
        self.connection_accepted = False
        self.game_version = game_version
        self.logging = logging
        self.proxy_options = proxy_options
        self.inited = False
        self.join = False
        self.in_game = False
        self.battle_started = False
        self.nickname = nickname
        self.players_info = []
        self.mine_pos = None
        self.current_time = int(time.time() * 1000) % 1024 + random.randint(-20, 20)
        self.url = lobby_address

        self.lobby_update_callback = None
        self.disconnect_callback = None
        self.connect_callback = None
        self.game_scene_callback = None
        self.game_start_callback = None
        self.game_event_callback = None
        self.private_event_callback = None

    def start(self):
        self.connected = True

        if self.proxy_options != None:
            self.ws = websocket.create_connection(
                self.url,
                proxy_type=self.proxy_options[0],
                http_proxy_host=self.proxy_options[1],
                http_proxy_port=self.proxy_options[2],
                http_proxy_timeout=5,
                sslopt={"cert_reqs": ssl.CERT_NONE}
            )
        else:
            self.ws = websocket.create_connection(self.url, sslopt={"cert_reqs": ssl.CERT_NONE})

        self.send_init_message()
        Thread(target=self.listen).start()

    def setup_callbacks(self,
        lobby_update_callback=None,
        disconnect_callback=None,
        connect_callback=None,
        game_scene_callback=None,
        game_start_callback=None,
        game_event_callback=None,
        private_event_callback=None
    ):
        self.lobby_update_callback = lobby_update_callback
        self.disconnect_callback = disconnect_callback
        self.connect_callback = connect_callback
        self.game_scene_callback = game_scene_callback
        self.game_start_callback = game_start_callback
        self.game_event_callback = game_event_callback
        self.private_event_callback = private_event_callback

    def ping(self):
        while self.connected:
            time.sleep(15)
            self.send_ping()

    def disconnect(self):
        try:
            if self.ws != None:
                self.ws.close()
                self.connected = False
        except Exception:
            pass

    def send_data(self, data, log=""):
        if self.logging:
            print("[SENT]:", log, data)
        try:
            if self.connected:
                self.ws.send_binary(data)
        except:
            self.disconnect()

    def send_init_message(self):
        buf = Buffer(Buffer.bits_to_bytes(39))
        buf.write_bits(1, 0)
        buf.write_bits(6, 13)

        buf.write_bits(14, self.game_version)
        buf.write_bits(4, 0)
        buf.write_bits(7, 0)
        buf.write_bits(1, 0)
        buf.write_bits(1, 0)

        buf.write_bits(5, 12)

        self.send_data(list(buf.buffer), "sent init")

    def send_challenge_response(self, buf):
        challengeGenerator = ChallengeGenerator()

        x = buf.decode_bits(3)
        y1, y2 = int(buf.decode_bits(16)), int(buf.decode_bits(20))
        y = challengeGenerator.generate_challenge(y1, y2)

        send_buf = Buffer(Buffer.bits_to_bytes(26))
        send_buf.write_bits(1, 0)
        send_buf.write_bits(6, 14)
        send_buf.write_bits(3, x)
        send_buf.write_bits(16, y)

        self.send_data(list(send_buf.buffer), "sent challenge")

    def send_account_info(self):
        buf = Buffer(Buffer.bits_to_bytes(115))
        buf.write_bits(1, 0)
        buf.write_bits(6, 17)


        buf.write_bits(16, random.randint(0, 60000))
        buf.write_bits(16, random.randint(0, 60000))
        buf.write_bits(16, random.randint(0, 60000))
        buf.write_bits(16, random.randint(0, 60000))
        buf.write_bits(12, random.randint(0, 2000))

        buf.write_bits(30, random.randint(100000, 300000))

        self.send_data(list(buf.buffer), "sent acc info")

    def send_session_info(self):
        buf = Buffer(Buffer.bits_to_bytes(40 + 16 * len(self.nickname)))
        buf.write_bits(1, 0)
        buf.write_bits(6, 1)
        buf.write_bits(10, self.current_time)

        buf.write_bits(5, len(self.nickname))
        buf.write_str(self.nickname)

        # colors
        buf.write_bits(6, 0)
        buf.write_bits(6, 0)
        buf.write_bits(6, 0)

        self.send_data(list(buf.buffer), "sent session info")

    def send_join_room(self, id):
        buf = Buffer(Buffer.bits_to_bytes(11))
        buf.write_bits(1, 0)
        buf.write_bits(6, 2)
        buf.write_bits(4, id)

        self.send_data(list(buf.buffer), "sent join room")

    def send_ready_for_session(self):
        buf = Buffer(Buffer.bits_to_bytes(58))
        buf.write_bits(1, 0)
        buf.write_bits(6, 5)

        buf.write_bits(8, 0 if self.url == "wss://territorial.io/i31/" else 1)

        buf.write_bits(10, self.challengeX)
        buf.write_bits(9, self.challengeY)

        buf.write_bits(10, self.current_time)
        buf.write_bits(14, self.game_version)

        self.send_data(list(buf.buffer), "sent game start")
        Thread(target=self.ping).start()

    def send_set_base(self, pos):
        buf = Buffer(Buffer.bits_to_bytes(27))
        buf.write_bits(1, 1)
        buf.write_bits(4, 0)

        buf.write_bits(22, pos)

        self.send_data(list(buf.buffer), "set base")
    
    def send_attack(self, percentage, target):
        buf = Buffer(Buffer.bits_to_bytes(27))
        buf.write_bits(1, 1)
        buf.write_bits(4, 1)

        buf.write_bits(10, percentage)
        buf.write_bits(10, target)

        self.send_data(list(buf.buffer), "attack")

    def send_money(self, target, percentage):
        buf = Buffer(Buffer.bits_to_bytes(24))
        buf.write_bits(1, 1)
        buf.write_bits(4, 2)

        buf.write_bits(10, percentage)
        buf.write_bits(9, target)

        self.send_data(list(buf.buffer), "sent money")

    def send_clan_request(self, player):
        buf = Buffer(Buffer.bits_to_bytes(14))
        buf.write_bits(1, 1)
        buf.write_bits(4, 14)

        buf.write_bits(9, player)

        self.send_data(list(buf.buffer), "sent money")

    def send_ping(self):
        buf = Buffer(Buffer.bits_to_bytes(8))
        buf.write_bits(1, 0)
        buf.write_bits(6, 4)
        buf.write_bits(1, 0)

        self.send_data(list(buf.buffer), "sent ping")

    def send_lobby_event(self, id):
        buf = Buffer(Buffer.bits_to_bytes(13))
        buf.write_bits(1, 0)
        buf.write_bits(6, 15)
        buf.write_bits(6, id)

        self.send_data(list(buf.buffer), "sent lobby event")

    def process_message(self, msg):
        try:
            buf = Buffer(data=msg)
        except TypeError:
            self.disconnect()
            if self.disconnect_callback != None:
                # if game was not initialized before disconnect, game version is probably outdated
                outdated_version = not self.connection_accepted
                self.disconnect_callback(self, outdated_version)
            return

        if len(buf.buffer) == 0:
            pass
        else:
            if buf.decode_bits(1) == 0:
                eventId = buf.decode_bits(6)

                if self.logging:
                    print("[EVENT]:", eventId, "length:", len(buf.buffer))

                if eventId == 9:
                    self.send_challenge_response(buf)
                    if self.inited == False:
                        self.send_account_info()
                        if self.in_game == False:
                            self.send_session_info()
                        else:
                            self.send_ready_for_session()
                        self.inited = True
                elif eventId == 11:
                    subEventId = buf.decode_bits(6)
                    if subEventId == 0:
                        self.send_lobby_event(1)
                elif eventId == 2:
                    if self.connection_accepted == False:
                        self.connection_accepted = True
                        if self.connect_callback != None:
                            self.connect_callback(self)

                    playersOnlineInfo = [0, 0, 0, 0]
                    playersOnlineInfoLen = buf.decode_bits(6)
                    for i in range(4):
                        playersOnlineInfo[i] = buf.decode_bits(playersOnlineInfoLen)

                    battlesInfo = []
                    battlesCount = buf.decode_bits(4)

                    for i in range(battlesCount):
                        battlesInfo.append({
                            "id": buf.decode_bits(5),
                            "gamemode": buf.decode_bits(4),
                            "crown": buf.decode_bits(1) == 1,
                            "mapId": buf.decode_bits(6),
                            "seed": buf.decode_bits(14),
                            "players": buf.decode_bits(playersOnlineInfoLen),
                            "maxPlayers": buf.decode_bits(9) + 1,
                            "time": buf.decode_bits(10),
                        })

                        clansCount = buf.decode_bits(3)
                        clansInfo = []
                        for j in range(clansCount):
                            clansInfo.append({"online": buf.decode_bits(9) + 1, "clan": buf.read_str(buf.decode_bits(3))})
                        battlesInfo[i]["clans"] = clansInfo

                    if self.lobby_update_callback:
                        self.lobby_update_callback(self, battlesInfo)
                elif eventId == 3 or eventId == 4:
                    buf.read_offset = 1

                    x = buf.decode_bits(6)
                    index = buf.decode_bits(10)
                    self.challengeX = buf.decode_bits(10)
                    if x == 3:
                        self.challengeY = buf.decode_bits(9)
                    else:
                        self.challengeY = buf.decode_bits(1)

                    buf.read_offset = 1
                    if buf.decode_bits(6) == 3:
                        buf.read_offset += 20

                        localPlayerId = buf.decode_bits(9)
                        uY = buf.decode_bits(14)
                        ua = buf.decode_bits(4)
                        a4V = buf.decode_bits(1) == 1
                        a4W = buf.decode_bits(6)
                        a4X = buf.decode_bits(14)
                        playersCount = buf.decode_bits(9) + 1
                        playersInfo = []
                        
                        for i in range(playersCount):
                            flag = buf.decode_bits(1)
                            colors = [buf.decode_bits(6), buf.decode_bits(6), buf.decode_bits(6)]
                            nickname = buf.read_str(buf.decode_bits(5))
                            playersInfo.append({"id": i, "nickname": nickname, "flag": flag})

                        self.players_info = playersInfo
                    else:
                        pass

                    self.url = f"wss://territorial.io/i3{index}/"

                    if self.game_scene_callback != None:
                        self.game_scene_callback(self, self.players_info, self.url)

                    if self.logging:
                        print("[CONNECTED]", "Game server:", self.url, "players:", len(self.players_info))

                    self.ws.close()
                    self.ws = websocket.create_connection(self.url)

                    self.inited = False
                    self.in_game = True
                    self.send_init_message()
            else:
                buf = Buffer(data=msg)
                buf.read_offset = 2
                size = len(buf.buffer) * 8
                id = None
                sender = None
                
                try:
                    while buf.read_offset + 8 <= size:
                        id = buf.decode_bits(4)
                        sender = buf.decode_bits(9)

                        if self.game_event_callback != None:
                            self.game_event_callback(self, buf, id, sender)

                        if self.logging:
                            pass
                            # print("[GAME EVENT]", id)

                        if id == 0: # place base
                            pos = buf.decode_bits(22)
                        elif id == 1: # attack
                            if self.battle_started == False:
                                self.battle_started = True
                                if self.game_start_callback != None:
                                    self.game_start_callback(self)

                            percentage = buf.decode_bits(10)
                            target = buf.decode_bits(10)
                        elif id == 2: # send money
                            value = buf.decode_bits(10)
                            target = buf.decode_bits(9)
                        elif id == 3 or id == 4:
                            buf.decode_bits(10)
                            buf.decode_bits(22)
                        elif id == 5 or id == 6:
                            emoji = buf.decode_bits(10)
                        elif id == 7:
                            buf.decode_bits(1)
                        elif id == 9:
                            pass
                            # print("Player left", self.players_info[sender]["nickname"])
                        else:
                            pass

                except Exception as e:
                    # private message
                    try:
                        buf.read_offset = 0
                        id = buf.decode_bits(4)
                        sender = buf.decode_bits(9)
                        if self.private_event_callback != None:
                            self.private_event_callback(self, buf, id, sender)
                    except:
                        # double cringe
                        pass

                    # print("private message", id, sender)
                    # print("ERROR ON READ:", "|", e, "|", id, sender, "|", buf.read_offset, "|", list(buf.buffer))

    def listen(self):
        while self.connected:
            message = None
            try:
                message = self.ws.recv()
            except:
                self.disconnect()
                return

            self.process_message(message)
