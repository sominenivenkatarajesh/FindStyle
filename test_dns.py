import socket

host = "db.vxcfjanjzvlfvjqeqazg.supabase.co"
try:
    addr_info = socket.getaddrinfo(host, 5432)
    print(f"Addresses for {host}:")
    for info in addr_info:
        print(info)
except Exception as e:
    print(f"Error resolving {host}: {e}")
