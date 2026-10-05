import urllib.error
import urllib.request

print("Sending GET request to Windows Helper at /next...")

try:
    response = urllib.request.urlopen("http://localhost:8000/next")
    print(f"Server responded with status code: {response.status}")
except urllib.error.URLError as e:
    print(f"Failed to connect: {e.reason}")
