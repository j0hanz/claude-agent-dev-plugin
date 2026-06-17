import os
import json
import time
import sys
import argparse
from pathlib import Path

# Detect PROJECT_ROOT relative to this script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BLACKBOARD_FILE = PROJECT_ROOT / ".agent_blackboard.json"
LOCK_FILE = BLACKBOARD_FILE.with_suffix(".json.lock")

STALE_LOCK_SECONDS = 60


def _pid_is_alive(pid):
    """
    Best-effort liveness check for a PID, cross-platform.
    Returns True if the process appears to be alive, False if it is
    definitely gone, and True (fail-safe) if liveness can't be determined.
    """
    if pid is None:
        return True
    if sys.platform == "win32":
        try:
            import ctypes

            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            handle = ctypes.windll.kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION, False, pid
            )
            if not handle:
                return False
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        except Exception:
            return True
    else:
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except (PermissionError, OSError):
            return True


def _read_lock_holder():
    """
    Returns (pid, mtime) for the current lock file, or (None, None) if it
    can't be read (e.g. it was removed concurrently).
    """
    try:
        mtime = LOCK_FILE.stat().st_mtime
        content = LOCK_FILE.read_text(encoding="utf-8").strip()
        pid = int(content) if content.isdigit() else None
        return pid, mtime
    except (FileNotFoundError, ValueError, OSError):
        return None, None


def _break_stale_lock():
    """
    Removes the lock file if its holder is stale: either the PID is no
    longer alive, or the lock has existed longer than STALE_LOCK_SECONDS.
    """
    pid, mtime = _read_lock_holder()
    if mtime is None:
        return
    age = time.time() - mtime
    if age < STALE_LOCK_SECONDS and _pid_is_alive(pid):
        return
    try:
        LOCK_FILE.unlink()
    except (FileNotFoundError, PermissionError, OSError):
        pass


def acquire_lock(timeout=10, retry_interval=0.05):
    """
    Acquire a lock using a lock file.
    Uses os.O_EXCL for atomic creation on Windows and Linux.
    A lock held by a dead process, or older than STALE_LOCK_SECONDS, is
    treated as abandoned and reclaimed instead of blocking forever.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # os.O_CREAT | os.O_EXCL ensures atomicity
            fd = os.open(str(LOCK_FILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            try:
                os.write(fd, str(os.getpid()).encode("utf-8"))
            finally:
                os.close(fd)
            return True
        except FileExistsError:
            _break_stale_lock()
            time.sleep(retry_interval)
        except PermissionError:
            # On Windows, sometimes PermissionError is raised if the file is being deleted or in a weird state
            time.sleep(retry_interval)
    return False


def release_lock():
    """
    Release the lock by removing the lock file.
    """
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except (FileNotFoundError, PermissionError):
        pass


def read_blackboard():
    """
    Reads the blackboard JSON file. Assumes lock is held.
    """
    if not BLACKBOARD_FILE.exists():
        return {}
    try:
        with open(BLACKBOARD_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            if not content.strip():
                return {}
            return json.loads(content)
    except (json.JSONDecodeError, IOError):
        # Re-raise to avoid overwriting blackboard with {} on transient read failures
        raise


def write_blackboard(data):
    """
    Writes the blackboard JSON file. Assumes lock is held.
    """
    # Write to a temporary file first for extra safety, though lock should handle it
    temp_file = BLACKBOARD_FILE.with_suffix(".json.tmp")
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    # Atomic replace
    os.replace(temp_file, BLACKBOARD_FILE)


def read(key):
    """
    Read a key from the blackboard with locking.
    """
    if acquire_lock():
        try:
            data = read_blackboard()
            return data.get(key)
        finally:
            release_lock()
    else:
        raise TimeoutError(f"Could not acquire lock for reading {key}")


def write(key, value):
    """
    Write a key-value pair to the blackboard with locking.
    """
    if acquire_lock():
        try:
            data = read_blackboard()
            data[key] = value
            write_blackboard(data)
        finally:
            release_lock()
    else:
        raise TimeoutError(f"Could not acquire lock for writing {key}={value}")


def main():
    parser = argparse.ArgumentParser(description="Shared Context Blackboard CLI")
    subparsers = parser.add_subparsers(dest="command")

    set_parser = subparsers.add_parser("set")
    set_parser.add_argument("key")
    set_parser.add_argument("value")

    get_parser = subparsers.add_parser("get")
    get_parser.add_argument("key")

    args = parser.parse_args()

    try:
        if args.command == "set":
            write(args.key, args.value)
            # print(f"Set {args.key} = {args.value}")
        elif args.command == "get":
            val = read(args.key)
            if val is not None:
                print(val)
            else:
                sys.exit(1)
        else:
            parser.print_help()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
