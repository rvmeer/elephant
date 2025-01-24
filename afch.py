from openai import AzureOpenAI
import os
import time
import json

class AssistantFunctionCallingHelper:
    def __init__(self):
        self.functions = {}
        self.tools = []

    def function(self, name, description, **kwargs):
        def decorator(f):
            self.functions[name] = f
            
            required_parameters = [key for key, value in kwargs.items() if value.get("required", False)]
            parameters = {
                "type": "object",
                "properties": {
                    key: {k:v for k,v in value.items() if k != "required"} for key, value in kwargs.items()
                },
                "required": required_parameters
            }

            if len(parameters["properties"]) == 0:
                parameters = {}

            function_dict = {
                "name": name,
                "description": description
            }
            if len(parameters) > 0:
                function_dict["parameters"] = parameters

            self.tools.append({
                "type": "function",
                "function": function_dict
            })
            return f
        return decorator

    def create_client(self, api_key=os.getenv("AZURE_OPENAI_API_KEY"), api_version="2024-07-01-preview", azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")):
        return AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=azure_endpoint
        )

    def create_thread_run(self, client, thread, assistant):
        return ThreadRun(client, thread, assistant, self.functions)

class ThreadRun:
    def __init__(self, client, thread, assistant, functions):
        self.client = client
        self.thread = thread
        self.assistant = assistant
        self.functions = functions

        self.run = self.client.beta.threads.runs.create(
            thread_id=self.thread.id,
            assistant_id=self.assistant.id
        )

    def handle_requires_action(self):
        tool_outputs = []
    
        for tool in self.run.required_action.submit_tool_outputs.tool_calls:
            arguments = json.loads(tool.function.arguments)
            f = self.functions.get(tool.function.name, None)
            if f:
                result = f(**arguments)
                tool_outputs.append({
                    "tool_call_id": tool.id,
                    "output": str(result)
                })
            else:
                print(f"Unknown function: {tool.function.name}")

        if tool_outputs:
            try:
                run = self.client.beta.threads.runs.submit_tool_outputs_and_poll(
                    thread_id=self.thread.id,
                    run_id=self.run.id,
                    tool_outputs=tool_outputs
                )
            except Exception as e:
                print("Failed to submit tool outputs:", e)
        else:
            print("No tool outputs to submit.")

    def execute(self):
        while True:
            self.run = self.client.beta.threads.runs.retrieve(
                thread_id=self.thread.id,
                run_id=self.run.id
            )

            if self.run.status in ["completed", "cancelled", "expired", "failed"]:
                return self.run
            
            if self.run.status == "requires_action":
                self.handle_requires_action()
            elif self.run.status == "in_progress" or self.run.status == "queued":
                time.sleep(1)
            else:
                print(self.run.status)