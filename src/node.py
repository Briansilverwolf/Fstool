from typing import List, Optional

class Node:
    def __init__(self, name: str, is_directory: bool = False, content: Optional[str] = None):
        self.name: str = name
        self.is_directory: bool = is_directory
        self.children: List['Node'] = []
        self.content: Optional[str] = content  # Store file content here

    def add_child(self, child: 'Node') -> None:
        self.children.append(child)

    def __repr__(self) -> str:
        return (
            f"Node(name='{self.name}', "
            f"is_directory={self.is_directory}, "
            f"children={len(self.children)}, "
            f"has_content={self.content is not None})"
        )