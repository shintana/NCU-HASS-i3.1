import unittest
import httplib
import urllib
import xmlrpclib
import ConfigParser
import json

config = ConfigParser.RawConfigParser()
config.read('hass.conf')

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

# global function for reset HASS
def HASS_reset():
        cluster_list = server.listCluster()
        for cluster in cluster_list:
            server.deleteCluster(cluster["cluster_id"])

class ClusterTest(unittest.TestCase):
    # set up before every test case runinng.
    def setUp(self):
        self.conn = httplib.HTTPConnection(REST_host, REST_port, timeout=30)
        self.cluster_name = 'test'

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

    def tearDown(self):
        self.conn.close()
        HASS_reset()

if __name__ == '__main__':
    unittest.main()

