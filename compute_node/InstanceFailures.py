##########################################################
#:Date: 2018/2/12
#:Version: 1
#:Authors:
#    - Elma Huang <huanghuei0206@gmail.com>
#    - LSC <sclee@g.ncu.edu.tw>
#:Python_Version: 2.7
#:Platform: Unix
#:Description:
#   This is a class which detects whether virtual machine happens error or not.
###########################################################


from __future__ import print_function

import logging
import subprocess
import sys
import threading
import time

import libvirt

# import ConfigParse
import InstanceEvent
from HAInstance import HAInstance
from NovaClient import NovaClient
from RecoveryInstance import RecoveryInstance


class InstanceFailure(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.nova_client = NovaClient.get_instance()
        self.recovery_vm = RecoveryInstance()
        self.libvirt_uri = "qemu:///system"
        HAInstance.update_ha_instance()

    def __virEventLoopNativeRun(self):
        while True:
            libvirt.virEventRunDefaultImpl()

    def run(self):
        while True:
            try:
                self.create_libvirt_detection_thread()
                libvirt_connection = self.getLibvirtConnection()
                # time.sleep(5)
                libvirt_connection.domainEventRegister(self._check_vm_state, None)  # event handler(callback,self)
                libvirt_connection.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_WATCHDOG,
                                                          self._check_vm_watchdog, None)
                # Adds a callback to receive notifications of arbitrary domain events occurring on a domain.
                while True:
                    self._check_network()
                    time.sleep(5)
                    if not self.check_libvirt_connect(libvirt_connection):  # 1 if alive, 0 if dead, -1 on error
                        break

            except Exception as e:
                message = "failed to run detection method , please check libvirt is alive.exception :" + str(e)
                logging.error(message)
                sys.exit(1)

    def create_libvirt_detection_thread(self):
        try:
            # set event loop thread
            libvirt.virEventRegisterDefaultImpl()
            event_loop_thread = threading.Thread(target = self.__virEventLoopNativeRun, name = "libvirtEventLoop")
            event_loop_thread.setDaemon(True)
            event_loop_thread.start()
        except Exception as e:
            message = "failed to create libvirt detection thread " + str(e)
            print(message)
            logging.error(message)

    def check_libvirt_connect(self, connection):
        """

        :param connection:
        :return:
        """
        try:
            if connection.isAlive() == 1:
                return True
            else:
                return False
        except Exception as e:
            mes = "fail to check libvirt connection isAlive()" + str(e)
            connection.close()
            logging.error(mes)
            return False

    def getLibvirtConnection(self):
        try:
            connection = libvirt.openReadOnly(self.libvirt_uri)
            if connection is None:
                print("failed to open connection to qemu:///system")
            else:
                return connection
        except Exception as e:
            message = "failed to open connection --exception" + str(e)
            print(message)
            logging.error(message)

    def _check_vm_state(self, connect, domain, event, detail, opaque):
        # event:column,detail:row
        start_detect_vm_state = time.time()
        print("start vm state: ", start_detect_vm_state)
        print("domain name :", domain.name(), " domain id :", domain.ID(), "event:", event, "detail:", detail)
        event_string = self.transform_detail_to_string(event, detail)
        print("state event string :", event_string)
        recovery_type = self._find_failure(event_string, domain.name())
        if recovery_type != "":
            fail_instance = [domain.name(), event_string, recovery_type]
            logging.info(str(fail_instance))
            start_recover_vm_state = time.time()
            print("start recover vm : ", start_recover_vm_state)
            result = self.recover_failed_instance(fail_instance = fail_instance)
            finish_recover_vm_state = time.time()
            print("finish recover vm : ", finish_recover_vm_state)
            print(self.show_result(result))

    def _find_failure(self, event_string, domain_name):
        recovery_type = ""
        if self._check_vm_crash(event_string):
            recovery_type = "Crash"
            return recovery_type
        elif self._check_vm_migrated(event_string):
            recovery_type = "Migration"
            return recovery_type
        elif self._check_vm_destroyed(event_string, domain_name):
            recovery_type = "Delete"
            # time.sleep(5)
        return recovery_type

    def _check_vm_crash(self, event_string):
        failed_string = InstanceEvent.Event_failed
        if event_string in failed_string:
            print("crash--state event string :", event_string)
            return True
        return False

    def _check_vm_destroyed(self, event_string, instance_name):
        destroyed_string = InstanceEvent.Event_destroyed
        if event_string in destroyed_string:
            print("destroy--state event string :", event_string)
            return self.check_destroy_state(instance_name)
            # return True
        # return False

    def _check_vm_migrated(self, event_string):
        migrated_string = InstanceEvent.Event_migrated
        if "Migrated" in event_string and event_string in migrated_string:
            print("migrate--state event string :", event_string)
            time.sleep(5)
            return True
        return False

    def _check_network(self):
        start_detect_vm_net = time.time()
        print("start detect vm net: ", start_detect_vm_net)
        recovery_type = "Network"
        ha_instance_list = HAInstance.get_instance_list()
        if not ha_instance_list:
            return
        for ha_instance in ha_instance_list:
            if not ha_instance.network_provider:
                return
            ip = ha_instance.network_provider[0]
            print("check net %s" % ip)
            if not self.ping_instance(ip):
                if self.check_network_down(ha_instance):
                    fail_instance = [ha_instance.name, ip, recovery_type]
                    # print fail_instance
                    start_recover_vm_net = time.time()
                    print("start recover vm net: ", start_recover_vm_net)
                    result = self.recover_failed_instance(fail_instance = fail_instance)
                    finish_recover_vm_net = time.time()
                    print("finsh recover vm net: ", finish_recover_vm_net)
                    print(self.show_result(result))

    def _check_vm_watchdog(self, connect, domain, action, opaque):
        print("domain name:", domain.name(), " domain id:", domain.ID(), "action:", action)
        start_detect_vm_state = time.time()
        print("start vm watchdog: ", start_detect_vm_state)
        recovery_type = "Watchdog"
        watchdog_string = InstanceEvent.Event_watchdog_action
        if action in watchdog_string:
            fail_instance = [domain.name(), action, recovery_type]
            result = self.recover_failed_instance(fail_instance = fail_instance)
            start_recover_vm_os = time.time()
            print("start recover vm os: ", start_recover_vm_os)
            print(self.show_result(result))

    def transform_detail_to_string(self, event, detail):
        """

        :param event: 
        :param detail: 
        :return: 
        """
        stateString = InstanceEvent.Event_string
        return stateString[event][detail]

    def recover_failed_instance(self, fail_instance):
        """

        :param fail_instance: 
        :return: 
        """
        # print "get ha vm"
        result = False
        print("start recover fail instance")
        print("update HA Instance")
        # HAInstance.update_ha_instance()  # for live migration host info
        ha_instance_list = HAInstance.get_instance_list()
        # check instance is protected
        if self.check_recovery_vm(fail_instance, ha_instance_list) or "Migration" in fail_instance[2]:  # True/None
            try:
                result = self.recovery_vm.recover_instance(fail_instance)
            except Exception as e:
                logging.error("InstanceFailures recover_failed_instance Except:" + str(e))
                print(str(e))
            finally:
                return result  # True/False
        else:
            return None

    def check_recovery_vm(self, failed_instance, ha_instance_list):
        """

        :param failed_instance: 
        :param ha_instance_list: 
        :return: 
        """
        # find all fail_vm in self.failed_instances is ha vm or not
        # print ha_instance_list
        result = None
        if not ha_instance_list:
            return result
        for ha_instance in ha_instance_list:
            if failed_instance[0] in ha_instance.name:
                result = True
        return result

    def check_destroy_state(self, instance_name):
        """

        :param instance_name: 
        :return: 
        """
        # instance = HAInstance.get_instance(instance_name)# not ha instance
        print("start check %s is destroyed or shutoff" % instance_name)
        time.sleep(5)
        return not self._instance_is_exist(instance_name)

    def check_network_down(self, instance, time_out = 5):
        """

        :param instance: 
        :param time_out: 
        :return: 
        """
        # check network state is down
        print("start to check network state second time")
        while time_out > 0:
            time.sleep(5)
            state = self.get_instance_state(instance.id)
            # maybe vm just be reboot
            # print("net state:", state)
            if state is not None and "ACTIVE" in state:
                # print("ip ?", instance.network_provider[0])
                network_state = self.ping_instance(instance.network_provider[0])
                # print("second ping :", network_state)
                if network_state:
                    # network state is not down
                    print("finish check net second time")
                    return False
                # network state is temporary down
                time_out -= 1
            else:
                # vm is deleted or shutoff
                print("finish check net second time")
                return False
        print("finish check net second time")
        return True

    def ping_instance(self, ip):
        """

        :param ip: 
        :return: 
        """
        try:
            response = subprocess.check_output(['timeout', '2', 'ping', '-c', '1', ip],
                                               stderr = subprocess.STDOUT,
                                               universal_newlines = True)
            print("ping %s success" % ip)
            return True
        except Exception as e:
            print("ping %s fail" % ip)
            # print("ping_instance--Exception:", str(e))
            return False

    def get_instance_state(self, instance_id):
        """

        :param instance_id: 
        :return: 
        """
        try:
            state = self.nova_client.get_instance_state(instance_id)
            return state
        except Exception as e:
            print("get_instance_state--Exception:", str(e))
            return None

    def _instance_is_exist(self, instance_name):
        all_instance = self.nova_client.get_all_instance_list()
        print("all vm :", all_instance)
        state = False
        for instance in all_instance:
            if getattr(instance, "OS-EXT-SRV-ATTR:instance_name") == instance_name:
                # print(getattr(instance, "OS-EXT-SRV-ATTR:instance_name"), " = ", instance_name,"?")
                state = True
        return state

    def show_result(self, result):
        """

        :param result: 
        :return: 
        """
        if result is None:
            return '\033[92m' + "[it is not HA instance] " + '\033[0m'
        elif result:
            return '\033[92m' + "[recover instance success] " + '\033[0m'
        elif not result:
            return '\033[91m' + "[recover instance fail] " + '\033[0m'
        else:
            return result


if __name__ == '__main__':
    a = InstanceFailure()
    a.start()
