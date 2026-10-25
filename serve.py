#!/usr/bin/env python3
"""
Simple local development server for LeetCode Company-Wise Explorer.
Serves index.html and company CSV files on localhost.
"""

import http.server
import socketserver
import webbrowser
import os
import sys

PORT = 8000

class CustomHTTPHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS and no-cache headers for easy local development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Try finding an available port
    port = PORT
    for attempt in range(10):
        try:
            with socketserver.TCPServer(("", port), CustomHTTPHandler) as httpd:
                url = f"http://localhost:{port}"
                print("=" * 60)
                print(f"🚀 LeetCode Explorer Dashboard is running at:")
                print(f"   {url}")
                print("=" * 60)
                print("Press Ctrl+C to stop the server.\n")
                
                # Open browser
                webbrowser.open(url)
                
                httpd.serve_forever()
        except OSError as e:
            if "Address already in use" in str(e) or e.errno == 98 or e.errno == 10048:
                port += 1
                continue
            else:
                raise e

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[✓] Server stopped.")
        sys.exit(0)
