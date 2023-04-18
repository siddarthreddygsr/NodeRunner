tmux \
new-session -d -s rhtop python3 n_5000_listen.py\; \
split-window \
python3 n_5001_listner.py\; \
split-window -h \
python3 n_5002_listner.py\; \
split-window \
python3 n_5003_listner.py\; \
select-layout even-horizontal\; \
select-pane -t 0 \; \
split-window  -v \
python3 n_5004_listner.py\; \
select-pane -t 2 \; \
split-window  -v \
python3 n_5000_sender.py\; \
select-pane -t 4 \; \
split-window  -v \
htop\; \
select-pane -t 6 \; \
split-window  -v \
htop\; \