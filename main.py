import getopt
import os
import sys
import subprocess
import shutil
import time
import tarfile
import zipfile
import stat

# Configuration
VERSION = "1.1.0"
DEFAULT_SETUP_DIR = os.path.expanduser("~/.setup")
LOCK_TIMEOUT = 30  # Maximum seconds to wait for a lock file


def show_help():
    print("""
Usage: curlFolder <url> [OPTIONS]

Options:
  -h, --help               Show this help message and exit.
  -v, --version            Show version information and exit.
  -q, --quiet              Enable quiet mode (suppress output).
  -e, --extract            Unpack archives, clean up source, and make scripts executable.
  -o, --override-path <dir> Change target directory from ~/.setup to a custom path.
""")


def ensure_curl_installed(quiet_mode=False):
    """Checks if curl is installed; if not, attempts to install it."""
    if shutil.which("curl") is not None:
        return

    if not quiet_mode:
        print("Warning: 'curl' is not installed. Attempting auto-installation...")

    if sys.platform.startswith("linux"):
        if shutil.which("apt-get"):
            cmd = "sudo apt-get update && sudo apt-get install -y curl"
        elif shutil.which("dnf"):
            cmd = "sudo dnf install -y curl"
        elif shutil.which("pacman"):
            cmd = "sudo pacman -S --noconfirm curl"
        else:
            print("Error: Unsupported Linux distribution. Please install 'curl' manually.")
            sys.exit(1)
            
    elif sys.platform == "darwin":
        if shutil.which("brew"):
            cmd = "brew install curl"
        else:
            print("Error: Homebrew required to install curl on macOS. Install manually.")
            sys.exit(1)
    else:
        print(f"Error: Unsupported operating system ({sys.platform}). Install curl manually.")
        sys.exit(1)

    try:
        subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL if quiet_mode else None)
        if not quiet_mode:
            print("Successfully installed 'curl'.")
    except subprocess.CalledProcessError as e:
        print(f"Error: Installation failed (code {e.returncode}). Run with sudo or install manually.")
        sys.exit(1)


def download_with_curl(url, target_dir, quiet_mode=False):
    """Invokes curl and saves the output file into the chosen directory."""
    filename = url.split("/")[-1] or "download.out"
    output_path = os.path.join(target_dir, filename)

    cmd = ["curl", "-L", "-o", output_path]
    if quiet_mode:
        cmd.append("-s")

    cmd.append(url)

    if not quiet_mode:
        print(f"Downloading {url} -> {output_path}...")

    try:
        subprocess.run(cmd, check=True)
        if not quiet_mode:
            print("Download completed successfully.")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"Error: Curl failed with exit code {e.returncode}")
        sys.exit(1)


def check_lock(lock_file, target_dir, quiet_mode=False):
    """Checks for a lock file and automatically times out after 30 seconds."""
    os.makedirs(target_dir, exist_ok=True)
    start_time = time.time()
    
    while os.path.isfile(lock_file):
        elapsed_time = time.time() - start_time
        if elapsed_time >= LOCK_TIMEOUT:
            if not quiet_mode:
                print(f"\nTimeout: Lock file has been active for over {LOCK_TIMEOUT} seconds.")
                print("Overriding lock and continuing execution...")
            break
            
        if not quiet_mode:
            remaining = int(LOCK_TIMEOUT - elapsed_time)
            print(f"\rWaiting for another instance to finish... ({remaining}s remaining)", end="", flush=True)
        
        time.sleep(1)

    if not quiet_mode and os.path.isfile(lock_file):
        print()

    try:
        with open(lock_file, "w") as f:
            f.write(str(os.getpid()))
    except Exception as e:
        print(f"Error: Could not write lock file: {e}")
        sys.exit(1)


def make_scripts_executable(directory, quiet_mode=False):
    """Recursively finds .sh files in the target directory and runs chmod +x on them."""
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".sh"):
                file_path = os.path.join(root, file)
                try:
                    st = os.stat(file_path)
                    os.chmod(file_path, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                    if not quiet_mode:
                        print(f"Made executable: {file_path}")
                except OSError as e:
                    print(f"Warning: Could not make {file_path} executable: {e}")


def extract_archive(file_path, target_dir, quiet_mode=False):
    """Unpacks archives into target_dir, runs script permissions, and deletes the source archive."""
    if not os.path.isfile(file_path):
        return

    extracted = False
    try:
        if file_path.endswith(".zip"):
            if not quiet_mode:
                print("Extracting ZIP archive...")
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(target_dir)
            extracted = True
            
        elif file_path.endswith((".tar", ".tar.gz", ".tgz")):
            if not quiet_mode:
                print("Extracting TAR archive...")
            with tarfile.open(file_path, 'r:*') as tar_ref:
                tar_ref.extractall(target_dir)
            extracted = True
                
        else:
            if not quiet_mode:
                print("Notice: File format not supported for native extraction. Skipping.")
                
        if extracted:
            make_scripts_executable(target_dir, quiet_mode)
            os.remove(file_path)
            if not quiet_mode:
                print(f"Cleaned up source archive: {os.path.basename(file_path)}")
                
    except Exception as e:
        print(f"Error during archive extraction or cleanup: {e}")


def finish_folder(lock_file):
    """Removes the locking file cleanly."""
    try:
        if os.path.isfile(lock_file):
            os.remove(lock_file)
    except OSError as e:
        print(f"Warning: Could not remove lock file: {e}")


def main():
    args = sys.argv[1:]
    quiet_mode = False
    extract_mode = False
    target_dir = DEFAULT_SETUP_DIR  # Default fallback path

    if not args:
        print(f"curlFolder v{VERSION}")
        print("Hint: Use '-h' or '--help' to see the full list of available options.")
        print("Usage: curlFolder <url> [OPTIONS]")
        sys.exit(0)

    # Added 'o:' to options and 'override-path=' to long_options to accept a string argument
    options = "hvqeo:"
    long_options = ["help", "version", "quiet", "extract", "override-path="]

    try:
        arguments, values = getopt.gnu_getopt(args, options, long_options)

        for currentArg, currentVal in arguments:
            if currentArg in ("-h", "--help"):
                show_help()
                sys.exit(0)
            elif currentArg in ("-v", "--version"):
                print("curlFolder v" + VERSION)
                sys.exit(0)
            elif currentArg in ("-q", "--quiet"):
                quiet_mode = True
            elif currentArg in ("-e", "--extract"):
                extract_mode = True
            elif currentArg in ("-o", "--override-path"):
                # Expand absolute / tilde paths safely
                target_dir = os.path.abspath(os.path.expanduser(currentVal))

        if not values:
            print("Error: Missing mandatory <url> argument.")
            print("Usage: curlFolder <url> [OPTIONS]")
            sys.exit(1)

        target_url = values[0]
        
        # Dynamically evaluate lock file location based on chosen target path
        lock_file = os.path.join(target_dir, "running.lock")

        # Execution Lifecycle
        ensure_curl_installed(quiet_mode)
        check_lock(lock_file, target_dir, quiet_mode)
        
        try:
            if not quiet_mode:
                print(f"Target URL: {target_url}")
                print(f"Destination: {target_dir}")
            
            downloaded_file = download_with_curl(target_url, target_dir, quiet_mode)
            
            if extract_mode and downloaded_file:
                extract_archive(downloaded_file, target_dir, quiet_mode)
                
        finally:
            finish_folder(lock_file)

    except getopt.error as err:
        print(f"Error: {str(err)}")
        show_help()
        sys.exit(2)

if __name__ == "__main__":
    main()
