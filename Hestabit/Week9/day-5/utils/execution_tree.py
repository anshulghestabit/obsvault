class ExecutionTree:

    def __init__(self):

        self.tree = {
            "planner": None,
            "workers": [],
            "reflection": None,
            "validator": None
        }

    def add_plan(self, steps):
        self.tree["planner"] = steps

    def add_worker_result(self, step, result):
        self.tree["workers"].append({
            "step": step,
            "result": result
        })

    def add_reflection(self, reflection):
        self.tree["reflection"] = reflection

    def add_validation(self, validation):
        self.tree["validator"] = validation

    def display(self):

        print("\nEXECUTION TREE\n")

        print("PLANNER:")
        for step in self.tree["planner"]:
            print(f"  ├─ {step}")

        print("\nWORKERS:")

        for w in self.tree["workers"]:
            print(f"  ├─ STEP: {w['step']}")
            print(f"      RESULT: {w['result'][:120]}...\n")

        print("REFLECTION:")
        print(self.tree["reflection"][:200], "\n")

        print("VALIDATION:")
        print(self.tree["validator"][:200])

        print("\n")