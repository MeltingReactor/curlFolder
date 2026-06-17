import getopt
import os
import sys
import subprocess
import shutil
import time
import tarfile
import zipfile

# Configuration
VERSION = "1.0.0"
SETUP_DIR = os.path.expanduser("~/.setup")
LOCK_FILE = os.path.join(SETUP_DIR, "running.lock")
LOCK_TIMEOUT = 30  # Maximum seconds to wait for a lock file


def show_help():
    print("""
Usage: curlFolder <url> [OPTIONS]

Options:
  -h, --help           Show this help message and exit.
  -v, --version        Show version information and exit.
  -q, --quiet          Enable quiet mode (suppress output).
  -e, --extract        Automatically unpack zip, tar, tar.gz, or tgz archives.
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


def download_with_curl(url, quiet_mode=False):
    """Invokes curl and saves the output file into ~/.setup/"""
    filename = url.split("/")[-1] or "download.out"
    output_path = os.path.join(SETUP_DIR, filename)

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


def check_lock(quiet_mode=False):
    """Checks for a lock file and automatically times out after 30 seconds."""
    os.makedirs(SETUP_DIR, exist_ok=True)
    start_time = time.time()

    while os.path.isfile(LOCK_FILE):
        elapsed_time = time.time() - start_time
        if elapsed_time >= LOCK_TIMEOUT:
            if not quiet_mode:
                print(f"\nTimeout: Lock file has been active for over {LOCK_TIMEOUT} seconds.")
                print("Overriding lock and continuing execution...")
            # Break the loop to overwrite the stale lock file
            break

        if not quiet_mode:
            # Print a clean, updating countdown timer on the same line
            remaining = int(LOCK_TIMEOUT - elapsed_time)
            print(f"\rWaiting for another instance to finish... ({remaining}s remaining)", end="", flush=True)

        time.sleep(1)

    if not quiet_mode and os.path.isfile(LOCK_FILE):
        print()  # Add a newline if we printed a countdown status

    # Create the lock file and store current process ID
    try:
        with open(LOCK_FILE, "w") as f:
            f.write(str(os.getpid()))
    except Exception as e:
        print(f"Error: Could not write lock file: {e}")
        sys.exit(1)


def extract_archive(file_path, quiet_mode=False):
    """Unpacks supported archive formats natively into ~/.setup/"""
    if not os.path.isfile(file_path):
        return

    if not quiet_mode:
        print(f"Checking {file_path} for extraction...")

    try:
        # Handle zip files
        if file_path.endswith(".zip"):
            if not quiet_mode:
                print("Extracting ZIP archive...")
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(SETUP_DIR)

        # Handle tar files (.tar, .tar.gz, .tgz)
        elif file_path.endswith((".tar", ".tar.gz", ".tgz")):
            if not quiet_mode:
                print("Extracting TAR archive...")
            with tarfile.open(file_path, 'r:*') as tar_ref:
                tar_ref.extractall(SETUP_DIR)

        else:
            if not quiet_mode:
                print("Notice: File format not supported for native extraction. Skipping.")

    except Exception as e:
        print(f"Error during archive extraction: {e}")


def finish_folder():
    """Removes the locking file cleanly."""
    try:
        if os.path.isfile(LOCK_FILE):
            os.remove(LOCK_FILE)
    except OSError as e:
        print(f"Warning: Could not remove lock file: {e}")


def main():
    args = sys.argv[1:]
    quiet_mode = False
    extract_mode = False

    if not args:
        print(f"curlFolder v{VERSION}")
        print("Hint: Use '-h' or '--help' to see the full list of available options.")
        print("Usage: curlFolder <url> [OPTIONS]")
        sys.exit(0)

    # Added 'e' / 'extract' to the available option lists
    options = "hvqe"
    long_options = ["help", "version", "quiet", "extract"]

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

        if not values:
            print("Error: Missing mandatory <url> argument.")
            print("Usage: curlFolder <url> [OPTIONS]")
            sys.exit(1)

        target_url = values[0]

        # Execution Lifecycle
        ensure_curl_installed(quiet_mode)
        check_lock(quiet_mode)

        try:
            if not quiet_mode:
                print(f"Target: {target_url}")

            # Run download download
            downloaded_file = download_with_curl(target_url, quiet_mode)

            # Unpack the file if extraction option was flagged
            if extract_mode and downloaded_file:
                extract_archive(downloaded_file, quiet_mode)

        finally:
            finish_folder()

    except getopt.error as err:
        print(f"Error: {str(err)}")
        show_help()
        sys.exit(2)

if __name__ == "__main__":
    main()
