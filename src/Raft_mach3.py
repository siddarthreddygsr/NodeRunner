from fastapi import FastAPI, Request
import requests
import json
import threading
import random

app = FastAPI()


class RaftNode:
    def _init_(self, ip, port,  peers, election_timeout_min, election_timeout_max, heartbeat_interval):
        self.ip = ip
        self.port = port
        self.peers = peers
        self.election_timeout_min = election_timeout_min
        self.election_timeout_max = election_timeout_max
        self.heartbeat_interval = heartbeat_interval
        self.current_term = 0
        self.voted_for = None
        self.log = []
        self.commit_index = 0
        self.last_applied = 0
        self.state = "follower"
        self.leader_port = None
        self.next_index = {peer: len(self.log) for peer in self.peers}
        self.match_index = {peer: 0 for peer in self.peers}
        self.election_timer = None
        self.heartbeat_timer = None
        self.vote_count = 0

    def send_message(self, message, dest_port):
        payload = {
            "src_port": self.port,
            "message": message
        }
        headers = {
            "Content-Type": "application/json"
        }
        dest_ip = '127.0.0.1'
        response = requests.post(f"http://{dest_ip}:{dest_port}/message", headers=headers, json=payload)
        if response.status_code != 200:
            print(f"Error sending message to {dest_port}. Response status code: {response.status_code}")
        else:
            print(f"Message sent to {dest_port}")

    async def handle_message(self, message):
        try:
            print("message")
            print(message["type"])
            if message["type"] == "request_vote":
                self.handle_request_vote(message)
            elif message["type"] == "request_vote_response":
                self.handle_request_vote_response(message)
            elif message["type"] == "append_entries":
                self.handle_append_entries(message)
            elif message["type"] == "append_entries_response":
                self.handle_append_entries_response(message)
        except:
            print(f"Received unknown message type: {message}\n")
            return {"status": "error", "message": f"Unknown message type: {message}"}

    async def receive_message(self, request: Request):
        message = await request.json()
        src_port = message['src_port']
        message = message['message']
        print(f"Received message from {src_port}: {message}")
        await self.handle_message(message)
        return {"status": "OK"}

    @app.post('/appendEntries')
    async def append_entries_endpoint(self, request: Request):
        message = await request.json()
        src_port = message['src_port']
        message = message['message']
        print(f"Received appendEntries message from {src_port}: {message}")
        await self.handle_append_entries(message)
        return {"status": "OK"}
    def listen(self):
        @app.post('/message')
        async def endpoint(request: Request):
            response = await self.receive_message(request)
            return response

        import uvicorn
        uvicorn.run(app, host=self.ip, port=self.port)


    def start_election_timer(self):
        self.election_timer = threading.Timer(random.uniform(self.election_timeout_min, self.election_timeout_max), self.start_election)
        self.election_timer.start()

    def cancel_election_timer(self):
        if self.election_timer:
            self.election_timer.cancel()
            self.election_timer = None

    def start_heartbeat_timer(self):
        self.heartbeat_timer = threading.Timer(self.heartbeat_interval, self.send_heartbeat)
        self.heartbeat_timer.start()

    def cancel_heartbeat_timer(self):
        if self.heartbeat_timer:
            self.heartbeat_timer.cancel()
            self.heartbeat_timer = None

    def start_election(self):
        print(f"Node {self.port}: Starting election")
        self.current_term += 1
        self.state = "candidate"
        self.voted_for = self.port
        self.cancel_election_timer()
        self.start_election_timer()
        self.request_votes()

    def request_votes(self):
        print(f"Node {self.port}: Requesting votes")
        self.vote_count = 1
        for peer in self.peers:
            if peer == self.port:
                continue
            message = {
                "src_port": self.port,
                "dst_port": peer,
                "type": "request_vote",
                "term": self.current_term,
                "last_log_index": len(self.log) - 1,
                "last_log_term": self.log[-1]["term"] if self.log else 0
            }
            self.send_message(message, peer)

    def handle_request_vote(self, message):
        print("sending response")
        response = {
            "src_port": self.port,
            "dst_port": message["src_port"],
            "type": "request_vote_response",
            "term": self.current_term,
            "vote_granted": False
        }
        if message["term"] < self.current_term:
            # Deny vote if candidate term is less than current term
            self.send_message(response, message["src_port"])
            return
        if self.voted_for is None or self.voted_for == message["src_port"]:
            # Grant vote if we haven't voted or if we have already voted for this candidate
            if self.log[-1]["term"] <= message["last_log_term"] and len(self.log) - 1 <= message["last_log_index"]:
                # Grant vote if candidate's log is at least as up-to-date as our log
                response["vote_granted"] = True
                print("Yes! Voted True")
                self.voted_for = message["src_port"]
        self.send_message(response, message["src_port"])

    
    def handle_request_vote_response(self, message):
        # Check if the response is for the current term
        print(message['term'])
        print(self.current_term)
        if message['term'] != self.current_term:
            return
        candidate_id = message['src_port']
        if candidate_id not in self.peers:
            return

        if candidate_id in self.voted_for:
            return
        print(message)
        if message["vote_granted"]:
            print("vote_granted")
            self.vote_count += 1
            print(self.vote_count)
            if self.vote_count > len(self.peers) // 2:
                self.state = "leader"
                self.leader_port = self.port
                self.cancel_election_timer()
                self.start_heartbeat_timer()
                self.send_append_entries()


    def send_append_entries(self):
        for peer in self.peers:
            if peer == self.port:
                continue
            prev_log_index = self.next_index[peer] - 1
            prev_log_term = self.log[prev_log_index]["term"] if prev_log_index >= 0 else 0
            entries = self.log[self.next_index[peer]:]
            message = {
                "src_port": self.port,
                "dst_port": peer,
                "type": "append_entries",
                "term": self.current_term,
                "prev_log_index": prev_log_index,
                "prev_log_term": prev_log_term,
                "entries": entries,
                "leader_commit": self.commit_index
            }
            self.send_message(message, peer)
    @app.route('/executeCommand', methods=['POST'])
    def my_endpoint():
        data = requests.json
        return {'status': 'success'}, 200
    
    def handle_append_entries(self, message):
        response = {
            "src_port": self.port,
            "dst_port": message["src_port"],
            "type": "append_entries_response",
            "term": self.current_term,
            "success": False
        }
        if message["term"] < self.current_term:
            # Deny append entries if leader term is less than current term
            self.send_message(response, message["src_port"])
            return
        if len(self.log) <= message["prev_log_index"] or self.log[message["prev_log_index"]]["term"] != message["prev_log_term"]:
            # Deny append entries if previous log doesn't match
            self.send_message(response, message["src_port"])
            return
        self.cancel_election_timer()
        self.start_election_timer()
        self.state = "follower"
        self.leader_port = message["src_port"]
        self.commit_index = min(message["leader_commit"], len(self.log) - 1)
        if len(message["entries"]) > 0:
            self.log = self.log[:message["prev_log_index"] + 1] + message["entries"]
        self.send_message(response, message["src_port"])

    def handle_append_entries_response(self, message):
        if message["term"] != self.current_term:
            return
        if message["success"]:
            self.match_index[message["src_port"]] = len(self.log) - 1
            self.next_index[message["src_port"]] = len(self.log)
            self.vote_count = sum([1 for peer in self.peers if self.match_index[peer] >= self.commit_index and peer != self.port])
            if self.vote_count > len(self.peers) // 2:
                self.commit_index += 1
        else:
            self.next_index[message["src_port"]] -= 1
        self.cancel_election_timer()
        self.start_election_timer()

    def send_heartbeat(self):
        for peer in self.peers:
            if peer == self.port:
                continue
            message = {
                "src_port": self.port,
                "dst_port": peer,
                "type": "heartbeat",
                "term": self.current_term,
                "leader_commit": self.commit_index
            }
            self.send_message(message, peer)

    def handle_heartbeat(self, message):
        if message["term"] < self.current_term:
            # Deny heartbeat if leader term is less than current term
            return
        self.cancel_election_timer()
        self.start_election_timer()
        self.leader_port = message["src_port"]
        self.commit_index = min(message["leader_commit"], len(self.log) - 1)