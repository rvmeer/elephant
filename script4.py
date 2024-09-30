from openai import AzureOpenAI
import os
import time
import json
import random
    
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),  
    api_version="2024-07-01-preview",
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    )

assistant = client.beta.assistants.create(
  name="Weather Bot",
  instructions="You are machine that loads and unloads wafers from a machine. The machine has 2 chucks. You can also calculate the average of a list of offsets.",
  model="gpt-4o2", #Replace with model deployment name
  tools=[
     {
      "type": "function",
      "function": {
        "name": "load_wafer",
        "description": "Load a wafer into the machine",
        "parameters": {
          "type": "object",
          "properties": {
            "chuck_id": {
              "type": "string",
              "description": "The id of the chuck, can be CHUCK_1 or CHUCK_2"
            }
          },
          "required": [
            "chuck_id"
          ]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "wafer_present_on_chuck",
        "description": "Check if a wafer is present on the chuck",
        "parameters": {
          "type": "object",
          "properties": {
            "chuck_id": {"type": "string", "description": "The id of the chuck, can be CHUCK_1 or CHUCK_2"}
          },
          "required": ["chuck_id"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "unload_wafer",
        "description": "Unload a wafer from the machine",
        "parameters": {
          "type": "object",
          "properties": {
            "chuck_id": {"type": "string", "description": "The id of the chuck, can be CHUCK_1 or CHUCK_2"}
          },
          "required": ["chuck_id"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "calculate",
        "description": "Calculate the average of a list of offsets",
        "parameters"
        : {
          "type": "object",
          "properties": {
            "offsets": {"type": "array", "items": {
               "type": "object",
               "properties": {
                  "x": {"type": "number"}, "y": {"type": "number"}}
            }}
          },
          "required": ["offsets"]
        }
       
      }
    }
  ]
)

# Create a thread
thread = client.beta.threads.create()
print(thread)

# Add a user question to the thread
message = client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content="""
I want you to perform the following steps: 

1. Make sure no wafers are present in the machine
2. Now, perform this 3 times:
   - Load a wafer onto chuck 1
   - Keep the returned offset is a list of offsets
3. Send the list of offsets to the calculation function
4. Give me the result of the calculation function
5. Make sure no wafers are left in the machine
"""
)

# Run the thread
run = client.beta.threads.runs.create(
  thread_id=thread.id,
  assistant_id=assistant.id,
  #instructions="New instructions" #You can optionally provide new instructions but these will override the default instructions
)

run = client.beta.threads.runs.retrieve(
  thread_id=thread.id,
  run_id=run.id
)

# wait until status is: requires_action
status = run.status
while status != "requires_action":
    time.sleep(5)
    run = client.beta.threads.runs.retrieve(thread_id=thread.id,run_id=run.id)
    status = run.status


##############

# Function definitions
def load_wafer(chuck_id):
    print(f"Loading wafer onto chuck {chuck_id}")

    x = random.uniform(0, 1.0)
    y = random.uniform(0, 1.0)
    
    return {"x": x, "y": y}
def wafer_present_on_chuck(chuck_id):
    print(f"Checking if wafer is present on chuck {chuck_id}")

    return chuck_id =='CHUCK_1'

def unload_wafer(chuck_id):
    print(f"Unloading wafer from chuck {chuck_id}")
    return True

def calculate(offsets):
    print(f"Calculating average of offsets (length: {len(offsets)})")

    offset_tuples = [(offset['x'], offset['y']) for offset in offsets]

    average_x = sum([x for x, _ in offset_tuples]) / len(offsets)
    average_y = sum([y for _, y in offset_tuples]) / len(offsets)
    
    return {"average_x": average_x, "average_y": average_y}

while run.status == "requires_action":

  # Define the list to store tool outputs
  tool_outputs = []
  
  # Loop through each tool in the required action section
  for tool in run.required_action.submit_tool_outputs.tool_calls:
    # get data from the weather function
    if tool.function.name == "load_wafer":
      arguments = json.loads(tool.function.arguments)
      result = load_wafer(**arguments)
      tool_outputs.append({
        "tool_call_id": tool.id,
        "output": str(result)
      })
    elif tool.function.name == "wafer_present_on_chuck":
      arguments = json.loads(tool.function.arguments)
      result = wafer_present_on_chuck(**arguments)
      tool_outputs.append({
        "tool_call_id": tool.id,
        "output": str(result)
      })
    elif tool.function.name == "unload_wafer":
      arguments = json.loads(tool.function.arguments)
      result = unload_wafer(**arguments)
      tool_outputs.append({
        "tool_call_id": tool.id,
        "output": str(result)
      })
    elif tool.function.name == "calculate":
      arguments = json.loads(tool.function.arguments)
      result = calculate(**arguments)
      tool_outputs.append({
        "tool_call_id": tool.id,
        "output": str(result)
      })
  
  # Submit all tool outputs at once after collecting them in a list
  if tool_outputs:
    try:
      run = client.beta.threads.runs.submit_tool_outputs_and_poll(
        thread_id=thread.id,
        run_id=run.id,
        tool_outputs=tool_outputs
      )
    except Exception as e:
      print("Failed to submit tool outputs:", e)
  else:
    print("No tool outputs to submit.")





if run.status == 'completed':
  print("run status: ", run.status)
  messages = client.beta.threads.messages.list(thread_id=thread.id)
  print(messages.to_json(indent=2))
else:
  print("run status: ", run.status)
  print (run.last_error.message)


##########
# Retrieve the status of the run
run = client.beta.threads.runs.retrieve(
  thread_id=thread.id,
  run_id=run.id
)

status = run.status
print(f'Status: {status}')
while status not in ["completed", "cancelled", "expired", "failed"]:
    time.sleep(5)
    run = client.beta.threads.runs.retrieve(thread_id=thread.id,run_id=run.id)
    status = run.status
    print(f'Status: {status}')

print(messages.data[0].content[0].text.value)