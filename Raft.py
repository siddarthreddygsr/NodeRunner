from flask import Flask, request
import requests
import json
import threading
import random

app = Flask(__name__)


class RaftNode:
    def __init__(self, ip, port,  peers, election_timeout_min, election_timeout_max, heartbeat_interval):
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
        self.leader_ip = None
        self.next_index = {peer: len(self.log) for peer in self.peers}
        self.match_index = {peer: 0 for peer in self.peers}
        self.election_timer = None
        self.heartbeat_timer = None

    def send_message(self, message, dest_port):
        payload = {
            "src_ip": self.ip,
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

    def listen(self):
        @app.route('/message', methods=['POST'])
        def receive_message():
            message = request.get_json()['message']
            src_ip = request.get_json()['src_ip']
            print(f"Received message from {src_ip}: {message}")
            self.handle_message(message)
            return "OK", 200
        
        app.run(host=self.ip, port=self.port,debug=True)


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
        print(f"Node {self.ip}: Starting election")
        self.current_term += 1
        self.state = "candidate"
        self.voted_for = self.ip
        self.cancel_election_timer()
        self.start_election_timer()
        self.request_votes()

    def request_votes(self):
        print(f"Node {self.ip}: Requesting votes")
        num_votes = 1
        for peer in self.peers:
            if peer == self.port:
                continue
            message = {
                "src_ip": self.ip,
                "dst_ip": peer,
                "type": "request_vote",
                "term": self.current_term,
                "last_log_index": len(self.log) - 1,
                "last_log_term": self.log[-1]["term"] if self.log else 0
            }
            self.send_message(message, peer)

    def handle_request_vote(self, message):
        response = {
            "src_ip": self.ip,
            "dst_ip": message["src_ip"],
            "type": "vote",
            "term": self.current_term,
            "vote_granted": False
        }
        if message["term"] < self.current_term:
            # Deny vote if candidate term is less than current term
            self.send_message(response, message["src_ip"])
            return
        if self.voted_for is None or self.voted_for == message["src_ip"]:
            # Grant vote if we haven't voted or if we have already voted for this candidate
            if self.log[-1]["term"] <= message["last_log_term"] and len(self.log) - 1 <= message["last_log_index"]:
                # Grant vote if candidate's log is at least as up-to-date as our log
                response["vote_granted"] = True
                self.voted_for = message["src_ip"]
        self.send_message(response, message["src_ip"])

    def handle_vote(self, message):
        if message["term"] != self.current_term:
            return
        if message["vote_granted"]:
            num_votes = sum([1 for peer in self.peers if self.match_index[peer] >= self.commit_index and peer != self.port])
            if num_votes > len(self.peers) // 2:
                self.state = "leader"
                self.leader_ip = self.ip
                self.cancel_election_timer()
                self.start_heartbeat_timer()
                self.send_append_entries()
    
    def handle_request_vote_response(self, message):
        # Check if the response is for the current term
        if message['term'] != self.current_term:
            return

        # Check if the response is from a valid candidate
        candidate_id = message['from']
        if candidate_id not in self.peers:
            return

        # Check if the candidate has already voted in this term
        if candidate_id in self.voted_for:
            return

        # Check if the candidate has granted its vote
        if message['vote_granted']:
            self.vote_count += 1
            if self.vote_count > len(self.peers) // 2:
                # The node has received enough votes to become leader
                self.become_leader()
        else:
            # The candidate did not grant its vote
            pass  # Handle the case where a candidate did not grant its vote


    def send_append_entries(self):
        for peer in self.peers:
            if peer == self.ip:
                continue
            prev_log_index = self.next_index[peer] - 1
            prev_log_term = self.log[prev_log_index]["term"] if prev_log_index >= 0 else 0
            entries = self.log[self.next_index[peer]:]
            message = {
                "src_ip": self.ip,
                "dst_ip": peer,
                "type": "append_entries",
                "term": self.current_term,
                "prev_log_index": prev_log_index,
                "prev_log_term": prev_log_term,
                "entries": entries,
                "leader_commit": self.commit_index
            }
            self.send_message(message, peer)


    def handle_message(self, message):
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

    def handle_append_entries(self, message):
        response = {
            "src_ip": self.ip,
            "dst_ip": message["src_ip"],
            "type": "append_entries_response",
            "term": self.current_term,
            "success": False
        }
        if message["term"] < self.current_term:
            # Deny append entries if leader term is less than current term
            self.send_message(response, message["src_ip"])
            return
        if len(self.log) <= message["prev_log_index"] or self.log[message["prev_log_index"]]["term"] != message["prev_log_term"]:
            # Deny append entries if previous log doesn't match
            self.send_message(response, message["src_ip"])
            return
        self.cancel_election_timer()
        self.start_election_timer()
        self.state = "follower"
        self.leader_ip = message["src_ip"]
        self.commit_index = min(message["leader_commit"], len(self.log) - 1)
        if len(message["entries"]) > 0:
            self.log = self.log[:message["prev_log_index"] + 1] + message["entries"]
        self.send_message(response, message["src_ip"])

    def handle_append_entries_response(self, message):
        if message["term"] != self.current_term:
            return
        if message["success"]:
            self.match_index[message["src_ip"]] = len(self.log) - 1
            self.next_index[message["src_ip"]] = len(self.log)
            num_votes = sum([1 for peer in self.peers if self.match_index[peer] >= self.commit_index and peer != self.ip])
            if num_votes > len(self.peers) // 2:
                self.commit_index += 1
        else:
            self.next_index[message["src_ip"]] -= 1
        self.cancel_election_timer()
        self.start_election_timer()

    def send_heartbeat(self):
        for peer in self.peers:
            if peer == self.ip:
                continue
            message = {
                "src_ip": self.ip,
                "dst_ip": peer,
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
        self.leader_ip = message["src_ip"]
        self.commit_index = min(message["leader_commit"], len(self.log) - 1)

    def run(self):
        self.start_election_timer()
        self.listen()