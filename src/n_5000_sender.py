from n_mach4 import *
import random
import time
import telnetlib
import requests
# message = {'src_ip': nodes[0].ip, 'dest_ip': nodes[1].ip, 'data':'Hello, world!'}

# nodes[0].send_message(message, nodes[1].port)

# nodes[0].start_election(/)
leaderP = None
i = random.randint(0,4)
for a in range(2):
    nodes[i].start_election()
leaderP = nodes[i].port
# print(nodes[i].leader_port)
# while nodes[i].leader_port != nodes[i].port:
#     nodes[i].start_election()
#     time.sleep(5)
#     print(nodes[i].leader_port)
#     if nodes[i].leader_port != None:
#         print("hi")
#         exit

while True:
    # print(leaderP)
    # print(nodes[i].leader_port)
    try:
        i = random.randint(0,4)
        nodes[i].start_election()
        time.sleep(10)
    except IndexError as e:
        print(f"{e}")

# i = random.randint(0,5)
# nodes[i].start_election()

# tn = telnetlib.Telnet()
# try:
#     tn.open("127.0.0.1", self.leader_port, timeout=2)
# except ConnectionRefusedError:
#     print(f"{port} Leader is down.")
# else:
#     print(f"{port} Leader is up.")
#     tn.close()
