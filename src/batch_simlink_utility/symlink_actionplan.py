import os

class ActionItem:
    def __init__(self, src, dst_dir):
        self.src = src
        self.dst_dir = dst_dir
        self.status = "Planned"
        self.error = None

    def __str__(self):
        return f"Move {self.src} -> {self.dst_dir} [Status: {self.status}]"

    def execute(self):
        base_name = os.path.basename(self.src)
        target = os.path.join(self.dst_dir, base_name)
        try:
            # Move original to target
            os.rename(self.src, target)
            # Create symlink at original location pointing to new
            os.symlink(target, self.src)
            self.status = "Done"
        except Exception as e:
            self.status = "Error"
            self.error = str(e)
            raise

class ActionPlan:
    def __init__(self):
        self.items = []

    def add_item(self, item: ActionItem):
        self.items.append(item)

    def clear(self):
        self.items = []

    def __str__(self):
        lines = []
        for item in self.items:
            line = str(item)
            if item.error:
                line += f" (Error: {item.error})"
            lines.append(line)
        return "\n".join(lines)