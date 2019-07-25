from __future__ import print_function
import ConfigParser
import logging
import threading
import subprocess
import time
import xmlrpclib
import re
import State
import TreeNode
from Detector import Detector
from NovaClient import NovaClient


class Diagnoser:

    def __init__(self, binary_tree, detector):
        self.binary_tree = binary_tree
        self.root = self.binary_tree.get_data()
        self.detector = detector
        self.detector_list = [None, self.detector.checkPowerStatus, self.detector.checkOSStatus,
                             self.detector.checkNetworkStatus, self.detector.checkServiceStatus]
        self.root_cause_list = [None, "power", "os",
                              "network", "service"]
        #self.detector_list = [None, 1,2,3,4,5,6,7]

    def detect(self):
        while True():
            root_cause = self.diagnosis()
            return root_cause

    def diagnosis(self, fault = None):
        last_detector_number = None
        last_result = None
        while True:
            # time.sleep(1)
            # get next detector
            if last_detector_number is None:
                detector = self.detector_list[self.root]
            else:
                if last_result is None:
                    print ("diagnosis error")
                    return
                else:
                    last_node = self.binary_tree.get_node_by_data(last_detector_number)
                    if last_result == False:
                        print(last_node)
                        next_node = last_node.get_right_node()
                        if next_node is None:
                            root_cause = last_node.get_data()+1
                            return self.root_cause_list[root_cause]
                    elif last_result == True:
                        next_node = last_node.get_left_node()
                        if next_node is None:
                            root_cause = last_node.get_data()
                            return self.root_cause_list[root_cause]
                    detector_number = next_node.get_data()
                    detector = self.detector_list[detector_number]
            # detect next node
            if fault is not None:
                if fault <= detector:
                    last_result =  True
                elif fault > detector:
                    last_result =  False
            else:
                result = detector()
                if result == State.HEALTH:
                    last_result = False
                else:
                    last_result = True
            last_detector_number = self.detector_list.index(detector)
