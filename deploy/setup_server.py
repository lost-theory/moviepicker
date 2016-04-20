'''
Sets up an Ubuntu 15 machine to run the moviepicker app.
'''

from __future__ import print_function

import os
import subprocess
from string import Template
from subprocess import check_call, check_output

NGINX_CONFIG = '''
server {
  listen 0.0.0.0:80;
  server_name 0.0.0.0 ${ips};

  location / {
    proxy_pass http://app;
  }
}

upstream app {
  server unix:/tmp/gunicorn.sock;
}
'''

SERVICE_CONFIG = '''
[Unit]
Description=Moviepicker WSGI server
After=network.target

[Service]
User=${user}
WorkingDirectory=${repo_path}
Type=simple
Environment=SECRET_KEY_PATH=${secret_key_path}
ExecStart=${gunicorn_path} --error-logfile=- --access-logfile=- --log-syslog --bind=unix:/tmp/gunicorn.sock --workers=4 app:app
KillMode=mixed

[Install]
WantedBy=multi-user.target
'''

def run(cmd, **kw):
    print("Running: {} with {}".format(cmd, kw))
    check_call(cmd, **kw)

def md5sum(path):
    checksum, _ = check_output(["md5sum", path]).strip().split()
    return checksum

def file_needs_update(src, dst):
    if not os.path.exists(dst):
        return True
    if md5sum(src) != md5sum(dst):
        return True
    return False

def main():
    # install packages
    if not os.path.isfile("/usr/bin/python2.7"):
        run(["sudo", "apt-get", "install", "-y", "python-minimal"])
    if not os.path.isfile("/usr/bin/virtualenv"):
        run(["sudo", "apt-get", "install", "-y", "python-virtualenv"])
    if not os.path.isfile("/usr/sbin/nginx"):
        run(["sudo", "apt-get", "install", "-y", "nginx"])
    if not os.path.isfile("/usr/bin/git"):
        run(["sudo", "apt-get", "install", "-y", "git"])

    # clone & update git repo
    repo_path = os.path.join(os.environ['HOME'], 'moviepicker')
    if not os.path.isdir(repo_path):
        run(["git", "clone", "git@github.com:lost-theory/moviepicker.git", repo_path])
    run(["git", "fetch"], cwd=repo_path)
    run(["git", "reset", "--hard", "origin/deploy"], cwd=repo_path)

    # virtualenv and requirements.txt
    venv_path = os.path.join(os.environ['HOME'], 'mp_env')
    pip_path = os.path.join(venv_path, "bin/pip")
    if not os.path.isdir(venv_path):
        run(["virtualenv", "-p", "/usr/bin/python2.7", venv_path])
    run([pip_path, "install", "-r", os.path.join(repo_path, "requirements.txt")])
    run([pip_path, "install", "gunicorn==19.4.5"])

    # nginx configs
    ips = check_output(["hostname", "--all-ip-addresses"]).strip()
    with open("/tmp/app.conf", "w") as f:
        f.write(Template(NGINX_CONFIG).substitute(
            ips=ips
        ))
    if file_needs_update(src="/tmp/app.conf", dst="/etc/nginx/conf.d/app.conf"):
        run(["sudo", "mv", "/tmp/app.conf", "/etc/nginx/conf.d/app.conf"])
        run(["sudo", "service", "nginx", "reload"])

    # gunicorn systemd service config
    gunicorn_service_src = "/tmp/gunicorn.service"
    gunicorn_service_dst = "/etc/systemd/system/multi-user.target.wants/gunicorn.service"
    with open(gunicorn_service_src, "w") as f:
        f.write(Template(SERVICE_CONFIG).substitute(
            user=os.environ['USER'],
            secret_key_path=os.path.join(os.environ['HOME'], '.moviepicker-secret'),
            gunicorn_path=os.path.join(venv_path, "bin/gunicorn"),
            repo_path=repo_path,
        ))
    if file_needs_update(src=gunicorn_service_src, dst=gunicorn_service_dst):
        run(["sudo", "mv", gunicorn_service_src, gunicorn_service_dst])
        run(["sudo", "systemctl", "daemon-reload"])
        run(["sudo", "service", "gunicorn", "restart"])

def push(remote):
    local_secret_path = os.path.join(os.environ['HOME'], '.moviepicker-secret')
    if not os.path.isfile(local_secret_path):
        raise RuntimeError("Please create a file at {!r} with the `app.secret_key` value you'd like to deploy.".format(local_secret_path))
    run(["scp", local_secret_path, "{}:~/".format(remote)])
    run(["scp", __file__, "{}:/tmp/".format(remote)])
    run(["ssh", "-A", remote, "python -u /tmp/setup_server.py main"])

if __name__ == "__main__":
    import sys
    script = sys.argv.pop(0)
    if not sys.argv:
        print("Usage: `{0} push user@host` or `{0} main`.".format(script))
    elif len(sys.argv) == 2 and sys.argv[0] == "push":
        push(sys.argv[1])
    elif sys.argv[0] == 'main':
        main()
