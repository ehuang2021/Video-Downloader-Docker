from flask import Flask, request, render_template, send_from_directory, session, redirect, url_for
from manage_download import download_file
import subprocess
import os
import threading
import time
import json
from werkzeug.middleware.proxy_fix import ProxyFix

# SessionObject class, used for tracking multiple sessions:
class SessionObject:



    def __init__(self, user_ID):
        self.user_id = user_ID
        self.downloaded_files = []
        self.user_path = os.path.join(DOWNLOAD_PATH, self.user_id)
        self.download_type = "video" # Default download settings
        self.download_quality = "best"
        os.makedirs(self.user_path, exist_ok=True) # Create directory to store all of users data


    def add_file(self, filename):
        # Adds the file to user's session list
        self.downloaded_files.append(filename)

    def get_files(self):
        # Gets list of downloaded files
        return self.downloaded_files
    
    def delete_files(self):
        # Deletes the session data
        if os.path.exists(self.user_path):
            # Loop and delete all files within user folder
            for file in os.listdir(self.user_path):
                os.remove(os.path.join(self.user_path, file))
            os.rmdir(self.user_path)
        self.downloaded_files = []


    def to_dict(self):
        # Turns itself into a dictionary for storage within session object
        return {
            "user_id": self.user_id,
            "downloaded_files": self.downloaded_files,
            "download_type" : self.download_type,
            "download_quality" : self.download_quality
        }
    
    @staticmethod
    def from_dict(data):
        # Rebuilds Session Object from Dictionary
        session_obj = SessionObject(data["user_id"])
        session_obj.downloaded_files = data.get("downloaded_files")
        session_obj.download_type = data.get("download_type")
        session_obj.download_quality = data.get("download_quality")
        return session_obj

def get_client_ip():
    # Gets client's real IP
    if "X-Forwarded-For" in request.headers:
        # X-Forwarded-For is a comma-separated list of IPs; the first one is the client's IP
        # Triggers when server is behind reverse proxy
        return request.headers["X-Forwarded-For"].split(",")[0].strip()
    
    return request.remote_addr  # Fallback to remote_addr if no header is present.
                                # Reverse Proxy not correct, or server not reverse proxied
def save_session_object(session_obj):
    # Saves the session object to flask session
    session["session_obj"] = json.dumps(session_obj.to_dict())

def get_session_object():
    # Gets the session object from flask session
    if "session_obj" in session:
        return SessionObject.from_dict(json.loads(session["session_obj"]))

    # If session_obj doesn't exist (new user), it will create a new object
    user_id = str(hash(request.remote_addr+ str(time.time())))
    session_obj = SessionObject(user_id)
    save_session_object(session_obj)
    return session_obj

# Import config file
with open("config.json") as f:
    globalConfig = json.load(f)


app = Flask(__name__)
SESSION_TIMEOUT = globalConfig["SESSION_TIMEOUT"] # 5 mins
DOWNLOAD_PATH = globalConfig["DOWNLOAD_PATH"]  # Directory to store downloaded files
app.secret_key = globalConfig["SECRET_KEY"] # Encryption key for local client-side cookie

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1) # Keeps IP after nginx reverse proxy


cleanup_timers = {}

@app.route('/')
def index():
    session_obj = get_session_object()
    reset_timer(session_obj.user_id) # Resets the timeout timer
    current_download_type = session_obj.download_type 
    return render_template('index.html', files=session_obj.get_files(), current_option=current_download_type)

@app.route('/download', methods=['POST'])
def download():
    session_obj = get_session_object()
    url = request.form.get('url')
    if not url:
        # If no URL is provided, display an error message
        return render_template('index.html', messages="No URL provided.", files=session_obj.get_files())

    try:
        download_file(url, session_obj.user_path, session_obj.download_type) # Execute the yt-dip.sh script with the provided URL
         # can fix output maybe with different params
        try:
            titleResult = subprocess.run(['./get.filename.sh', url, session_obj.download_type], capture_output=True, text=True, check=True)
            filename = titleResult.stdout.strip()
            session_obj.add_file(filename) # Add file name to obj file list
            save_session_object(session_obj)
            message = f"Download successful: {filename} "
            make_logs("download","download.txt", url, filename)
        except subprocess.CalledProcessError as e:
            message = f"Something went wrong"
        
    except subprocess.CalledProcessError as e:
        # If the script fails, capture the error message
        messagePreCleaned = e.stderr.strip()
        message = "ERROR: " + error_management(messagePreCleaned)

    return render_template('index.html', message=message, files=session_obj.get_files())

@app.route('/files/<filename>')
def serve_file(filename):
    # Serve the requested file as a downloadable attachment
    return send_from_directory(get_session_object().user_path, filename, as_attachment=True)

@app.route('/set_option', methods=['POST'])
def download_options():
    session_obj = get_session_object()
    session_obj.download_type = request.form.get('download_type')

    save_session_object(session_obj)
    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    session_obj = get_session_object()
    delete_user_files(session_obj)
    session.clear()
    return redirect(url_for('index'))


def reset_timer(user_id):
    # Resets inactivity timer for user, or creates new one
    if user_id in cleanup_timers:
        cleanup_timers[user_id].cancel()
    
    def cleanup_user_files(user_id):
        session_obj = SessionObject(user_id) # Recreates SessionObject due to timer thread not being able to 
                                             # access main thread. This is ok beacuse of how delete_files() works
        delete_user_files(session_obj)

    # Starts new timer
    timer = threading.Timer(SESSION_TIMEOUT, cleanup_user_files, args=(user_id, ))
    cleanup_timers[user_id] = timer
    timer.start()

def delete_user_files(session_obj: SessionObject):
    # Deletes all files, and cancels inactivity timer
    session_obj.delete_files()
    userID = session_obj.user_id
    if userID in cleanup_timers:
        cleanup_timers[userID].cancel()
        del cleanup_timers[userID]

# Centeralizes possible errors
def error_management(message):
    if "is not a valid URL" in message:
        return "Invalid URL"
    else:
        return message
    
def make_logs(log, file, url=None, name=None):
    DIRECTORY = "./logs"

    filePath = os.path.join(DIRECTORY, file)
    openFile = open(filePath, "a")
    # LOG FACTORY
    if log == "download":
        stringToWrite = request.headers.get('User-Agent') + "   " + name + "  " + url + "\n"
        openFile.write(stringToWrite)
    openFile.close


if __name__ == '__main__':
    # Ensure the downloads directory exists
    os.makedirs(DOWNLOAD_PATH, exist_ok=True)
    # Run the Flask app on all network interfaces on port 5000
    app.run(host='0.0.0.0', port=4999)