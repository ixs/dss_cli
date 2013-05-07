#!/usr/bin/env python
#
#    A Python class to interact with a Open-E DSS storage server via the SSH API
#    Copyright (C) 2013  Andreas Thienemann <andreas@bawue.net>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the version 2 of the GNU General Public License
#    as published by the Free Software Foundation.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import logging
import pprint
import sys
import paramiko

class DSS_API():
    def __init__(self, server, keyfile, username = "api", password = None, port = 22223, debug = False):
        self.client = paramiko.SSHClient()
        if debug == True:
            self.logger = logging.getLogger("paramiko")
            self.logger.addHandler(logging.StreamHandler(sys.stdout))
            self.logger.setLevel(logging.DEBUG)
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.connect_params = (server, port, username, password, None, keyfile)

    def api_exec(self, cmdstr):
    	r"""Run a command via SSH"""
        self.client.connect(*self.connect_params)
        stdin, stdout, stderr = self.client.exec_command(cmdstr)
        stdout = stdout.read()
        stderr = stderr.read()
        self.client.close()
        if len(stderr) > 0:
          raise RuntimeError(stderr)
        return stdout[:-1]

    def get_cmds(self):
    	self.commands = dict()
      	for line in self.api_exec("help").split("\n"):
      		if line == "":
      			continue
      		cmd, desc = line.split(" - ")
      		cmd = cmd.strip()
      		self.commands[cmd] = desc

    def get_cmd_help(self, command):
    	return self.api_exec("%s --help" % (command))

def main():
	dss = DSS_API("191.168.220.1", "testfiler.key")

if __name__ == "__main__":
	main()