import time
import re
import subprocess
import socket


class TreeNode:

    def __init__(self, data):
        self.left = None
        self.right = None
        self.data = data

    def insert(self, data):
# Compare the new value with the parent node
        if self.data:
            if data < self.data:
                if self.left is None:
                    self.left = TreeNode(data)
                else:
                    self.left.insert(data)
            elif data > self.data:
                if self.right is None:
                    self.right = TreeNode(data)
                else:
                    self.right.insert(data)
        else:
            self.data = data

# Print the tree
    def PrintTree(self):
        if self.left:
            self.left.PrintTree()
        print (str(self.data))
        if self.right:
            self.right.PrintTree()

    def get_data(self):
        return self.data

    def get_left_node(self):
        return self.left

    def get_right_node(self):
        return self.right

    def get_node_by_data(self, data):
        if self.data == data:
            return self
        elif self.data < data:
            if self.right != None:
                return self.right.get_node_by_data(data)
            else:
                return "not found"
        elif self.data > data:
            if self.left != None:
                return self.left.get_node_by_data(data)
            else:
                return "not found!"


