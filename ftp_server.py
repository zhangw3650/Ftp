'''
ftp 文件服务器
'''
from socket import *
import os
import sys
import signal
import time

# 文件库路径
FILE_PATH = "/home/tarena/ftpFile/"
HOST = ""
PORT = 8000
ADDR = (HOST, PORT)


# 将文件服务器功能写在类中
class FtpServer(object):
    def __init__(self, connfd):
        self.connfd = connfd

    def do_list(self):
        # 获取文件列表
        file_list = os.listdir(FILE_PATH)
        if not file_list:
            self.connfd.send("文件库为空".encode())
        else:
            self.connfd.send(b'OK')
            time.sleep(0.1)
        files = ''
        for file in file_list:
            if file[0] != '.' and os.path.isfile(FILE_PATH + file):
                files = files + file + '#'
        self.connfd.send(files.encode())

    def do_get(self, filename):
        try:
            fd = open(FILE_PATH + filename, 'rb')
        except Exception:
            self.connfd.send("文件不存在".encode())
            return
        self.connfd.send(b'OK')
        time.sleep(0.1)
        # 发送文件
        while True:
            data = fd.read(1024)
            if not data:
                fd.close()
                time.sleep(0.1)
                self.connfd.send(b'##')
                break
            self.connfd.send(data)
        print("文件发送完毕")

    def do_quit(self, addr):
        self.connfd.close()
        sys.exit("客户端已退出 " + str(addr))

    def do_put(self, filename):
        file_list = os.listdir(FILE_PATH)
        if filename in file_list:
            self.connfd.send("文件库中已有同名文件".encode())
        else:
            self.connfd.send(b'OK')
            fd = open(FILE_PATH + filename, 'wb')
            while True:
                data = self.connfd.recv(1024)
                if data == b'##':
                    fd.close()
                    break
                fd.write(data)
            print("文件接受完毕")


# 创建套接字，接受客户端链接，创建新的进程
def main():
    sockfd = socket()
    sockfd.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sockfd.bind(ADDR)
    sockfd.listen(5)

    # 处理子进程退出
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)
    print("Listen the port 8000...")

    while True:
        try:
            connfd, addr = sockfd.accept()
        except KeyboardInterrupt:
            sockfd.close()
            sys.exit("服务器退出")
        except Exception as e:
            print("服务端异常:", e)
            continue

        print("已连接客户端", addr)

        # 创建子的进程
        pid = os.fork()
        if pid == 0:
            sockfd.close()
            ftp = FtpServer(connfd)
            # 判断客户端请求
            while True:
                data = connfd.recv(1024).decode()
                if not data:
                    connfd.close()
                    sys.exit("客户端已退出", addr)
                elif data[0] == 'L':
                    ftp.do_list()
                elif data[0] == 'G':
                    filename = data.split(' ')[-1]
                    ftp.do_get(filename)
                elif data[0] == 'P':
                    filename = data.split(' ')[-1]
                    ftp.do_put(filename)
                elif data[0] == 'Q':
                    ftp.do_quit(addr)

        else:
            # 父进程或者创建失败都继续等待下个客户端链接
            connfd.close()
            continue


if __name__ == "__main__":
    main()
