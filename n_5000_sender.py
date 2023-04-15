from n_mach4 import *   
import requests
message = {'src_ip': nodes[0].ip, 'dest_ip': nodes[1].ip, 'data':'Hello, world!'}

nodes[0].send_message(message, nodes[1].port)

nodes[0].start_election()
