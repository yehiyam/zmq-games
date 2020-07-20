# 0MQ games

* create venv
```shell
virtualenv ~/envs/zmq -p /usr/bin/python3.7
```
* install
```shell
pip install -r requirements.txt
```

### one client
run in multiple terminals
```shell
python clientStandalone.py
python server.py
python server.py
python server.py
python server.py
```

server options (envs)
WORK_TIME_MS: sleep time in milliseconds (simulates work)
CLIENT_ADDRESS: in the form of `tcp://localhost:5556`. to support running on multiple machines/dockers

client options (envs)
DATA_SIZE: data payload size in bytes

### multiple clients
WIP
```shell
python clientMulty.py
```