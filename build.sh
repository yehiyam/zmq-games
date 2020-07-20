VER=v0.0.2
docker build -t yehiyam/zmqserver:$VER -f server.Dockerfile  .
docker push yehiyam/zmqserver:$VER
docker build -t yehiyam/zmqclient:$VER -f client.Dockerfile  .
docker push yehiyam/zmqclient:$VER
