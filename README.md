# SimpleWebServer

SimpleWebServer is a basic HTTP/HTTPS server that supports server side execution. It was designed for educational purposes and is vulnerable to many common
HTTP exploits such as SQL Injection, Shell Injection and Directory Traversal. Not for use in production environments.

## Usage
Example 1: HTTP
```python
python3 testServer.py http
```

Example 2: HTTPS
```python
python3 testServer.py https
```

Example 3: HTTPS without a private key
```python
python3 testServer.py https-no-cert
```

## Config
The config file (config.json) can be used to set:

root_directory: str, The location of pages to serve, default="pages"

log_directory: str, The location of log files, default="logs"

log_level: array, The verbosity of logging, info or debug, default="info"

## Author
Jeff Malavasi

CSEC 731 Project B
