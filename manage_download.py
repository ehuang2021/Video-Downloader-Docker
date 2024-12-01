import subprocess

def download_file(url, filepath, download_type="video", download_quality="best"):
    
    
    subprocess.run(['./yt.dip.sh', url, filepath, download_type, download_quality], capture_output=True, text=True, check=True)
