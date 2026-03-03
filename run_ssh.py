import paramiko
import sys

def run_ssh_command(host, user, password, command):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(host, username=user, password=password)
        stdin, stdout, stderr = client.exec_command(command)
        print(stdout.read().decode())
        print(stderr.read().decode(), file=sys.stderr)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
    finally:
        client.close()

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python run_ssh.py <host> <user> <password> <command>")
    else:
        run_ssh_command(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
