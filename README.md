# NODE RUNNER

## Getting started

### What is RAFT consensus Algorithm ?

The RAFT consensus algorithm is a distributed consensus algorithm designed to ensure fault-tolerance in a distributed system. The algorithm is based on the concept of electing a leader among a group of nodes in a distributed system to ensure consistency and reliability.

The RAFT algorithm follows a leader-based approach, where one node is elected as the leader, and it is responsible for coordinating the operations of the other nodes in the system. The leader is chosen through an election process where each node in the system casts a vote. The node with the majority of votes becomes the leader.

RAFT ensures that the leader is always up-to-date with the latest state of the system. The leader is responsible for managing the log of all operations in the system and distributing this information to other nodes. This ensures that all nodes have access to the same information and can perform operations in a consistent manner.

One of the key advantages of the RAFT consensus algorithm is its ability to recover from failures quickly. In the event of a failure, a new leader can be elected within a few seconds, ensuring that the system remains operational.

Overall, the RAFT consensus algorithm is a robust and reliable solution for achieving consensus in a distributed system. Its simplicity and fault-tolerance make it a popular choice for developers looking to build distributed systems that require high availability and consistency.


### installing requirements

```
    pip3 install -r requirements.txt 
```

for mac:  
``` 
    brew install tmux
```
for GNU/Linux: 
``` 
    sudo apt install tmux
    yay -S tmux
```

## start the project

```
    cd src/
    # starting 5 nodes on port 5000, 5001, 5002, 5003 and 5004.
    ./start-all.sh
```


