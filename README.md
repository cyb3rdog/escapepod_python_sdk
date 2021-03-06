# EscapePod Extension SDK for Python
#### by cyb3rdog

This is the EscapePod Python SDK for Cyb3rVector's EscapePod Extension Proxy.

With this SDK, you can:
- maintain all your EscapePod intents from Python code
- dynamically create new extension intents from code
- react to and override all Vector's voice commands, including those created on the fly
- and more...


## Getting Started

1) Use of this SDK assumes some familiarity and experience with Vector Python SDK, as well as ownership of the Anki/DDL Vector and DDL EscapePod.

2) In order to use this SDK to its full potential, it is recommended to have also the [vector-python-sdk](https://github.com/cyb3rdog/vector-python-sdk) installed,
as at this moment, this is the only Vector Python SDK, which can be used with your EscapePod onboarded Vector.

3) This SDK requires the Cyb3rVector Extension Proxy service to be deployed and configured to use with your EscapePod [see the **deployment** guide](deployment/)


## EscapePod SDK Installation

 - Note: Use either **```pip```** or **```pip3```** correspondingly to the Python version you are using.

To install this SDK, run:

- ```pip install escapepod_sdk``` or ```pip3 install escapepod_sdk```

To upgrade this SDK to its latest version, use:

- ```pip install escapepod_sdk --upgrade``` or ```pip3 install escapepod_sdk --upgrade```


If you want to know where the SDK files are installed, use following command:

- Windows:  ```py -c "import escapepod_sdk as _; print(_.__path__)"```
- Linux:    ```python3 -c "import escapepod_sdk as _; print(_.__path__)"```


## Extension Deployement

#### **Please see the [deployment guide here](deployment/)**.
EscapePod Extension Proxy itself, and its source code is maintained in separate repository: [cyb3rdog/escape-pod-proxy](https://github.com/cyb3rdog/escape-pod-proxy).


## Tutorials

To learn how to this SDK, start with tutorial example programs in the [examples](examples/) folder.


## Logging

In order to change the log level to other then default value of `INFO`, set the `SDK_LOG_LEVEL` enviroment variable:

Allowed values are:
```
CRITICAL	= 50
FATAL 		= CRITICAL
ERROR 		= 40
WARNING 	= 30
WARN 		= WARNING
INFO 		= 20
DEBUG 		= 10
```

Example:

- Windows: ```SET SDK_LOG_LEVEL=DEBUG```
- Lunux:   ```SDK_LOG_LEVEL="DEBUG"```
