class TaskManager:
    def __init__(self):
        self.tasks = {}

    def add_task(self, task_id, description):
        if task_id in self.tasks:
            raise Exception("Task already exists")

        task = {
            "id": task_id,
            "description": description,
            "completed": False
        }

        self.tasks[task_id] = task

    def remove_task(self, task_id):
        if task_id not in self.tasks:
            raise Exception("Task not found")

        del self.tasks[task_id]

    def mark_task_complete(self, task_id):
        if task_id not in self.tasks:
            raise Exception("Task not found")

        self.tasks[task_id]["completed"] = True

    def list_pending_tasks(self):
        pending = {}

        for task_id in self.tasks:
            task = self.tasks[task_id]

            if task["completed"] == False:
                pending[task_id] = task

        return pending