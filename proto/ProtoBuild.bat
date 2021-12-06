REM pip install grpcio grpclib protobuf

protoc -I./cybervector --python_out ./cybervector cybervector_proxy.proto
protoc -I./cybervector --python_grpc_out ./cybervector cybervector_proxy.proto --plugin=grpc_python_plugin
