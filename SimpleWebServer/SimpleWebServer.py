# title:          SimpleWebServer.py
# description:    Basic Python Web Server
# author:         jmalavasi
# date:           01252021
# version:        1.0
# ==============================================================================

from encodings import utf_8
import re
import socket
import ssl
import threading
import os
import subprocess
import datetime
import json

class ParseError(BaseException):
    """ Base Exception Class for ParseRequest """
    pass

class ParseRequest:
    def __init__(self, request):
        """ Parses an HTTP request 
        
        Parameters:
            request: str, an HTTP request    
        """ 
        self.first_line_complete = False
        self.headers_complete = False
        self.method = ""
        self.uri = ""
        self.host = ""
        self.port = None
        self.query_parameters = {}
        self.version = ""
        self.headers = {}
        self.body = ""
        self.errors = 0
        self.request = request
        self.previous_element = " "
        self.status_code = "200 OK"
        try:
            self.main()
        except ParseError as e:
            self.status_code = "400 - Bad Request"
        except Exception:
            self.status_code = "500 - Internal Server Error"

    def get_method(self):
        """ Gets method from parsed request
        
        Returns:
            request method
        """    
        return self.method
    
    def get_uri(self):
        """ Gets URI from parsed request
        
        Returns:
            request URI
        """    
        return self.uri
    
    def get_version(self):
        """ Gets HTTP version from parsed request
        
        Returns:
            request version
        """    
        return self.version
    
    def get_headers(self):
        """ Gets headers from parsed request
        
        Returns:
            request headers
        """    
        return self.headers
    
    def get_host(self):
        """ Gets host from parsed uri
        
        Returns:
            request host
        """    
        return self.host
    
    def get_query_parameters(self):
        """ Gets query parameters from parsed uri
        
        Returns:
            request query parameters
        """    
        return self.query_parameters        
    
    def get_body(self):
        """ Gets body from parsed request
        
        Returns:
            request body
        """    
        return self.body

    def get_status_code(self):
        """ Gets Status Code from parsed request
        
        Returns:
            request Status Code
        """    
        return self.status_code
        
    def is_valid_method(self):
        """ Tests for valid method in request
        
        Determines if method in request is valid based on presence in 
        valid_methods list. If invalid, STATUS = 501.
        """
        valid_methods = ["GET","PUT","DELETE","POST","HEAD"]
        if self.method in valid_methods:
            return True
        else:
            self.status_code = "501 Not Implemented"
            return False
        
    def is_valid_version(self):
        """ Tests for valid HTTP version in request
        
        Determines if HTTP Version in request is valid based on presence in
        valid_versions list. If invalid, STATUS = 505
        """
        valid_versions = ["HTTP/1.0","HTTP/1.1"]
        if self.version in valid_versions:
            return True
        else:
            self.status_code = "505 HTTP Version Not Supported"
            return False
            
    def is_valid_body(self):
        """ Tests for valid Body version in request
        
        Determines if body in request is valid based on 
        length indicated in content-length header. If valid, return true.
        """
        if self.get_method() == "POST":
            if "Content-Length" in self.get_headers():
                return True
            else:
                self.status_code = "411 Length Required"
    
    def parse_first_line(self, element):
        """ Parses request line
        
        Split request line on spaces and run validation on each token.

        Parameters:
            element: str, element delimited by \\r\\n
        """
        self.method, self.uri, self.version = element.split()
        if self.is_valid_method() == False:
            self.errors += 1
        if self.is_valid_version() == False:
            self.errors += 1
        self.parse_uri()
        self.first_line_complete = True

    def parse_uri(self):
        """ Parses URI
        
        Split request line into host, port and query parameters
        """
        uri = self.get_uri()

        if ":" in uri:
            self.host = uri[:uri.find(":")]
            self.port = uri[uri.find(":")+1:uri.find("?")]
        elif "?" in uri:
            self.host = uri[:uri.find("?")]
        else:
            self.host = uri
            
        self.query_parameters = uri[uri.find("?")+1:]
        
    def parse_headers(self, element):
        """ Parses headers
        
        Split headers on first colon and run validation on each token.

        Parameters:
            element: str, element delimited by \\r\\n
        """
        
        if element != "":
            name, value = element.split(": ", maxsplit=1)
            if name in self.headers.keys():
                self.headers[name] = "{},{}".format(self.headers.get(name), value)                
            else:
                self.headers[name] = value                
        elif element == "" and self.previous_element == "":
            self.headers_complete = True
        self.previous_element = element  
            
    def parse_body(self):
        """ Parses body
        
        Pull n characters from Content-Length Header
        """
        if "Content-Length" in self.get_headers():
            self.body = self.request[-(int(self.get_headers()['Content-Length'])):]
        if self.is_valid_body() == False:
                self.errors += 1
    
    def main(self):
        """ Execute HTTP Parser
        
        Split raw data from file based on HTTP EOL in RFC2616. Parse
        each element and return appropriate status code.  Parser is based on two flags 
        first_line_complete and headers_complete.
        """
        elements = re.split("[\r\n]",self.request)
        for element in elements:
            if not self.first_line_complete:
                self.parse_first_line(element)
            elif not self.headers_complete:
                self.parse_headers(element)
            else:
                self.parse_body()
        
class SimpleWebServer:
    def __init__(self, listening_address, port, cert=None, key=None):
        """ Creates a simple HTTP Web server
        
        Parameters:
            listening_address: str, IP range to listen on
            port: int, port to run server on
            cert: str, path to public certificate
            key: str, path to private key
        """ 
        self.listening_address = listening_address
        self.port = port
        self.cert = cert
        self.key = key
        self.status_code = "200 OK"
        
        config = json.load(open('config.json'))
        self.root_directory = config['root_directory']
        self.log_level = config['log_level']
        self.log_file = "{}/SimpleWebServer-log-".format(config['log_directory'])

        if (cert != None):
            if (key != None):
                self.ssl = True
            else:
                self.log("info","Missing Private Key")
                exit()
        else:
            self.ssl = False
            
        try:
            self.main()
        except Exception:
            self.status_code = "500 - Internal Server Error"
        
    def ssl_handler(self,connection):
        # opens an SSL connection
        self.status_code = "200 OK"
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        context.load_cert_chain(certfile=self.cert,keyfile=self.key, password=None)
        s_connection = context.wrap_socket(connection,server_side=True)
        request = s_connection.recv(8192).decode()      
        s_connection.send(self.response(request).encode())
        s_connection.close()

    def basic_handler(self,connection):
        # opens a standard HTTP connection
        self.status_code = "200 OK"
        request = connection.recv(8192).decode()      
        connection.send(self.response(request).encode())
        connection.close()

    def generate_dynamic_content(self, parsed_request):
        """ Generates a dynamic page
        
        Parameters:
            parsed_request: obj, a parsed HTTP request
        Returns:
            body, str, dynamic HTTP Response
        """ 
        try:
            if parsed_request.get_method() == "GET":
                os.environ["QUERY_STRING"] = "{}".format(parsed_request.get_query_parameters())
                os.environ["SCRIPT_FILENAME"] = "{}{}".format(self.root_directory,parsed_request.get_host())
                os.environ["REQUEST_METHOD"] = "GET"
                os.environ["REDIRECT_STATUS"] = "0"
                body = (subprocess.check_output(["php-cgi", "-q"])).decode("utf-8")
                body_start_pos = body.find("\r\n\r\n") + 7
                body = body[body_start_pos:]
                
                # reset cache
                os.environ.pop("QUERY_STRING")
                os.environ.pop("SCRIPT_FILENAME")
                os.environ.pop("REQUEST_METHOD")
                os.environ.pop("REDIRECT_STATUS")
            elif parsed_request.get_method() == "POST":
                os.environ["GATEWAY_INTERFACE"] =  "CGI/1.1"
                os.environ["SCRIPT_FILENAME"] = "{}{}".format(self.root_directory,parsed_request.get_host())
                os.environ["REQUEST_METHOD"] = "POST"
                os.environ["SERVER_PROTOCOL"] = "HTTP/1.1"
                os.environ["REMOTE_HOST"] = "127.0.0.1"
                os.environ["CONTENT_TYPE"] = "application/x-www-form-urlencoded"
                os.environ["CONTENT_LENGTH"] = "{}".format(len(parsed_request.get_body()))
                body = subprocess.check_output("echo \"{}\" | php-cgi".format(parsed_request.get_body()),shell=True).decode("utf_8")
                body_start_pos = body.find("\r\n\r\n") + 7
                body = body[body_start_pos:]
                # reset cache
                os.environ.pop("GATEWAY_INTERFACE")
                os.environ.pop("SCRIPT_FILENAME")
                os.environ.pop("REQUEST_METHOD")
                os.environ.pop("REMOTE_HOST")
                os.environ.pop("SERVER_PROTOCOL")
                os.environ.pop("CONTENT_TYPE")
                os.environ.pop("CONTENT_LENGTH")
        except:
            self.status_code = "500 Internal Server Error"
        return body

    def response(self,request):
        """ Generates an HTTP response
        
        Parameters:
            request: str, a raw HTTP request

        Returns:
            response: str, a HTTP response
        """ 
        parsed_request = ParseRequest(request)
        self.log("info","Incoming Request - {}".format(request).split("\r\n")[0])
        self.log("debug","Request\n{}".format(request))
        self.log("debug","Parsed Request\nVersion: {}\nMethod: {}\nURI: {}\nHeaders: {}\nbody: {}".format(parsed_request.get_version(),parsed_request.get_method(),parsed_request.get_uri(),len(parsed_request.get_headers()),parsed_request.get_body()))

        # if put or delete complete file i/o, else retrieve resourse
        if parsed_request.get_method() == "PUT":
            try:
                f = open("{}{}".format(self.root_directory,parsed_request.get_host()),"w")
                f.write(parsed_request.get_body())
                f.close()
                body = open("{}{}".format(self.root_directory,parsed_request.get_host())).read()
                self.status_code = "201 Created"
            except PermissionError:
                self.status_code = "403 Forbidden"
                body = open("{}/403".format(self.root_directory)).read()
        elif parsed_request.get_method() == "DELETE":
            if os.path.exists("{}{}".format(self.root_directory,parsed_request.get_host())):
                os.remove("{}{}".format(self.root_directory,parsed_request.get_host()))
        else:
            try:
                if ".php" in parsed_request.get_host():
                    body = self.generate_dynamic_content(parsed_request)
                else:
                    body = open("{}{}".format(self.root_directory,parsed_request.get_host())).read()
            except (FileNotFoundError, NotADirectoryError):
                self.status_code = "404 Not Found"
                body = open("{}/404".format(self.root_directory)).read()
            except PermissionError:
                self.status_code = "403 Forbidden"
                body = open("{}/403".format(self.root_directory)).read()
            except:
                body = open("{}/index".format(self.root_directory)).read()

        # append status code to response, server errors override parse errors
        if self.status_code == "200 OK":
            response = "HTTP/1.1 {}\r\n".format(parsed_request.get_status_code())
        else:
            response = "HTTP/1.1 {}\r\n".format(self.status_code)

        # append location header to response if file is created
        if parsed_request.get_method() == "PUT":
            response += "Location: {}\r\n".format(parsed_request.get_host())

        # append headers related to body to response
        if parsed_request.get_method() == "DELETE":
            response += "Content-Length: 0" + "\r\n"
        else:
            response += "Content-Length: " + str(len(body)) + "\r\n"
        response += "Content-Type: text/html\r\n\r\n"

        # append body to response unless method is head or delete
        if parsed_request.get_method() != "HEAD" and parsed_request.get_method() != "DELETE":
            response += body + "\r\n"
        
        self.log("debug","Response\n {}".format(response))      
        return response

    def log(self, level, message):
        """ Writes to log file
        
        Parameters:
            level: str, debug or info    
            level: str, mesage to log
        """ 
        if level in self.log_level:
            f = open("{}-{}.log".format(self.log_file,datetime.datetime.now().strftime("%d-%m-%Y")),"a")
            f.writelines("[{0}] {1}: {2}\n\n".format(level,datetime.datetime.now(),message))
            f.close()            

    def main(self):
        """ Execute HTTP Server
        
        Initializes a threaded HTTP server. For educational use only.
        """
        server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        server.bind((self.listening_address,self.port))
        server.listen(5)
        
        while True:
            connection,address = server.accept()
            if self.ssl:
                thread = threading.Thread(target=self.ssl_handler(connection))
            else:
                thread = threading.Thread(target=self.basic_handler(connection))
            thread.start()