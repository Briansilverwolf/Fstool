from typing import List

class Node:
    def __init__(self, name: str, is_directory: bool = False):
        self.name = name
        self.is_directory = is_directory
        self.children: List['Node'] = []

    def add_child(self, child: 'Node'):
        self.children.append(child)


