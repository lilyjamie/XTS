#!/usr/bin/env python3
#coding=utf-8

""" modify pty module to pass return code of spawn """
"""Pseudo terminal utilities."""

# Bugs: No signal handling.  Doesn't set slave termios and window size.
#       Only tested on Linux.
# See:  W. Richard Stevens. 1992.  Advanced Programming in the
#       UNIX Environment.  Chapter 19.
# Author: Steen Lumholt -- with additions by Guido.

from select import select
import os
import tty
import sys


class monitor_terminal(object):
    def __init__(self, argv):
        self.STDIN_FILENO = 0
        self.STDOUT_FILENO = 1
        self.STDERR_FILENO = 2
        self.CHILD = 0
        self.argv = argv
        self.master_fd = 0
        self.exit = True

    def set_exit(self):
        self.exit = False

    def openpty(self):
        """openpty() -> (master_fd, slave_fd)
        Open a pty master/slave pair, using os.openpty() if possible."""

        try:
            return os.openpty()
        except (AttributeError, OSError):
            pass
        master_fd, slave_name = self._open_terminal()
        slave_fd = self.slave_open(slave_name)
        return master_fd, slave_fd

    def master_open(self):
        """master_open() -> (master_fd, slave_name)
        Open a pty master and return the fd, and the filename of the slave end.
        Deprecated, use openpty() instead."""

        try:
            master_fd, slave_fd = os.openpty()
        except (AttributeError, OSError):
            pass
        else:
            slave_name = os.ttyname(slave_fd)
            os.close(slave_fd)
            return master_fd, slave_name

        return self._open_terminal()

    def _open_terminal(self):
        """Open pty master and return (master_fd, tty_name)."""
        for x in 'pqrstuvwxyzPQRST':
            for y in '0123456789abcdef':
                pty_name = '/dev/pty' + x + y
                try:
                    fd = os.open(pty_name, os.O_RDWR)
                except os.error:
                    continue
                return (fd, '/dev/tty' + x + y)
        raise os.error('out of pty devices')

    def slave_open(self, tty_name):
        """slave_open(tty_name) -> slave_fd
        Open the pty slave and acquire the controlling terminal, returning
        opened filedescriptor.
        Deprecated, use openpty() instead."""

        result = os.open(tty_name, os.O_RDWR)
        try:
            from fcntl import ioctl, I_PUSH
        except ImportError:
            return result
        try:
            ioctl(result, I_PUSH, "ptem")
            ioctl(result, I_PUSH, "ldterm")
        except IOError:
            pass
        return result

    def fork(self):
        """fork() -> (pid, master_fd)
        Fork and make the child a session leader with a controlling terminal."""
        try:
            pid, fd = os.forkpty()
        except (AttributeError, OSError):
            pass
        else:
            if pid == self.CHILD:
                try:
                    os.setsid()
                except OSError:
                    # os.forkpty() already set us session leader
                    pass
            return pid, fd
        master_fd, slave_fd = self.openpty()
        pid = os.fork()
        if pid == self.CHILD:
            # Establish a new session.
            os.setsid()
            os.close(master_fd)

            # Slave becomes stdin/stdout/stderr of child.
            os.dup2(slave_fd, self.STDIN_FILENO)
            os.dup2(slave_fd, self.STDOUT_FILENO)
            os.dup2(slave_fd, self.STDERR_FILENO)
            if (slave_fd > self.STDERR_FILENO):
                os.close(slave_fd)

            # Explicitly open the tty to make it become a controlling tty.
            tmp_fd = os.open(os.ttyname(self.STDOUT_FILENO), os.O_RDWR)
            os.close(tmp_fd)
        else:
            os.close(slave_fd)
        # Parent and child process.
        return pid, master_fd
    #内部自用_writen
    def _writen(self,fd, data):
        """Write all the data to a descriptor."""
        while data != '':
            n = os.write(fd, data.encode())
            data = data[n:]
    #用户可用的writen
    def writen(self,data):
        self._writen(self.master_fd, data)

    def _read(self,fd):
        """Default read function."""
        return os.read(fd, 1024)

    def _copy(self,master_fd):
        """Parent copy loop.
        Copies
                pty master -> standard output
                standard input -> pty master    """
        fds = [master_fd, self.STDIN_FILENO]
        self.master_fd=master_fd
        while self.exit:
            rfds, wfds, xfds = select(fds, [], [])
            if master_fd in rfds:
                data = self._read(master_fd)
                if not data:  # Reached EOF.
                    fds.remove(master_fd)
                else:
                    self.monitor(data.decode())
                    os.write(self.STDOUT_FILENO, data)
            if self.STDIN_FILENO in rfds:
                data = self._read(self.STDIN_FILENO)
                if not data:
                    fds.remove(self.STDIN_FILENO)
                else:
                    self._writen(master_fd, data.decode())

    #用户自定义过程监控函数
    def monitor(self, line_stream):
        return

    #用户自定义最终执行代码
    def final(self):
        return

    def run(self):
        """Create a process."""
        if type(self.argv) == type(''):
            self.argv = (self.argv,)
        pid, master_fd = self.fork()
        if pid == self.CHILD:
            os.execlp(self.argv[0], *self.argv)
        try:
            mode = tty.tcgetattr(self.STDIN_FILENO)
            tty.setraw(self.STDIN_FILENO)
            restore = 1
        except tty.error:    # This is the same as termios.error
            restore = 0
        
        try:
            self._copy(master_fd)
        
        except (AttributeError):
            if restore:
                tty.tcsetattr(self.STDIN_FILENO, tty.TCSAFLUSH, mode)
            raise AttributeError
        except (SyntaxError):
            if restore:
                tty.tcsetattr(self.STDIN_FILENO, tty.TCSAFLUSH, mode)
            raise SyntaxError
        except (TypeError):
            if restore:
                tty.tcsetattr(self.STDIN_FILENO, tty.TCSAFLUSH, mode)
            raise TypeError
        except (NameError):
            if restore:
                tty.tcsetattr(self.STDIN_FILENO, tty.TCSAFLUSH, mode)
            raise NameError
        except(IOError, OSError):
            if restore:
                tty.tcsetattr(self.STDIN_FILENO, tty.TCSAFLUSH, mode)
        except (KeyboardInterrupt):
            if restore:
                tty.tcsetattr(self.STDIN_FILENO, tty.TCSAFLUSH, mode)
        except:
            if restore:
                tty.tcsetattr(self.STDIN_FILENO, tty.TCSAFLUSH, mode)
            print("Unknown error")
        self.final()
        os.close(master_fd)
        return os.waitpid(pid, 0)[1]


#调试用主函数
if __name__ == "__main__":
    
    exit(0)

