from Raft import RaftNode
from typing import List

# define a list of IP addresses for the nodes
node_ips: List[str] = ['127.0.0.1']
# node_ips: List[str] = ['10.243.111.4']
# create a list to store the nodes
nodes: List[RaftNode] = []
node_ports: List[str] = ['5000', '5001', '5002', '5003', '5004']

# create a node for each IP address
for port in node_ports:
    node = RaftNode('127.0.0.1', port,  node_ports, 10, 20, 5)
    nodes.append(node)

# for node in nodes:
#     node.run()
# print("Nope")
# nodes[0].run()
# # print("fuck Me")
# nodes[1].run()
# # print("No you")

# message = {'src_ip': nodes[0].id, 'dest_ip': nodes[1].id, 'data':'Hello, world!'}
# nodes[0].send_message(message, nodes[1].port)
