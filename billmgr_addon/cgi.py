#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CGI интерфейс для плагинов
"""

import os
import sys

from billmgr_addon.utils.logging import LOGGER


def run_with_cgi(application):
    environ = dict(os.environ.items())
    environ["wsgi.input"] = sys.stdin.buffer
    environ["wsgi.errors"] = sys.stderr
    environ["wsgi.version"] = (1, 0)
    environ["wsgi.multithread"] = False
    environ["wsgi.multiprocess"] = True
    environ["wsgi.run_once"] = True

    if environ.get("HTTPS", "off") in ("on", "1"):
        environ["wsgi.url_scheme"] = "https"
    else:
        environ["wsgi.url_scheme"] = "http"

    headers_set = []
    headers_sent = []

    is_plugin_request = environ.get("EVENT_TYPE") in ["action", "before", "after"]

    def write(data):
        response_str = ""
        if not headers_set:
            raise AssertionError("write() before start_response()")

        if not is_plugin_request and not headers_sent:
            # Before the first output, send the stored headers
            status, response_headers = headers_sent[:] = headers_set
            sys.stdout.write(f"HTTP/1.1 {status}\r\n")
            for header in response_headers:
                sys.stdout.write("{}: {}\r\n".format(header[0], header[1]))
            sys.stdout.write("\r\n")

        response_body = data.decode("utf-8")
        sys.stdout.write(response_body)

    def start_response(status, response_headers, exception=None):
        if exception:
            try:
                if headers_sent:
                    # Re-raise original exception if headers sent
                    raise exception
            finally:
                exception = None  # avoid dangling circular ref
        elif headers_set:
            raise AssertionError("Headers already set!")

        headers_set[:] = [status, response_headers]
        return write

    try:
        result = application(environ, start_response)
    except Exception as e:
        LOGGER.exception(e)
        headers_set = []
        headers_sent = []
        start_response(500, [])
        write("Something went wrong".encode("utf-8"))
        quit(0)

    # result = application(environ, start_response)
    try:
        for data in result:
            if data:  # don't send headers until body appears
                write(data)
        if not headers_sent:
            write("")  # send headers now if body was empty
    finally:
        if hasattr(result, "close"):
            result.close()

    quit(0)
