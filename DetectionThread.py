#########################################################
#:Date: 2017/12/13
#:Version: 1
#:Authors:
#    - Elma Huang <huanghuei0206@gmail.com>
#    - LSC <sclee@g.ncu.edu.tw>
#:Python_Version: 2.7
#:Platform: Unix
#:Description:
#   This is a class which detects whether computing nodes happens error or not.
##########################################################


from __future__ import print_function

import ConfigParser
import logging
import threading
import time
import xmlrpclib
import re

import State
from Detector import Detector
from TreeNode import TreeNode
from Diagnoser import Diagnoser

class DetectionThread(threading.Thread):
    def __init__(self, cluster_id, node, port, polling_interval):
        threading.Thread.__init__(self)
        self.node = node
        self.cluster_id = cluster_id
        self.ipmi_status = node.ipmi_status
        self.polling_interval = polling_interval
        self.loop_exit = False
        self.config = ConfigParser.RawConfigParser()
        self.config.read('hass.conf')
        self.detector = Detector(node, port)
        self.tree = self.set_tree()
        self.diagnoser = Diagnoser(self.tree, self.detector)
        self.function_map = [self.detector.checkPowerStatus, self.detector.checkOSStatus,
                             self.detector.checkNetworkStatus, self.detector.checkServiceStatus]
        self.authUrl = "http://" + self.config.get("rpc", "rpc_username") + ":" + self.config.get("rpc",
                                                                                                  "rpc_password") + \
                       "@127.0.0.1:" + self.config.get(
            "rpc", "rpc_bind_port")
        self.server = xmlrpclib.ServerProxy(self.authUrl)

    def set_tree(self):
        tree = TreeNode(3)
        tree.insert(1)
        tree.insert(2)
        return tree

    def run(self):
        while not self.loop_exit:
            state = self.detect()
            print("[" + self.node.name + "] " + state)

            if state != State.HEALTH:
                f = open("/home/controller/newLog","a")
                f.write("%d " % (time.time()*1000))
                f.close()
        
                logging.error("[" + self.node.name + "] " + state)
                try:
                    recover_success = self.server.recover(state, self.cluster_id, self.node.name)
                    if recover_success:  # recover success
                        print("recover success")
                        self.detector.connect()
                    else:  # recover fail(False) or get cluster fail(none)
                        print("recover fail delete node %s from the cluster" % self.node.name)
                        self.server.deleteNode(self.cluster_id, self.node.name)
                        self.stop()
                except Exception as e:
                    print("Exception : " + str(e))
                    self.stop()
                self.server.updateDB()
            time.sleep(self.polling_interval)

    def stop(self):
        self.loop_exit = True

    def detect(self):
        highest_level_check = self.function_map[-1]
        if self.detector.checkSensorStatus() != State.HEALTH:
            return State.SENSOR_FAIL
        if highest_level_check() != State.HEALTH:
            state = self.verify(highest_level_check)
            return state
        return State.HEALTH

    def verify(self, func):
        fail_state = self.diagnoser.diagnosis()
        print(fail_state)
        return fail_state

if __name__ == "__main__":
    config = ConfigParser.RawConfigParser()
    config.read('hass.conf')
    authUrl = "http://" + config.get("rpc", "rpc_username") + ":" + config.get("rpc",
                                                                               "rpc_password") + "@127.0.0.1:" \
              + config.get(
        "rpc", "rpc_bind_port")
    server = xmlrpclib.ServerProxy(authUrl)
    server.test()


