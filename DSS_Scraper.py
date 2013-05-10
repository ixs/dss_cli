#!/usr/bin/python
#
#    A Python module to control an Open-E DSS Filer.
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

import json
import urllib
import urlparse
import HTMLParser
import logging
import operator
import pprint
import random
import re
import sys
import mechanize
import cookielib
import BeautifulSoup

class DSS_Scraper():

    def __init__(self, server, password, debug = False):
        r"""Initiate defaults"""
        self.server = server
        self.password = password
        self.debug = debug
        self.allowed_cmds = [ "volume_replication_remove", "volume_replication_mode", "volume_replication_task_create", "iscsi_target_access", "iscsi_target_remove",
                "failover_task", "nas_share_toggle_smb", "volume_replication_task_stop", "volume_replication_task_remove", "volume_replication_task_status", "lv_remove"]

        # Logging
        if debug == True:
            self.logger = logging.getLogger("mechanize")
            self.logger.addHandler(logging.StreamHandler(sys.stdout))
            self.logger.setLevel(logging.DEBUG)

        # Browser
        self.br = mechanize.Browser()
        if debug == True:
            self.br.set_debug_http(True)
            self.br.set_debug_responses(False)
            self.br.set_debug_redirects(True)

        # Cookie Jar
        self.cj = cookielib.LWPCookieJar()
        self.br.set_cookiejar(self.cj)

    def login(self):
        r"""Login into remote Open-E DSS Server"""
        self.br.open("%s/" % (self.server,))
        self.soup = BeautifulSoup.BeautifulSoup(self.br.response().read())
        # Need to login
        if filter(lambda x:x[1] == 'login_form', self.soup('form')[0].attrs)[0][1] == "login_form":
            self.br.select_form(nr=0)
            self.br["set_user"] = ["full_access"]
            self.br["password"] = self.password
            self.br.submit()

        self.soup = BeautifulSoup.BeautifulSoup(self.br.response().read())

        # Build a list of all addresses
        for script in self.soup('script'):
            if "Address" in script.text:
                # Now extract both Addresses and MenuStruct JSON construct
                # Simple top down parser
                struct = None
                for line in script.text.split('\n'):
                    if line == 'Addresses = {':
                        struct = "{"
                        continue
                    if line == "}":
                        struct += line
                        self.addresses = json.loads(struct)
                        continue
                    if line == 'MenuStruct = [':
                        struct = "["
                        continue
                    if line == ']':
                        struct += line
                        self.menustruct = json.loads(struct)
                        continue
                    if struct is not None:
                        struct += line

    def logout(self):
        r"""Logout of remote Open-E DSS Filer"""
        self.br.open("%s/?logout=1" % (self.server,))
        self.br.close()

    def fetch_message_index(self):
        r"""Fetch index of messages"""
        self.br.open("%s/error.php" % (self.server,))
        self.br.open("%s/status.php?status=logsXML&select=messages" % (self.server,))
        print self.br.response().read()

    def fetch_message(self, msgid):
        r"""Fetch a message by ID"""
        self.br.open("%s/error.php?groupId=%s" % (self.server, msgid))
        print self.br.response().read()

    def parse_pageData(self, msg):
        r"""Parse Javascript returned by server and extract the JSON pageData contruct"""
        for line in msg.split("\n"):
            if line.startswith("this.pageData"):
                return json.loads(line.split(" ", 2)[2][:-1])

    def module_list(self, id):
        r"""Output JSON construct detailing the items on a module page"""
        self.br.open("%s/XhrModuleLoader.php?opt=%s&id=%s&__rand=%f" % (self.server, "list", id, random.random()))
        return self.parse_pageData(self.br.response().read())

    def module_display(self, moduleName, id, **args):
        r"""Output the HTML code for an item on a module page"""
        if len(args) > 0:
            self.br.open("%s/XhrModuleLoader.php?opt=%s&_moduleName=%s&id=%s&%s&__rand=%s" % (self.server, "disp", moduleName, id, urllib.urlencode(args), random.random()))
        else:
            self.br.open("%s/XhrModuleLoader.php?opt=%s&_moduleName=%s&id=%s&__rand=%s" % (self.server, "disp", moduleName, id, random.random()))
        return self.br.response().read()

    def tree_index(self, id):
        r"""Fetch dataLink descriptions of the left tree pane(s) on a module page"""
        module = self.module_list(id)
        return dict(map(lambda x: (x["name"], x["dataLink"]), module["trees"]))

    def tree_items(self, datalink):
        r"""Parse the tree items included in a tree pane referenced by a dataLink URL"""
        self.br.open("%s/%s&text=1&_rn=%s" % (self.server, datalink, random.random()))
        ret = dict()
        for line in self.br.response().read().split('\n'):
            if line.startswith("ob = new WebFXTreeItem("):
                # Extract URL, and parse that to get uid, type and name
                items = urlparse.parse_qs(urlparse.urlparse(HTMLParser.HTMLParser().unescape(line.split("'", 5)[4][:-1]))[4])
                ret[items["name"][0]] = dict()
                for item in items:
                    if item not in ["module"]:
                        ret[items["name"][0]][item] = items[item][0]
        return ret


    def tree_list(self, items):
        r"""Return the JSON construct detailing the items on a tree page. This is similar to the module_list() function."""
        self.br.open("%s/XhrModuleLoader.php?opt=%s&%s&__rand=%s" % (self.server, "list", urllib.urlencode(items), random.random()))
        return self.parse_pageData(self.br.response().read())


    def tree_display(self, items):
        r"""Display the tree page items"""
        self.br.open("%s/XhrModuleLoader.php?opt=%s&%s&__rand=%s" % (self.server, "disp", urllib.urlencode(items), random.random()))
        return self.br.response().read()


    def remove_control_from_active_form(self, whitelist = [], blacklist = []):
        if len(whitelist) > 0 and len(blacklist) == 0:
            # Remove the controls not needed/wanted based on the whitelist
            # For some reason, HTMLClientForm does not always correctly remove an item. This needs several iterations it seems.
            clean = False
            while clean == False:
                for control in self.br.form.controls:
                    if control.name not in whitelist:
                        self.br.form.controls.remove(control)
                clean = True
                for control in self.br.form.controls:
                    if control.name not in whitelist:
                        clean = False

        if len(whitelist) == 0 and len(blacklist) > 0:
            # Remove the controls not needed/wanted based on the blacklist
            # For some reason, HTMLClientForm does not always correctly remove an item. This needs several iterations it seems.
            clean = False
            while clean == False:
                for control in self.br.form.controls:
                    if control.name in blacklist:
                        self.br.form.controls.remove(control)
                clean = True
                for control in self.br.form.controls:
                    if control.name in blacklist:
                        clean = False


    def volume_replication_remove(self, lv_name):
        r"""Removes replication from Volume
        Usage: volume_replication_remove <lvname>

        Remove replication from a lv.

        Options:
          -h, --help     show this help message and exit
        """
        if lv_name[:2] != "lv":
            raise ValueError("Doesn't look like a logical volume")
        vg = lv_name[2:-2]
        # Fetch the tree information
        tree_index = self.tree_index('1.5')
        tree_items = self.tree_items(tree_index["volumes"])
        for module in self.tree_list(tree_items[vg])["modules"]:
            if module["name"] == "VolumeManager":
                content = self.tree_display({ "_moduleName": module["name"], "id": module["pageId"], "name": vg, "uid": tree_items[vg]["uid"] })
                self.br.select_form(nr=0)
                # Select the modify LV action.
                for item in self.br.form.find_control("data[action]").items:
                    label = item.get_labels()[0]._text
                    item = item.name.split(";")
                    if item[0] == "expand" and label.startswith("modify") and label.split("\xc2\xa0")[1] == lv_name:
                        self.br.form["data[action]"] = [";".join(item)]
                        break
                # Remove the controls not needed/wanted
                self.remove_control_from_active_form(whitelist = ["VolumeManager_send", "data[uid]", "data[lv_name]", "data[snapshot_name]", "data[iscsi_volume_type]", "data[new_size]",
                    "data[endAction]", "jump", "data[action]", "data[assign_lv]", "data[iscsitrgt]", "data[blocksize]", "data[initialize_level]"])
                # Add the run_engine toggle
                self.br.form.new_control("hidden", "run_engine", { "value": "true" })
                self.br.form.fixup()
                self.br.submit()


    def volume_replication_mode(self, lv_name, mode, clear_metadata=False):
        r"""Set volume replication mode to source or destination
        Usage: volume_replication_mode <lvname> <mode> [options]

        Configure the volume replication mode of a lv.

        <mode> can be either "primary" for source or "secondary" for destination.

        Options:
          -h, --help     show this help message and exit
          --clear        clear the replication metadata
        """
        if mode not in ["primary", "secondary"]:
            raise ValueError("Invalid mode specified")
        response = self.module_display("VolumeReplicationMode", "1.5.2")
        # Build a dictionary of lv:uid
        self.soup = BeautifulSoup.BeautifulSoup(response)
        volumes = list()
        uids = list()
        for elem in self.soup.findAll('td', {"class": "trowLeft"}):
            volumes.append(elem.getText())
        for elem in self.soup.findAll('input', {"class": "checkbox"}):
            dtype, name = operator.itemgetter(1, 3)(re.split('[\[\]]', elem.attrMap["name"]))
            if dtype == "clear_metadata":
                uids.append(name)
        volumes = dict(zip(volumes, uids))

        self.br.select_form(nr=0)
        self.br.form["data[state][%s]" % (volumes[lv_name])] = [mode]

        # Remove clear_metadata entries
        self.remove_control_from_active_form(blacklist = map(lambda x: "data[clear_metadata][%s]" % (volumes[x]), volumes))
        if clear_metadata == True:
            self.br.form.new_control("checkbox", "data[clear_metadata][%s]" % (volumes[lv_name]), { "value": "1" })
            self.br.form.find_control(name="data[clear_metadata][%s]" % (volumes[lv_name])).items[0].selected = True
        self.br.form.new_control("hidden", "run_engine", { "value": "1" })
        self.br.submit()

    def volume_replication_task_create(self, src_lv_name, dst_lv_name, task_name, bandwidth = 40):
        r"""Create a volume replication task
        Usage: volume_replication_task_create <source lvname> <destination lvname> <task name> [bandwidth]

        This function allows you to create a volume replication task replicating a
        source to a destination volume.

        Options:
          -h, --help     show this help message and exit
        """
        # Reload not needed, form comes pre-filled
        # self.br.open("%s/status.php?%s", self.server, urllib.urlencode({ "status": "replication_remote_lv", "opt_param": "scan", "local_lv_size": 1, "local_lv_type": "b",
        #         "id": "DefineVolumeReplicationTask_destination_volume_id, "btn1": "DefineVolumeReplicationTask_reload", "btn2": "DefineVolumeReplicationTask_create"))
        response = self.module_display("DefineVolumeReplicationTask", "1.5.2")
        self.soup = BeautifulSoup.BeautifulSoup(response)
        # Check if we have an error message from the server.
        try:
            raise SystemError(self.soup.find("div", { "class": "messageBody" }).getText())
        except AttributeError:
            pass
        self.br.select_form(nr=0)
        self.remove_control_from_active_form(whitelist = ["DefineVolumeReplicationTask_send", "data[mirror_server_ip]", "data[source_lv_shortname]",
                "data[destination_lv_shortname]", "data[task_name]", "data[bandwidth]", "jump", "data[source_uid]", "data[destination_uid]"])
        # Build a dictionary of lvnames and uids
        src_volumes = dict()
        dst_volumes = dict()
        for item in self.br.form.find_control("data[source_uid]").items:
            label = item.get_labels()[0]._text
            src_volumes[label] = item.name
        for item in self.br.form.find_control("data[destination_uid]").items:
            label = item.get_labels()[0]._text
            dst_volumes[label] = item.name
        # Fill in the form
        self.br.form.find_control("data[source_lv_shortname]").readonly = False
        self.br.form.find_control("data[destination_lv_shortname]").readonly = False
        self.br.form["data[source_lv_shortname]"] = src_lv_name
        self.br.form["data[destination_lv_shortname]"] = dst_lv_name
        self.br.form["data[task_name]"] = task_name
        self.br.form["data[bandwidth]"] = str(bandwidth)
        self.br.form["data[source_uid]"] = [src_volumes[src_lv_name]]
        try:
            self.br.form["data[destination_uid]"] = [dst_volumes[dst_lv_name]]
        except KeyError:
            raise SystemError("Failover system does not have specified target destination.")
        self.br.form.new_control("hidden", "run_engine", { "value": "true"})
        self.br.submit()

    def volume_replication_task_action(self, task_name, action):
        response = self.module_display("ReplicationTasksManager", "1.5.2")
        # Build a list of Tasks
        self.soup = BeautifulSoup.BeautifulSoup(response)
        tasks = list()
        for elem in self.soup.findAll('td', {"class": "trow"}):
            if elem.span != None:
                tasks.append(elem.getText())
        if task_name not in tasks or task_name == "failover_data":
            raise ValueError("Invalid task name given.")
        if action not in ("start", "stop", "remove"):
            raise ValueError("Invalid action given.")
        self.br.select_form(nr=0)
        self.br.form.find_control("action_input").readonly = False
        self.br.form.find_control("task").readonly = False
        self.br.form.find_control("type").readonly = False
        self.br.form["action_input"] = action
        self.br.form["type"] = "VREP"
        self.br.form["task"] = task_name
        self.br.form.new_control("hidden", "run_engine", { "value": "true"})
        self.br.submit()

    def lv_remove(self, lv_name):
        r"""Remove a logical volume
        Usage: lv_remove <lv>

        This function deletes a logical volume.

        Options:
          -h, --help     show this help message and exit
        """
        if lv_name[:2] != "lv":
            raise ValueError("Doesn't look like a logical volume")
        vg = lv_name[2:-2]
        # Fetch the tree information
        tree_index = self.tree_index('1.5')
        tree_items = self.tree_items(tree_index["volumes"])
        lvs = list()
        for module in self.tree_list(tree_items[vg])["modules"]:
            if module["name"] == "VolumeManager":
                content = self.tree_display({ "_moduleName": module["name"], "id": module["pageId"], "name": vg, "uid": tree_items[vg]["uid"] })

                # Build a dictionary containing lv-id and remove cmd
                self.soup = BeautifulSoup.BeautifulSoup(content)
                for elem in self.soup.findAll('td', {"class": "trowLeft fat"}):
                    if elem.span != None:
                        lvs.append([elem.getText()])
                i = 0
                for elem in self.soup.findAll('td', {"class": "trowRight"}):
                    if elem.span != None and i < len(lvs):
                        for attr in elem.span.img.attrs:
                            if attr[0] == "onclick":
                                lvs[i].append(re.split('[\(\)]', attr[1])[1][1:-1])
                        i += 1
                if ["failover_data"] in lvs:
                    del lvs[lvs.index(["failover_data"])]
                lvs = dict(lvs)

                self.br.select_form(nr=0)
                # Remove the controls not needed/wanted
                self.remove_control_from_active_form(whitelist = ["VolumeManager_send", "data[uid]", "data[lv_name]", "data[snapshot_name]", "data[iscsi_volume_type]", "data[new_size]",
                    "data[endAction]", "jump", "data[assign_lv]", "data[iscsitrgt]", "data[blocksize]", "data[initialize_level]"])
                # Add
                self.br.form.new_control("hidden", "data[action]", { "value": lvs[lv_name] })                
                # Add the run_engine toggle
                self.br.form.new_control("hidden", "run_engine", { "value": "true" })
                self.br.form.fixup()
                self.br.submit()

    def volume_replication_task_stop(self, task_name):
        r"""Stop a replication task
        Usage: volume_replication_task_stop <task>

        This function is able to stop a running volume replication task.

        Options:
          -h, --help     show this help message and exit
        """
        self.volume_replication_task_action(task_name, "stop")

    def volume_replication_task_remove(self, task_name):
        r"""Remove a replication task
        Usage: volume_replication_task_remove <task>

        This function is able to remove a volume replication task.

        Options:
          -h, --help     show this help message and exit
        """
        self.volume_replication_task_action(task_name, "remove")

    def volume_replication_task_status(self, task_name):
        r"""Status of a replication task
        Usage: volume_replication_task_status <task>

        Options:
          -h, --help     show this help message and exit
        """
        response = self.module_display("RunningTasks", "3.4.1", type="backupTasksLogs", name="Volume Replication", tasktype="VREP")
        self.br.open("%s/status.php?status=running_tasks_info&opt_param=RunningTasks3.4.1_%s" % (self.server, task_name))
        self.soup = BeautifulSoup.BeautifulSoup(self.br.response().read())
        self.soup = BeautifulSoup.BeautifulSoup(HTMLParser.HTMLParser().unescape(self.soup.status.data.getText()))
        keys = list()
        vals = list()
        for item in self.soup.findAll("div", {"class": "txtArea"}):
            keys.append(item.getText())

        for item in self.soup.findAll("div", {"class": "inputArea"}):
            vals.append(item.getText())

        for i in range(0, len(keys)):
            print "%-25s %s" % (keys[i], vals[i])


    def failover_task(self, task, state):
        r"""Manage a failover task
        Usage: failover_task <task> <state>

        Remove a volume replication task from the failover setup.
        This serves to include or exclude replicated volumes from the failover group.

        <task> is a volume replication task_name
        <state> is either enable or disable

        Options:
          -h, --help     show this help message and exit
        """
        response = self.module_display("ClusterTasks", "1.2.2")
        self.br.select_form(nr=0)
        tasks = list()
        task_name = ""

        if state == "disable":
            selector = "ClusterTasks_moving_list_sel_shares_list"
        elif state == "enable":
            selector = "ClusterTasks_moving_list_ava_shares_list"
        else:
            raise ValueError("Incorrect state %s given." % (state))
        for control in self.br.form.controls:
            if control.id == selector:
                for item in control.items:
                    tasks.append(item.name)
                    if item.name.split(" ", 1)[1] == task:
                        task_name = item.name
        self.remove_control_from_active_form(whitelist = ["ClusterTasks_send", "user", "ClusterTasks_moving_list_ava_shares_listqu",
                "ClusterTasks_moving_list_sel_shares_listqu", "selected_tasks", "jump"])
        self.br.form.find_control("selected_tasks").readonly = False

        current_tasks = self.br.form["selected_tasks"].split(";")
        if state == "disable":
            del current_tasks[current_tasks.index(task_name)]
        elif state == "enable":
            try:
                # Delete empty item
                del current_tasks[current_tasks.index("")]
            except:
                pass
            current_tasks.append(task_name)
        self.br.form["selected_tasks"] = ";".join(current_tasks)
        self.br.form.new_control("hidden", "run_engine", { "value": "true"})
        self.br.submit()


    def iscsi_target_access(self, target, allow = [], deny = []):
        r"""Configure Target IP access
        Usage: iscsi_target_access <target> [options]

        This function allows you to configure IP addresses allowed and denied to access an iscsi target.

        Optons:
          -h, --help          show this help message and exit
          -a IP, --allow=IP   The IP address or the network allowed access to the target.
          -d IP, --deny=IP    The IP address or the network denied access to the target.

        Multiple IPs or CIDR ranges can be separated by semicolon.
        """
        response = self.module_display("TargetIpAccess", "2.8.1", type = "target", label = target, name = target)
        self.br.select_form(nr=0)
        for rule in ("allow", "deny"):
            if len(rule) > 1:
                self.br.form[rule] = ";".join(locals()[rule])
        self.br.form.new_control("hidden", "run_engine", { "value": "true"})
        self.br.submit()

    def iscsi_target_remove(self, target):
        r"""Remove an existing iSCSI target
        Usage: iscsi_target_remove <target>

        This function removes the existing iSCSI target named <target>

        Optons:
          -h, --help          show this help message and exit
        """
        tree_index = self.tree_index('2.8')
        tree_items = self.tree_items(tree_index["targets"])
        if target not in tree_items:
            raise ValueError("Target %s not found" % (target))
        self.module_display("TargetRemove", "2.8.1", type = "target", label = tree_items[target]["label"], name = target)
        self.br.select_form(nr=0)
        self.br.form.new_control("hidden", "run_engine", { "value": "true"})
        self.br.submit()
        #self.br.form = mechanize._form.ParseString("", "http://%s/postEvent.php" % (self.server))[0]
        #self.br.form.method = "POST"
        #self.br.form.new_control("hidden", "type", {"value": "cache"})
        #self.br.form.new_control("hidden", "event", {"value": "lv_disks_change"})
        #self.br.submit()

    def nas_share_toggle_smb(self, share, state):
        r"""Enable or disable SMB support for a share
        Usage: nas_share_toggle_smb <share> <state>

        This function enables or disables SMB support for a given <share>.
        <state> needs to be either "enabled" or "disabled".

        Optons:
          -h, --help          show this help message and exit
        """
        tree_index = self.tree_index('1.6')
        tree_items = self.tree_items(tree_index["shares"])
        if share not in tree_items:
            raise ValueError("Share %s not found" % (share))
        self.module_display("ResourcesSmbSettings", "1.6.1", type = "share", name = share)
        self.br.select_form(nr=0)
        if state == "enabled":
            self.br.form.find_control(name="smb").items[0].selected = True
        elif state == "disabled":
            self.br.form.find_control(name="smb").items[0].selected = False
        else:
            raise ValueError("State must be either \"enabled\" or \"disable\"")
        self.br.form.new_control("hidden", "run_engine", { "value": "true"})
        self.br.submit()

    def get_cmds(self):
        cmds = dict()
        for cmd in self.allowed_cmds:
            cmds[cmd] = getattr(self, cmd).__doc__.split("\n")[0]
        self.commands = cmds

    def get_cmd_help(self, command):
        if command not in self.allowed_cmds:
            raise ValueError("Invalid command")
        help = ""
        for line in getattr(self, command).__doc__.split("\n")[1:]:
            help += "%s\n" % line.strip()
        return help

    def web_exec(self, *args):
        args = args[0]
        cmd = args[0]
        if cmd == "volume_replication_mode":
            if args[-1] == "--clear":
                cm = True
            else:
                cm = False
            return self.volume_replication_mode(args[1], args[2], clear_metadata=cm)
        elif cmd in self.allowed_cmds:
                getattr(self, cmd)(*args[1:])
        else:
            raise ValueError("Unknown function called.")


def test():
    server = "https://192.168.220.1"
    password = "admin"

    filer1 = DSS_Scraper(server, password, debug = True)
    filer1.login()
    filer1.logout()

if __name__ == "__main__":
    test()