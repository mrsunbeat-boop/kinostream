import subprocess
import base64
import sys

def run_command(host, user, password, command):
    print(f"[*] Выполняю на {host}: {command[:100]}...")
    try:
        result = subprocess.run(
            ['python', 'run_ssh.py', host, user, password, command],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        if result.returncode != 0:
            print(f"[!] Ошибка на {host}: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"[!] Исключение при выполнении на {host}: {e}")
        return False

def main():
    print("=== Мастер быстрой установки White VPN ===")
    ru_ip = input("Введите IP российского сервера (RU): ").strip()
    ru_pass = input("Введите пароль root для RU сервера: ").strip()
    
    fi_ip = input("Введите IP зарубежного сервера (FI): ").strip()
    fi_pass = input("Введите пароль root для FI сервера: ").strip()
    
    domain = input("Введите домен (например, white-box.mooo.com) или оставьте пустым: ").strip()
    if not domain:
        domain = ru_ip # Используем IP если домен не указан

    print("\n--- ЭТАП 1: Настройка зарубежного сервера (FI) ---")
    
    # 1. Установка 3x-ui
    install_cmd = "if ! command -v x-ui &> /dev/null; then bash <(curl -Ls https://raw.githubusercontent.com/maci93/3x-ui/master/install.sh); fi"
    if not run_command(fi_ip, "root", fi_pass, install_cmd):
        print("[-] Ошибка при установке 3x-ui. Прерываю.")
        return

    # 2. Настройка 3x-ui через SQL
    # Команды: subTitle='freelink', subDomain=domain, webCertFile='/root/cert/panel/fullchain.pem', webKeyFile='/root/cert/panel/privkey.pem'
    sql_script = f"""
    UPDATE settings SET value='freelink' WHERE key='subTitle';
    UPDATE settings SET value='{domain}' WHERE key='subDomain';
    UPDATE settings SET value='/root/cert/panel/fullchain.pem' WHERE key='webCertFile';
    UPDATE settings SET value='/root/cert/panel/privkey.pem' WHERE key='webKeyFile';
    """
    sql_b64 = base64.b64encode(sql_script.encode()).decode()
    setup_fi_cmd = f"echo '{sql_b64}' | base64 -d | sqlite3 /etc/x-ui/x-ui.db && /usr/local/x-ui/x-ui setting -username admin -password Adminushka1! -port 2053 && x-ui restart"
    
    if not run_command(fi_ip, "root", fi_pass, setup_fi_cmd):
        print("[-] Ошибка при настройке 3x-ui.")
        return

    print("\n--- ЭТАП 2: Настройка российского сервера (RU) ---")
    
    # 1. Установка Nginx
    install_nginx_cmd = "apt-get update && apt-get install -y nginx"
    if not run_command(ru_ip, "root", ru_pass, install_nginx_cmd):
        print("[-] Ошибка при установке Nginx.")
        return

    # 2. Конфигурация Nginx
    nginx_conf = f"""
server {{
    listen 80;
    server_name {domain};
    location /sub/ {{
        proxy_pass http://{fi_ip}:2096/sub/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
server {{
    listen 443 ssl;
    server_name {domain};
    ssl_certificate /etc/letsencrypt/live/{domain}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{domain}/privkey.pem;
    location /sub/ {{
        proxy_pass http://{fi_ip}:2096/sub/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
"""
    nginx_b64 = base64.b64encode(nginx_conf.encode()).decode()
    setup_ru_cmd = f"echo '{nginx_b64}' | base64 -d > /etc/nginx/sites-enabled/default && nginx -t && systemctl restart nginx"
    
    if not run_command(ru_ip, "root", ru_pass, setup_ru_cmd):
        print("[-] Ошибка при настройке Nginx. Проверьте, есть ли сертификаты по путям.")
    else:
        print("\n=== УСТАНОВКА ЗАВЕРШЕНА УСПЕШНО! ===")
        print(f"Панель управления: https://{domain}:2053 (или http://{fi_ip}:2053)")
        print(f"Логин: admin")
        print(f"Пароль: Adminushka1!")
        print(f"Подписки доступны через: http://{domain}/sub/<ID>")

if __name__ == "__main__":
    main()
