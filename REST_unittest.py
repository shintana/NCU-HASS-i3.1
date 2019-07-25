import unittest
import httplib
import urllib
import xmlrpclib
import ConfigParser
import json
import HASS_RESTful
from Hass import Hass

config = ConfigParser.RawConfigParser()
config.read('/etc/hass.conf')

REST_host = config.get("RESTful","host")
REST_port = int(config.get("RESTful","port"))

rpc_username = config.get("rpc","rpc_username")
rpc_password = config.get("rpc","rpc_password")
rpc_port = int(config.get("rpc","rpc_bind_port"))

openstack_user_name = config.get("openstack", "openstack_admin_account")
openstack_domain = config.get("openstack", "openstack_user_domain_id")
openstack_password = config.get("openstack", "openstack_admin_password")

keystone_port = int(config.get("keystone_auth","port"))

# get RPC connection to HASS
auth_url = "http://%s:%s@127.0.0.1:%s" % (rpc_username, rpc_password, rpc_port)
server = xmlrpclib.ServerProxy(auth_url)

#get openstack access token
data = '{ "auth": { "identity": { "methods": [ "password" ], "password": { "user": { "name": \"%s\", "domain": { "name": \"%s\" }, "password": \"%s\" } } } } }' % (openstack_user_name, openstack_domain, openstack_password)
headers = {"Content-Type": "application/json"}
http_client = httplib.HTTPConnection(REST_host, keystone_port, timeout=30)
http_client.request("POST", "/v3/auth/tokens", body=data, headers=headers)
token = http_client.getresponse().getheaders()[1][1]

#token = "gAAAAABauLthXBbVmUZsg2ZkaioPdJDmY00s07Esz85chANS9PB8EDOksS2DmNyuGDD6tKfVkN9I6hh7s9pRIfUYM6UTO7LbwwNzWwLcrClPAGbmn2k3gbcuIrMJ3eZLeJQzdbd9djfayS0njFxZQgeRNZMenq6UrQ"

# set up global headers
headers = {'Content-Type' : 'application/json',
		   'X-Auth-Token' : token}

# message declaration
MESSAGE_OK = 'succeed'
MESSAGE_FAIL = 'failed'

app = HASS_RESTful.app.test_client()
HASS = Hass()
HASS_RESTful.RESTfulThread(HASS)

# global function for reset HASS
def HASS_reset():
	cluster_list = HASS.listCluster()
	for cluster in cluster_list:
		HASS.deleteCluster(cluster["cluster_id"])

class ClusterTest(unittest.TestCase):
	# set up before every test case runinng.
	def setUp(self):
		self.conn = httplib.HTTPConnection(REST_host, REST_port, timeout=30)
		self.cluster_name = 'test'

	def test_xxx(self):
		data = {"cluster_name": self.cluster_name}
		data = json.dumps(data)
		res = app.post("/HASS/api/cluster", data =data, headers=headers)
		#res = app.get("/HASS/api/clusters", headers=headers, follow_redirects=True)

	def test_create_cluster(self):
		# perform http request
		data = {"cluster_name": self.cluster_name}
		data = json.dumps(data)
		self.conn.request("POST", "/HASS/api/cluster", body=data, headers=headers)
		response = json.loads(self.conn.getresponse().read())

		# assert equal
		self.assertEqual(response["code"], MESSAGE_OK)
		self.assertEqual(len(server.listCluster()), 1)

	def test_create_cluster_overlapping_name(self):
		# create cluster first
		server.createCluster(self.cluster_name) 

		# perform http request
		data = {"cluster_name": self.cluster_name}
		data = json.dumps(data)
		self.conn.request("POST", "/HASS/api/cluster", body=data, headers=headers)
		response = json.loads(self.conn.getresponse().read())

		# assert equal
		self.assertEqual(response["code"], MESSAGE_FAIL)
		self.assertEqual(len(server.listCluster()), 1)

	def test_create_cluster_lack_post_arguments(self):
		# perform http request
		data = None
		self.conn.request("POST", "/HASS/api/cluster", body=data, headers=headers)
		response = json.loads(self.conn.getresponse().read())
		# assert equal
		self.assertEqual(response["code"], MESSAGE_FAIL)
		self.assertEqual(len(server.listCluster()), 0)

	def test_delete_cluster(self):
        	res = server.createCluster(self.cluster_name)
		cluster_id = res["data"]["clusterId"]

	        # perform http request
	        data = {"cluster_id": cluster_id}
	        data = json.dumps(data)
	        endpoint = "/HASS/api/cluster?cluster_id=%s" % cluster_id
	        self.conn.request("DELETE", endpoint, body=data, headers=headers)
	        response = json.loads(self.conn.getresponse().read())

	        # assert equal
	        self.assertEqual(response["code"], MESSAGE_OK)
	        self.assertEqual(len(server.listCluster()), 0)

	def test_non_exist_cluster_id(self):
        	res = server.createCluster(self.cluster_name)
        	cluster_id = res["data"]["clusterId"]
		newCluster_id = "123456"

        	# perform http request
        	data = {"cluster_id": newCluster_id}
        	data = json.dumps(data)
        	endpoint = "/HASS/api/cluster?cluster_id=%s" % newCluster_id
        	self.conn.request("DELETE", endpoint, body=data, headers=headers)
        	response = json.loads(self.conn.getresponse().read())

        	# assert equal
        	self.assertEqual(response["code"], MESSAGE_FAIL)
        	self.assertEqual(len(server.listCluster()), 1)

	def test_delete_cluster_lack_post_arguments(self):
        	# perform ttp request
        	data = None
        	data = json.dumps(data)
        	endpoint = "/HASS/api/cluster"
        	self.conn.request("DELETE", endpoint, body=data, headers=headers)
        	response = json.loads(self.conn.getresponse().read())

        	# assert equal
        	self.assertEqual(response["code"], MESSAGE_FAIL)
        	self.assertEqual(len(server.listCluster()), 0)

	def test_list_cluster(self):
        	server.createCluster(self.cluster_name)
        	server.createCluster('test2')

        	# perform http request
        	data = None
        	data = json.dumps(data)
        	self.conn.request("GET", "/HASS/api/clusters", body=data, headers=headers)
        	response = json.loads(self.conn.getresponse().read())

        	# assert equal
        	self.assertEqual(response["code"], MESSAGE_OK)
        	self.assertEqual(len(server.listCluster()), 2)
	
	# clean the data after test case end.
	def tearDown(self):
		self.conn.close()
		HASS_reset()

class NodeTest(unittest.TestCase):
	# set up before every test case runinng.
        def setUp(self):
                self.conn = httplib.HTTPConnection(REST_host, REST_port, timeout=30)
                self.cluster_name = 'test'

	def test_add_node(self):
        	res = server.createCluster(self.cluster_name)
        	cluster_id = res["data"]["clusterId"]
        	node_list = ["compute1","compute2"]

        	# perform http request
        	data = {"cluster_id": cluster_id,"node_list": node_list}
        	data = json.dumps(data)
        	self.conn.request("POST", "/HASS/api/node", body=data, headers=headers)
        	response = json.loads(self.conn.getresponse().read())
		nodeList = response["data"]["node"]

        	# assert equal
        	self.assertEqual(response["code"], MESSAGE_OK)
        	self.assertEqual(len(nodeList), 2)
	
	def test_add_node_not_in_compute_pool(self):
        	res = server.createCluster(self.cluster_name)
        	cluster_id = res["data"]["clusterId"]

        	# perform http request
        	data = {"cluster_id": cluster_id,"node_list": "compute3"}
        	data = json.dumps(data)
        	self.conn.request("POST", "/HASS/api/node", body=data, headers=headers)
        	response = json.loads(self.conn.getresponse().read())
		nodeList = response["data"]["node"]
		
        	# assert equal
        	self.assertEqual(response["code"], MESSAGE_FAIL)
        	self.assertEqual(len(nodeList), 0)

	def test_add_node_not_exist_cluster_id(self):
        	res = server.createCluster(self.cluster_name)
        	cluster_id = res["data"]["clusterId"]
        	node_list = ["compute1"]

        	# perform http request
        	data = {"cluster_id": '123',"node_list": node_list}
        	data = json.dumps(data)
        	self.conn.request("POST", "/HASS/api/node", body=data, headers=headers)
        	response = json.loads(self.conn.getresponse().read())        	
		
		node_list = server.listNode(cluster_id)
                count_node_list = node_list["data"]["nodeList"]

        	# assert equal
        	self.assertEqual(response["code"], MESSAGE_FAIL)
		self.assertEqual(len(count_node_list),0)
	
	def test_add_node_lack_post_arguments(self):
        	# perform http request
        	data = None
        	data = json.dumps(data)
        	self.conn.request("POST", "/HASS/api/node", body=data, headers=headers)
        	response = json.loads(self.conn.getresponse().read())

        	# assert equal
        	self.assertEqual(response["code"], MESSAGE_FAIL)

	def test_delete_node(self):
        	node_name = "compute1"
        	res = server.createCluster(self.cluster_name)
        	cluster_id = res["data"]["clusterId"]
		addnode = server.addNode(cluster_id,[node_name])
		
        	# perform http request
        	data = {"cluster_id": cluster_id,"node_name": node_name}
        	data = json.dumps(data)
        	endpoint = "/HASS/api/node?cluster_id=%s&&node_name=%s" % (cluster_id,node_name)
        	self.conn.request("DELETE", endpoint, body=data, headers=headers)
        	response = json.loads(self.conn.getresponse().read())
        	node_list = server.listNode(cluster_id)
		count_node_list = node_list["data"]["nodeList"]

        	# assert equal
        	self.assertEqual(response["code"], MESSAGE_OK)
        	self.assertEqual(len(count_node_list), 0)

	def test_delete_node_not_in_node_list(self):
        	res = server.createCluster(self.cluster_name)
        	cluster_id = res["data"]["clusterId"]
        	node_name = "compute3"

        	# perform http request
        	data = {"cluster_id": cluster_id,"node_name": node_name}
        	data = json.dumps(data)
        	endpoint = "/HASS/api/node?cluster_id=%s&&node_name=%s" % (cluster_id, node_name)
        	self.conn.request("DELETE", endpoint, body=data, headers=headers)
        	response = json.loads(self.conn.getresponse().read())
		node_list = server.listNode(cluster_id)
                count_node_list = node_list["data"]["nodeList"]

        	# assert equal
        	self.assertEqual(response["code"], MESSAGE_FAIL)
        	self.assertEqual(len(count_node_list), 0)

	def test_delete_node_not_exist_cluster_id(self):
        	res = server.createCluster(self.cluster_name)
        	cluster_id = res["data"]["clusterId"]
		newClusterID = "12345"
        	node_name = "compute1"

        	# perform http request
        	data = {"cluster_id": newClusterID,"node_name": node_name}
        	data = json.dumps(data)
        	endpoint = "/HASS/api/node?cluster_id=%s&&node_name=%s" % (newClusterID, node_name)
        	self.conn.request("DELETE", endpoint, body=data, headers=headers)
        	response = json.loads(self.conn.getresponse().read())

		node_list = server.listNode(cluster_id)
                count_node_list = node_list["data"]["nodeList"]

        	# assert equal
        	self.assertEqual(response["code"], MESSAGE_FAIL)
		self.assertEqual(len(count_node_list), 0)
    
	def test_delete_node_lack_post_arguments(self):
        	# perform http request
        	data = None
        	data = json.dumps(data)
        	endpoint = "/HASS/api/node"
        	self.conn.request("DELETE", endpoint, body=data, headers=headers)
        	response = json.loads(self.conn.getresponse().read())
		
        	# assert equal
        	self.assertEqual(response["code"], MESSAGE_FAIL)
		
	def test_list_node(self):
		node_list = ["compute1"]
        	res = server.createCluster(self.cluster_name)
        	cluster_id = res["data"]["clusterId"]
		addnode = server.addNode(cluster_id,node_list)

        	# perform http request
        	data = {"cluster_id": cluster_id}
        	data = json.dumps(data)
        	endpoint = "/HASS/api/nodes/%s" % cluster_id
        	self.conn.request("GET", endpoint, body=data, headers=headers)
        	response = json.loads(self.conn.getresponse().read())
		for nodelist in response["data"]["nodeList"]:
			n = nodelist["node_name"].split()

        	# assert equal
        	self.assertEqual(response["code"], MESSAGE_OK)
        	self.assertEqual(len(n),1)

	def test_list_node_not_exist_cluster_id(self):
        	res = server.createCluster(self.cluster_name)
		cluster_id = res["data"]["clusterId"]
        	newClusterID = "12345"

        	# perform http request
        	data = {"cluster_id": cluster_id}
        	data = json.dumps(data)
        	endpoint = "/HASS/api/nodes/%s" % newClusterID
        	self.conn.request("GET", endpoint, body=data, headers=headers)
        	response = json.loads(self.conn.getresponse().read())

		node_list = server.listNode(res["data"]["clusterId"])
                count_node_list = node_list["data"]["nodeList"]

        	# assert equal
        	self.assertEqual(response["code"], MESSAGE_FAIL)
        	self.assertEqual(len(count_node_list), 0)

	# clean the data after test case end.
        def tearDown(self):
                self.conn.close()
                HASS_reset()


class InstanceTest(unittest.TestCase):
    	# set up before every test case runinng.
    	def setUp(self):
        	self.conn = httplib.HTTPConnection(REST_host, REST_port, timeout=30)
        	self.cluster_name = 'test'

	def test_add_instance(self):
        	res = server.createCluster(self.cluster_name)
        	cluster_id = res["data"]["clusterId"]
		server.addNode(cluster_id,["compute1"])
        	instance_id = "b6e95aa3-79f0-4edd-9a63-deb4d884b191"

        	# perform http request
        	data = {"cluster_id": cluster_id, "instance_id": instance_id}
        	data = json.dumps(data)
        	self.conn.request("POST", "/HASS/api/instance", body=data, headers=headers)
        	response = json.loads(self.conn.getresponse().read())

		listinstance = server.listInstance(cluster_id)
		for instance in listinstance["data"]["instanceList"]:
        		i = instance["name"].split()

        	# assert equal
        	self.assertEqual(response["code"], MESSAGE_OK)
        	self.assertEqual(len(i), 1)
	
	def test_add_instance_overlapping(self):
        	res = server.createCluster(self.cluster_name)
        	cluster_id = res["data"]["clusterId"]
		server.addNode(cluster_id,["compute1"])
        	instance_id = "b6e95aa3-79f0-4edd-9a63-deb4d884b191"
        	server.addInstance(cluster_id,instance_id)

        	# perform http request
        	data = {"cluster_id": cluster_id, "instance_id": instance_id}
        	data = json.dumps(data)
        	self.conn.request("POST", "/HASS/api/instance", body=data, headers=headers)
        	response = json.loads(self.conn.getresponse().read())

		listinstance = server.listInstance(cluster_id)
                for instance in listinstance["data"]["instanceList"]:
                        i = instance["name"].split()

        	# assert equal
        	self.assertEqual(response["code"], MESSAGE_FAIL)
        	self.assertEqual(len(i), 1)
	
	def test_add_instance_overlapping_different_cluster(self):
        	res = server.createCluster(self.cluster_name)
        	cluster_id = res["data"]["clusterId"]
		server.addNode(cluster_id,["compute1"])
        	res2 = server.createCluster("test2")
        	cluster_id2 = res2["data"]["clusterId"]
		server.addNode(cluster_id2,["compute2"])
        	instance_id = "b6e95aa3-79f0-4edd-9a63-deb4d884b191"
        	server.addInstance(cluster_id,instance_id)

        	# perform http request
        	data = {"cluster_id": cluster_id2, "instance_id": instance_id}
        	data = json.dumps(data)
        	self.conn.request("POST", "/HASS/api/instance", body=data, headers=headers)
        	response = json.loads(self.conn.getresponse().read())
	
		listinstance = server.listInstance(cluster_id)
		if len(listinstance["data"]["instanceList"]) > 0:
                	for instance in listinstance["data"]["instanceList"]:
                        	i = instance["name"].split()
		else:
			i = []

		listinstance2 = server.listInstance(cluster_id2)
		if len(listinstance2["data"]["instanceList"]) > 0:
                        for instance in listinstance2["data"]["instanceList"]:
                                j = instance["name"].split()
                else:
                        j = []

        	# assert equal
        	self.assertEqual(response["code"], MESSAGE_FAIL)
        	self.assertEqual(len(i), 1)
        	self.assertEqual(len(j), 0)
	
	def test_add_instance_non_exist_cluster_id(self):
        	res = server.createCluster(self.cluster_name)
        	cluster_id = res["data"]["clusterId"]
		server.addNode(cluster_id,["compute1"])
		instance_id = "b6e95aa3-79f0-4edd-9a63-deb4d884b191"

        	# perform http request
        	data = {"cluster_id": "123456", "instance_id": instance_id}
        	data = json.dumps(data)
        	self.conn.request("POST", "/HASS/api/instance", body=data, headers=headers)
        	response = json.loads(self.conn.getresponse().read())

		listinstance = server.listInstance(cluster_id)
		if len(listinstance["data"]["instanceList"]) > 0:
                        for instance in listinstance["data"]["instanceList"]:
                                i = instance["name"].split()
                else:
                        i = []

        	# assert equal
        	self.assertEqual(response["code"], MESSAGE_FAIL)
		self.assertEqual(len(i), 0)

	def test_add_instance_not_exist_instance_id(self):
		res = server.createCluster(self.cluster_name)
                cluster_id = res["data"]["clusterId"]
                server.addNode(cluster_id,["compute1"])
                instance_id = "123"

                # perform http request
                data = {"cluster_id": cluster_id, "instance_id": instance_id}
                data = json.dumps(data)
                self.conn.request("POST", "/HASS/api/instance", body=data, headers=headers)
                response = json.loads(self.conn.getresponse().read())
		
		listinstance = server.listInstance(cluster_id)
                if len(listinstance["data"]["instanceList"]) > 0:
                        for instance in listinstance["data"]["instanceList"]:
                                i = instance["name"].split()
                else:
                        i = []

                # assert equal
                self.assertEqual(response["code"], MESSAGE_FAIL)
		self.assertEqual(len(i), 0)

	def test_add_instance_poweroff(self):
		res = server.createCluster(self.cluster_name)
                cluster_id = res["data"]["clusterId"]
                server.addNode(cluster_id,["compute1"])
                instance_id = "cd8ced53-9d3b-4208-8d19-250e6f8ab9c9"

                # perform http request
                data = {"cluster_id": cluster_id, "instance_id": instance_id}
                data = json.dumps(data)
                self.conn.request("POST", "/HASS/api/instance", body=data, headers=headers)
                response = json.loads(self.conn.getresponse().read())

		listinstance = server.listInstance(cluster_id)
                if len(listinstance["data"]["instanceList"]) > 0:
                        for instance in listinstance["data"]["instanceList"]:
                                i = instance["name"].split()
                else:
                        i = []

                # assert equal
                self.assertEqual(response["code"], MESSAGE_FAIL)
		self.assertEqual(len(i),0)

	def test_add_instance_not_have_volume(self):
        	res = server.createCluster(self.cluster_name)
                cluster_id = res["data"]["clusterId"]
                server.addNode(cluster_id,["compute1"])
                instance_id = "a7c7a897-8904-4d54-b124-65b117cd3f78"

                # perform http request
                data = {"cluster_id": cluster_id, "instance_id": instance_id}
                data = json.dumps(data)
                self.conn.request("POST", "/HASS/api/instance", body=data, headers=headers)
                response = json.loads(self.conn.getresponse().read())

		listinstance = server.listInstance(cluster_id)
                if len(listinstance["data"]["instanceList"]) > 0:
                        for instance in listinstance["data"]["instanceList"]:
                                i = instance["name"].split()
                else:
                        i = []

                # assert equal
                self.assertEqual(response["code"], MESSAGE_FAIL)
		self.assertEqual(len(i),0)

	def test_add_instance_lack_post_arguments(self):
		# perform http request
                data = None
                data = json.dumps(data)
                self.conn.request("POST", "/HASS/api/instance", body=data, headers=headers)
                response = json.loads(self.conn.getresponse().read())

                # assert equal
                self.assertEqual(response["code"], MESSAGE_FAIL)	

	def test_list_instance(self):
                res = server.createCluster(self.cluster_name)
                cluster_id = res["data"]["clusterId"]
                addnode = server.addNode(cluster_id,["compute1"])
        	instance_id = "b6e95aa3-79f0-4edd-9a63-deb4d884b191"
                server.addInstance(cluster_id,instance_id)

        	# perform http request
        	data = {"cluster_id": cluster_id}
        	data = json.dumps(data)
        	endpoint = "/HASS/api/instances/%s" % cluster_id
        	self.conn.request("GET", endpoint, body=data, headers=headers)
        	response = json.loads(self.conn.getresponse().read())

                for instance in response["data"]["instanceList"]:
                        i = instance["name"].split()

        	# assert equal
        	self.assertEqual(response["code"], MESSAGE_OK)
        	self.assertEqual(len(i), 1)
	
	def test_delete_instance(self):
        	res = server.createCluster(self.cluster_name)
        	cluster_id = res["data"]["clusterId"]
		server.addNode(cluster_id,["compute1"])
        	instance_id = "b6e95aa3-79f0-4edd-9a63-deb4d884b191"
		server.addInstance(cluster_id,instance_id)

        	# perform http request
        	data = {"cluster_id": cluster_id, "instance_id": instance_id}
        	data = json.dumps(data)
        	endpoint = "/HASS/api/instance?cluster_id=%s&&instance_id=%s" % (cluster_id, instance_id)
        	self.conn.request("DELETE", endpoint, body=data, headers=headers)
        	response = json.loads(self.conn.getresponse().read())
		
		listinstance = server.listInstance(cluster_id)
                if len(listinstance["data"]["instanceList"]) > 0:
                        for instance in listinstance["data"]["instanceList"]:
                                i = instance["name"].split()
                else:
                        i = []

        	# assert equal
        	self.assertEqual(response["code"], MESSAGE_OK)
        	self.assertEqual(len(i), 0)
   	
	def test_delete_instance_non_exist_cluster_id(self):
        	res = server.createCluster(self.cluster_name)
        	cluster_id = res["data"]["clusterId"]
		newClusterID = "12345"
		server.addNode(cluster_id,["compute1"])
        	instance_id = "b6e95aa3-79f0-4edd-9a63-deb4d884b191"

        	# perform http request
        	data = {"cluster_id": newClusterID, "instance_id": instance_id}
        	data = json.dumps(data)
        	endpoint = "/HASS/api/instance?cluster_id=%s&&instance_id=%s" % (newClusterID, instance_id)
        	self.conn.request("DELETE", endpoint, body=data, headers=headers)
        	response = json.loads(self.conn.getresponse().read())
		
		listinstance = server.listInstance(cluster_id)
                if len(listinstance["data"]["instanceList"]) > 0:
                        for instance in listinstance["data"]["instanceList"]:
                                i = instance["name"].split()
                else:
                        i = []

        	# assert equal
        	self.assertEqual(response["code"], MESSAGE_FAIL)
		self.assertEqual(len(i),0)        	
	
	def test_delete_instance_non_protected_instance_id(self):
        	res = server.createCluster(self.cluster_name)
        	cluster_id = res["data"]["clusterId"]
		server.addNode(cluster_id,["compute1"])
        	instance_id = "234"

        	# perform http request
        	data = {"cluster_id": cluster_id, "instance_id": instance_id}
        	data = json.dumps(data)
        	endpoint = "/HASS/api/instance?cluster_id=%s&&instance_id=%s" % (cluster_id, instance_id)
        	self.conn.request("DELETE", endpoint, body=data, headers=headers)
        	response = json.loads(self.conn.getresponse().read())

		listinstance = server.listInstance(cluster_id)
                if len(listinstance["data"]["instanceList"]) > 0:
                        for instance in listinstance["data"]["instanceList"]:
                                i = instance["name"].split()
                else:
                        i = []

        	# assert equal
        	self.assertEqual(response["code"], MESSAGE_FAIL)
        	self.assertEqual(len(i), 0)
	
	def test_delete_instance_lack_post_arguments(self):
        	# perform http request
        	data = None
        	data = json.dumps(data)
        	endpoint = "/HASS/api/instance"
        	self.conn.request("DELETE", endpoint, body=data, headers=headers)
        	response = json.loads(self.conn.getresponse().read())

        	# assert equal
        	self.assertEqual(response["code"], MESSAGE_FAIL)

	def tearDown(self):
        	self.conn.close()
        	HASS_reset()	


if __name__ == '__main__':
	unittest.main()
