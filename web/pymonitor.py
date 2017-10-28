#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, time, subprocess

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

command = ['echo', 'ok']
process = None

def log(s):
    print('[Monitor] %s' % s)

# 把restart这个方法绑定到消息响应中，watchdog的FileSystemEventHandler会对目录下任何修改作出反应
class MyFileSystemEventHander(FileSystemEventHandler):
    def __init__(self, fn):
        super(MyFileSystemEventHander, self).__init__()
        self.restart = fn

    # 继承自FileSystemEventHandler
    def on_any_event(self, event):
        if event.src_path.endswith('.py'):
            log('Python source file changed: %s' % event.src_path)
            self.restart()


def kill_process():
    global process
    if process:
        log('Kill process [%s]...' % process.pid)
        process.kill()
        process.wait()
        log('Process ended with code %s.' % process.returncode)
        process = None

def start_process():
    global process, command
    log('Start process %s...' % ' '.join(command))
    process = subprocess.Popen(command, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)

def restart_process():
    kill_process()
    start_process()

def start_watch(path, callback):
    observer = Observer()
    # 这里对path就是web目录对绝对路径
    observer.schedule(MyFileSystemEventHander(restart_process), path, recursive=True)
    observer.start()
    log('Watching directory %s...' % path)
    start_process()
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == '__main__':
    # print(sys.argv)
    # argv = sys.argv[1:]
    # if not argv:
    #     print('Usage: ./pymonitor your-script.py')
    #     exit(0)
    # if argv[0] != 'python3':
    #     argv.insert(0, 'python3')

    # 这样一来直接在pycharm里面运行pymonitor.py就可以了
    command = ['python3', 'app.py']
    path = os.path.abspath('.')
    start_watch(path, None)