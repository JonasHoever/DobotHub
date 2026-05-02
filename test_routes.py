#!/usr/bin/env python3
import web_server

print("Flask app routes:")
for rule in web_server.app.url_map.iter_rules():
    print(f"  {rule.rule:40} -> {rule.endpoint}")
