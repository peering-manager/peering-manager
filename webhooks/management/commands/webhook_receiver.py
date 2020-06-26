import sys

from django.core.management.base import BaseCommand
from http.server import HTTPServer, BaseHTTPRequestHandler


request_counter = 1


class WebhookHandler(BaseHTTPRequestHandler):
    show_headers = True

    def __getattr__(self, item):
        """
        Returns the same method ignoring the HTTP request type.
        """
        if item.startswith("do_"):
            return self.do_ANY
        raise AttributeError

    def log_message(self, format_str, *args):
        global request_counter
        print(
            f"[{request_counter}] {self.date_time_string()} {self.address_string()} {format_str % args}"
        )

    def do_ANY(self):
        global request_counter

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Webhook received!\n")

        request_counter += 1

        for k, v in self.headers.items():
            print(f"{k}: {v}")
        print()

        content_length = self.headers.get("Content-Length")
        if content_length is not None:
            body = self.rfile.read(int(content_length))
            print(body.decode("utf-8"))
        else:
            print("(No body)")

        print("------------")


class Command(BaseCommand):
    help = "Starts a basic listener that displays received HTTP requests"
    default_port = 9000

    def add_arguments(self, parser):
        parser.add_argument(
            "--port",
            type=int,
            default=self.default_port,
            help=f"Optional port number (default: {self.default_port})",
        )

    def handle(self, *args, **options):
        port = options["port"]

        self.stdout.write(
            f"Listening on port http://localhost:{port}. Stop with CTRL+C."
        )
        httpd = HTTPServer(("localhost", port), WebhookHandler)

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            self.stdout.write("\nExiting...")
