# EscapePod Extension Proxy Deployment 
#### ***by cyb3rdog***

EscapePod Extension Proxy itself, and its source code is maintained in separate repository [cyb3rdog/escape-pod-proxy](https://github.com/cyb3rdog/escape-pod-proxy).

## Deployment Guide

### A) Automatic, from the Cyb3rVector application:

The [Cyb3rVector](https://cyb3rdog.github.io/Cyb3rVector) application contains automatic mechanism for deployment of this Extension proxy to the EscapePod server.


### B) Manual, to your EscapePod:

This section describes how to deploy the Cyb3rVector EscapePod Extension Proxy service to your EscapePod.
In this scenario, Extension Proxy will be hosted on same IP address as your EscapePod software, and connections from EscapePod to Extension Proxy and from Extension Proxy to MongoDB will all be done locally.

1. Make sure you've added the following lines to your escapepod config (in ```/etc/escape-pod.conf```)
```sh
ENABLE_EXTENSIONS=true
ESCAPEPOD_EXTENDER_TARGET=127.0.0.1:8089
ESCAPEPOD_EXTENDER_DISABLE_TLS=true
```

2. [Download](cybervector-proxy_1.0.0_linux_x64.zip), unzip and deploy the ```cybervector-proxy``` all binary to your escape pod (i.e */usr/local/escapepod/bin/*)
3. Create service, to run the binary during EscapePod boot with all the enviroment varibles initialized ([example service here](https://github.com/cyb3rdog/escape-pod-proxy/blob/Cyb3rPod/Resources/cybervector-proxy.service))
4. Reload and restart the services / or your Escape-Pod
```
sudo systemctl daemon-reload
sudo systemctl enable cybervector-proxy
sudo systemctl start cybervector-proxy
```


### C) Manual, to Windows:

In this scenario, the Extension Proxy will run on different host than on your EscapePod.

1. Make sure you've added the following lines to your escapepod config (in ```/etc/escape-pod.conf```), where XX.XX.XX.XX is an IP address of the windows machine where the Extension Proxy will run:
```sh
ENABLE_EXTENSIONS=true
ESCAPEPOD_EXTENDER_TARGET=XX.XX.XX.XX:8089
ESCAPEPOD_EXTENDER_DISABLE_TLS=true
```

2. Change the MongoDB binding adress to 0.0.0.0 to expose its port to your local network (in /etc/mongod.conf)
```sh
# network interfaces
net:
  port: 27017
  bindIp: 0.0.0.0
```

3. Restart the services / or your Escape-Pod
```
sudo systemctl restart mongod
sudo systemctl restart escape_pod
```

4. [Download](cybervector-proxy_1.0.0_win_x64.zip), unzip and run your Extension Proxy on Windows.
5. Enable the *cybervector-proxy* program on your windows firewall
