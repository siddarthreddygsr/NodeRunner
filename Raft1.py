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
            print(f"Message sent to {dest_ip}")

    def listen(self):
        @app.route('/message', methods=['POST'])
        def receive_message():
            message = request.get_json()['message']
            src_ip = request.get_json()['src_ip']
            print(f"Received message from {src_ip}: {message}")
            self.handle_message(message)
            return "OK", 200
        
        app.run(host=self.ip, port=self.port,debug=True)