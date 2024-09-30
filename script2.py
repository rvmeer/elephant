from openai import AzureOpenAI
import os
import time
import json
    
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),  
    api_version="2024-07-01-preview",
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    )

assistant = client.beta.assistants.create(
  name="Weather Bot",
  instructions="You are a weather bot. Use the provided functions to answer questions.",
  model="gpt-4o2", #Replace with model deployment name
  tools=[{
      "type": "function",
    "function": {
      "name": "get_weather",
      "description": "Get the weather in location",
      "parameters": {
        "type": "object",
        "properties": {
          "location": {"type": "string", "description": "The city name, for example San Francisco"}
        },
        "required": ["location"]
      }
    }
  }]
)

# Create a thread
thread = client.beta.threads.create()
print(thread)

# Add a user question to the thread
message = client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content="What is the weather in Eindhoven"
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

# Example function
def get_weather():
    return "It's 80 degrees F and slightly cloudy."

# Define the list to store tool outputs
tool_outputs = []
 
# Loop through each tool in the required action section
for tool in run.required_action.submit_tool_outputs.tool_calls:
  # get data from the weather function
  if tool.function.name == "get_weather":
    arguments = json.loads(tool.function.arguments)
    location = arguments["location"]
    weather = get_weather(location)
    tool_outputs.append({
      "tool_call_id": tool.id,
      "output": weather
    })
 
# Submit all tool outputs at once after collecting them in a list
if tool_outputs:
  try:
    run = client.beta.threads.runs.submit_tool_outputs_and_poll(
      thread_id=thread.id,
      run_id=run.id,
      tool_outputs=tool_outputs
    )
    print("Tool outputs submitted successfully.")
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



