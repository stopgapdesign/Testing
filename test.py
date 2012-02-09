#!/usr/bin/python

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
import MySQLdb
import urlparse
import threading, socket
from Queue import Queue

class queryThread(threading.Thread):
	def __init__(self, t):
		threading.Thread.__init__(self, target = t)
		self.db     = MySQLdb.connect('localhost', 'mindfulchange', 'shoelace1', 'mindfulchange')
		self.cursor = self.db.cursor()

class ThreadPoolMixIn(ThreadingMixIn):
    '''
    use a thread pool instead of a new thread on every request
    '''
    numThreads = 10
    allow_reuse_address = True  # seems to fix socket.error on server restart

    def serve_forever(self):
        '''
        Handle one request at a time until doomsday.
        '''
        # set up the threadpool
        self.requests = Queue(self.numThreads)

        for x in range(self.numThreads):
            t = queryThread(t = self.process_request_thread)
            t.setDaemon(1)
            t.start()

        # server main loop
        while True:
            self.handle_request()
            
        self.server_close()

    
    def process_request_thread(self):
        '''
        obtain request from queue instead of directly from server socket
        '''
        while True:
            ThreadingMixIn.process_request_thread(self, *self.requests.get())

    
    def handle_request(self):
        '''
        simply collect requests and put them on the queue for the workers.
        '''
        try:
            request, client_address = self.get_request()
        except socket.error:
            return
        if self.verify_request(request, client_address):
            self.requests.put((request, client_address))



class Handler(BaseHTTPRequestHandler):
	def do_GET(self):
		self.send_response(200)
		self.send_header("Content-type", "text/plain")
		self.end_headers()
		self.wfile.write("Hello World!\r\n")
		cursor = threading.currentThread().cursor
		cursor.execute("SELECT VERSION()")
		row = cursor.fetchone()
		self.wfile.write("MySQL server version: " + row[0] + "\r\n")

		url = urlparse.urlparse(self.path)
		params = urlparse.parse_qs(url.query)
		self.wfile.write("term: " + params.get('term', [''])[0] + "\r\n")
		self.wfile.write("thread:" + threading.currentThread().getName() + '\r\n')

class ThreadedHTTPServer(ThreadPoolMixIn, HTTPServer):
	"""Handle requests in a separate thread."""



def serve_on_port(port):
	server = ThreadedHTTPServer(('', port), Handler)
	server.serve_forever()

if __name__ == '__main__':
	serve_on_port(8080)