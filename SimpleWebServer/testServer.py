import sys
from SimpleWebServer import SimpleWebServer

test = sys.argv[1]

if test == "http":
    # HTTP Server without SSL
    server = SimpleWebServer("localhost",80)
elif test == "https":
    # HTTP Server with SSL
    server = SimpleWebServer("localhost",443,"ssl/test.crt","ssl/test.key")
elif test == "https-no-cert":
    # Missing private key
    server = SimpleWebServer("localhost",443,"ssl/test.crt")