import platform
import subprocess

def get_linux_distribution():
    """
    Retrieves the Linux distribution name.

    This function tries to determine the Linux distribution name by checking various sources,
    such as the '/etc/os-release' file, the 'lsb_release' command, and the '/etc/issue' file.
    If the distribution name cannot be determined, it returns 'Unknown'.

    Returns:
        str: The Linux distribution name.
    """
    try:
        with open("/etc/os-release") as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith('NAME='):
                    return line.split('=')[1].strip().strip('"')
    except IOError:
        pass

    try:
        return subprocess.check_output(["lsb_release", "-d"]).split(b":")[1].strip().decode()
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    try:
        with open("/etc/issue") as f:
            return f.readline().strip()
    except IOError:
        pass

    return "Unknown"

def get_system_info():
    """
    Get system information including OS type and distribution.

    Returns:
        str: System information.
    """
    os_type = platform.system()

    if os_type == "Linux":
        try:
            system_info = subprocess.check_output(["uname", "-a"]).decode().strip()
        except FileNotFoundError:
            system_info = "unable to fetch"

        result = f"System Information: {system_info}\n"
        result += f"Distribution: {get_linux_distribution()}"
    elif os_type == "Windows":
        system_info = platform.platform()
        result = f"System Information: {system_info}\n"
        result += "OS: Windows"
    elif os_type == "Darwin":
        system_info = subprocess.check_output(["uname", "-a"]).decode().strip()
        result = f"System Information: {system_info}\n"
        result += f"OS: macOS {platform.mac_ver()[0]}"
    elif os_type in ["FreeBSD", "NetBSD", "OpenBSD"]:
        try:
            system_info = subprocess.check_output(["uname", "-a"]).decode().strip()
        except FileNotFoundError:
            system_info = "unable to fetch"

        result = f"System Information: {system_info}\n"
        result += f"OS: {os_type} {platform.release()}"
    else:
        result = "System Information not available\nOS: Unknown"

    return result