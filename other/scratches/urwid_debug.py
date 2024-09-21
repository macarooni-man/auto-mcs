from flask import Flask, render_template_string, request
import requests


# Create a webapp with Flask to send debug messages.
# On init of app:

# from urwid_debug import print, clear_debug_log
# clear_debug_log()

# the print() function is overridden from STDOUT to reporting to the webserver at localhost:5000



app = Flask(__name__)

# Store debug messages
debug_log = []

# HTML template to display the log
html_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Debug Log</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 10px; }
        .log { white-space: pre-wrap; background-color: #f5f5f5; padding: 10px; border-radius: 5px; height: 80vh; overflow-y: scroll; font-family: monospace, monospace;}
        .actions { margin-top: 10px; }
        .actions button { padding: 10px; background-color: #ff4d4d; border: none; color: white; cursor: pointer; }
        .actions button:hover { background-color: #ff1a1a; }
    </style>
    <script>
        // Auto-refresh the page every 2 seconds
        setTimeout(function(){
            window.location.reload(1);
        }, 2000);

        // Scroll to the bottom of the log
        function scrollToBottom() {
            var logDiv = document.querySelector('.log');
            logDiv.scrollTop = logDiv.scrollHeight;
        }

        // Scroll after the page has fully loaded
        window.onload = scrollToBottom;
    </script>
</head>
<body>
    <h1>Debug Log</h1>
    <div class="log">{{ log }}</div>
</body>
</html>
'''


@app.route('/')
def home():
    return render_template_string(html_template, log="\n".join(debug_log))


@app.route('/log', methods=['POST'])
def log():
    message = request.form.get('message')
    if message:
        debug_log.append(message)
    return '', 204


@app.route('/clear', methods=['POST'])
def clear_log():
    debug_log.clear()
    return '', 204


def run_server():
    app.run(debug=False, port=5000)


def print(*message):
    try:
        requests.post('http://127.0.0.1:5000/log', data={'message': ' '.join([str(i) for i in message])})
    except requests.exceptions.RequestException as e:
        print(f"Failed to send debug message: {e}")


# Function to clear the debug log via a call to the clear route
def clear_debug_log():
    try:
        requests.post('http://127.0.0.1:5000/clear')
        print("Debug log cleared.")
    except requests.exceptions.RequestException as e:
        print(f"Failed to clear debug log: {e}")


if __name__ == '__main__':
    run_server()
