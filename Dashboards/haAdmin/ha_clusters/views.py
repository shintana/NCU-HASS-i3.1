from django.utils.translation import ugettext_lazy as _
from django.utils.datastructures import SortedDict
from django.core.urlresolvers import reverse_lazy

from horizon import tabs
from horizon import exceptions
from horizon import tables
from horizon import workflows


import logging
from openstack_dashboard import api

from openstack_dashboard.dashboards.haAdmin.ha_clusters import tables as project_tables
from openstack_dashboard.dashboards.haAdmin.ha_clusters \
    import workflows as ha_cluster_workflows

from openstack_dashboard.REST.RESTClient import RESTClient

import xmlrpclib

import ConfigParser
import MySQLdb, MySQLdb.cursors
from horizon import exceptions

LOG = logging.getLogger(__name__)

config = ConfigParser.RawConfigParser()
config.read('/refactor-HASS/hass.conf')

server = RESTClient.getInstance()

class Response(object):
	def __init__(self, code, message=None, data=None):
		self.code = code
		self.message = message
		self.data = data

class Cluster:
    def __init__(self, cluster_name, id, computing_node_number, instance_number):
	self.id = id
	self.cluster_name = cluster_name
	self.computing_node_number = computing_node_number
	self.instance_number = instance_number

class ComputingNode:
    def __init__(self, id, computing_node_name, instance_number):
	self.id = id
	self.computing_node_name = computing_node_name
	self.instance_number = instance_number

class IndexView(tables.DataTableView):
    table_class = project_tables.ClustersTable
    template_name = 'haAdmin/ha_clusters/index.html'
    page_title = _("HA_Clusters")
    #LOG.error("aaaaaaaaaaaaaaaa")
    #
    #
    '''
    authUrl = "http://user:0928759204@127.0.0.1:61209"
    server = xmlrpclib.ServerProxy(authUrl)
    result = server.listCluster()
    for cluster in result:
        uuid = cluster[0]
	LOG.error(uuid)
        node_infoo = server.listInstance(uuid)["instanceList"]
        LOG.error(node_infoo)
	LOG.error(len(node_infoo))
    '''
    #        
    #         
    def get_data(self):
	authUrl = "http://user:0928759204@127.0.0.1:61209"
	#server = xmlrpclib.ServerProxy(authUrl)
	result = server.list_cluster()["data"]
	clusters = []
	for cluster in result:
	    node_info = []
	    instance_info = []
	    uuid = cluster["cluster_id"]
	    name = cluster["cluster_name"]
	    node_number = 0
	    instance_number = 0
	    node_info = server.list_node(uuid)
	    node_info = Response(code=node_info["code"], message=node_info["message"], data=node_info["data"])
	    if (node_info != "" ):
		node_number = len(node_info.data.get("nodeList"))
	    instance_info = server.list_instance(uuid)
            instance_info = Response(code=instance_info["code"], message=instance_info["message"], data=instance_info["data"])
	    if (instance_info != ""):
		instance_number = len(instance_info.data.get("instanceList"))
	    clusters.append(Cluster(name, uuid, node_number, instance_number))
        return clusters

class DetailView(tables.DataTableView):
    table_class = project_tables.ClusterDetailTable
    template_name = 'haAdmin/ha_clusters/detail.html'
    page_title = _("HA Cluster (uuid:{{cluster_id}})") 
    def get_data(self):
	authUrl = "http://user:0928759204@127.0.0.1:61209"
        #server = xmlrpclib.ServerProxy(authUrl)
        result = server.list_node(self.kwargs["cluster_id"])
	result = Response(code=result["code"], message=result["message"], data=result["data"])
	if result.code == "succeed" : # Success
	    computing_nodes = []
	    #node_name_list =[]
	    result = result.data.get("nodeList")[:] # filter success code
	    if result != "":
		instance_id = 0 
		for node in result:#node = [compute name,cluster id , ipmi state]
	    	    name  = node["node_name"]  # split computing nodes
		    #node_anme_list.append(name)
	    	    #instance_id = 0
		    #for name in result:
		    full_instance_information = server.list_instance(self.kwargs["cluster_id"])
		    full_instance_information = Response(code=full_instance_information["code"], message=full_instance_information["message"], data=full_instance_information["data"])
		    instance_number  = self.get_instance_number(name, full_instance_information)
	            computing_nodes.append(ComputingNode(instance_id, name, instance_number))
		    instance_id = instance_id + 1
	        return computing_nodes
	    else:
	        return []
	else:
	    return []
    def get_instance_number(self, node_name, data):
	#result, instance_list = data.split(";")	
	instance_list = data.data.get("instanceList")
	#instance_list =[instance id ,instance name,host name,ipmi state]
	result = data.code
	instance_number = 0
	if result == 'succeed' and instance_list != "":
	    #instances = instance_list.split(",")
	    for instance in instance_list:
	         if node_name == instance["host"]:
		    instance_number = instance_number + 1 
	return instance_number

class CreateView(workflows.WorkflowView):
    workflow_class = ha_cluster_workflows.CreateHAClusterWorkflow
    template_name = "haAdmin/ha_clusters/create.html"
    page_title = _("Create HA Cluster")

class AddView(workflows.WorkflowView):
    workflow_class = ha_cluster_workflows.AddComputingNodeWorkflow
    template_name = "haAdmin/ha_clusters/add_node.html"
    page_title = _("Add Computing Node")

