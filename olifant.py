from openai import AzureOpenAI
import os
import time
import json
import random

# Create the API client
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),  
    api_version="2024-07-01-preview",
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    )

# Create an assistant
assistant = client.beta.assistants.create(
  name="Olifant",
  instructions="You are machine that puts animals in a fridge. Only one animal can stay in the fridge at the same time. Close the fridge when a new animal is put in it.",
  model="gpt-4o2", #Replace with model deployment name
  tools=[
     {
      "type": "function",
      "function": {
        "name": "open_fridge",
        "description": "Opens the fridge so an animal can be put inside"
      }
    },
    {
      "type": "function",
      "function": {
        "name": "animal_present_in_fridge",
        "description": "Check if an animal is present in the fridge, works only if the fridge is open."
      }
    },
    {
      "type": "function",
      "function": {
        "name": "close_fridge",
        "description": "Closes the fridge"
      }
    },
    {
      "type": "function",
      "function": {
        "name": "put_animal_in_fridge",
        "description": "Puts a named animal in the fridge, only works if the fridge is open",
        "parameters": {
          "type": "object",
          "properties": {
            "animal_name": {"type": "string", "description": "The name of the animal"}
          },
          "required": ["animal_name"]
        }
      },
    },
    {
        "type": "function",
        "function": {
            "name": "remove_animal_from_fridge",
            "description": "Removes the current animal from the fridge, only works if the fridge is open"
        }
    }
  ]
)

####
current_animal = None

def open_fridge():
    print("Opening the fridge")

def animal_present_in_fridge():
    print("Checking if an animal is present in the fridge")
    return current_animal is not None

def close_fridge():
    print("Closing the fridge")

def put_animal_in_fridge(animal_name):
    global current_animal
    
    print(f"Putting {animal_name} in the fridge")
    current_animal = animal_name

def remove_animal_from_fridge():
    global current_animal
    
    print(f"Removing {current_animal} from the fridge")
    current_animal = None

functions = {
    "open_fridge": open_fridge,
    "animal_present_in_fridge": animal_present_in_fridge,
    "close_fridge": close_fridge,
    "put_animal_in_fridge": put_animal_in_fridge,
    "remove_animal_from_fridge": remove_animal_from_fridge
}
####



# Create a thread
thread = client.beta.threads.create()

instructions1 = """
I want you to perform the following steps: 

1. Open the fridge
2. Check if an animal is present in the fridge, if so remove it
3. Put an elephant in the fridge
4. Close the fridge
5. Open the fridge
6. Check if an animal is present in the fridge, if so remove it
7. Put a giraffe in the fridge
8. Close the fridge
"""

instructions2 = """
I want you to perform the following steps:
1. Make sure the fridge is empty
2. Put an elephant in the fridge
3. Close the fridge
4. Make sure the fridge is empty
5. Put a giraffe in the fridge
6. Close the fridge
"""

instructions3="""
I want you to perform the following steps:
1. First put an elephant in the fridge
2. Then put a giraffe in the fridge

Always make sure the fridge is empty before putting an animal in it.
"""

# Add a user message to the thread
message = client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content=instructions1
)

# Run the thread
run = client.beta.threads.runs.create(
  thread_id=thread.id,
  assistant_id=assistant.id
)

# Update the run information
run = client.beta.threads.runs.retrieve(
  thread_id=thread.id,
  run_id=run.id
)

# Wait until the run status is: requires_action
status = run.status
while status != "requires_action":
    time.sleep(5)
    run = client.beta.threads.runs.retrieve(thread_id=thread.id,run_id=run.id)
    status = run.status

############

while run.status == "requires_action":

    # Define the list to store tool outputs
    tool_outputs = []
  
    # Loop through each tool in the required action section
    for tool in run.required_action.submit_tool_outputs.tool_calls:
        arguments = json.loads(tool.function.arguments)
        f = functions.get(tool.function.name, None)
        if f:
            result = f(**arguments)
            tool_outputs.append({
                "tool_call_id": tool.id,
                "output": str(result)
            })
        else:
            print(f"Unknown function: {tool.function.name}")

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

########

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


