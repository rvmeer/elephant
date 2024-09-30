import os
import json
from openai import AzureOpenAI
import time
    
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),  
    api_version="2024-05-01-preview",
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    )

# Create an assistant
assistant = client.beta.assistants.create(
    name="Data Visualization",
    instructions=f"You are a helpful AI assistant who makes interesting visualizations based on data." 
    f"You have access to a sandboxed environment for writing and testing code."
    f"When you are asked to create a visualization you should follow these steps:"
    f"1. Write the code."
    f"2. Anytime you write new code display a preview of the code to show your work."
    f"3. Run the code to confirm that it runs."
    f"4. If the code is successful display the visualization."
    f"5. If the code is unsuccessful display the error message and try to revise the code and rerun going through the steps from above again.",
    tools=[{"type": "code_interpreter"}],
    model="gpt-4o2" #You must replace this value with the deployment name for your model.
)

print(assistant.model_dump_json(indent=2))

# Create a thread
thread = client.beta.threads.create()
print(thread)

# Add a user question to the thread
message = client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content="Create a visualization of a sinewave"
)

# Run the thread
run = client.beta.threads.runs.create(
  thread_id=thread.id,
  assistant_id=assistant.id,
  #instructions="New instructions" #You can optionally provide new instructions but these will override the default instructions
)

# Retrieve the status of the run
run = client.beta.threads.runs.retrieve(
  thread_id=thread.id,
  run_id=run.id
)

status = run.status
print(status)

status = run.status

while status not in ["completed", "cancelled", "expired", "failed"]:
    time.sleep(5)
    run = client.beta.threads.runs.retrieve(thread_id=thread.id,run_id=run.id)
    status = run.status
    print(f'Status: {status}')

messages = client.beta.threads.messages.list(
  thread_id=thread.id
) 

print(f'Status: {status}')
print(messages.model_dump_json(indent=2))

data = json.loads(messages.model_dump_json(indent=2))
image_file_id = data['data'][0]['content'][0]['image_file']['file_id']
print(image_file_id)  # Outputs: assistant-1YGVTvNzc2JXajI5JU9F0HMD

content = client.files.content(image_file_id)
image= content.write_to_file("sinewave.png")

# Dark mode

# Add a user question to the thread
message = client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content="I prefer visualizations in darkmode can you change the colors to make a darkmode version of this visualization."
)

# Run the thread
run = client.beta.threads.runs.create(
  thread_id=thread.id,
  assistant_id=assistant.id,
)

# Retrieve the status of the run
run = client.beta.threads.runs.retrieve(
  thread_id=thread.id,
  run_id=run.id
)

status = run.status
print(status)
while status not in ["completed", "cancelled", "expired", "failed"]:
    time.sleep(5)
    run = client.beta.threads.runs.retrieve(thread_id=thread.id,run_id=run.id)
    status = run.status
    print(f'Status: {status}')

messages = client.beta.threads.messages.list(
  thread_id=thread.id
)
print(messages.model_dump_json(indent=2))


data = json.loads(messages.model_dump_json(indent=2))
file_ids = [content['image_file']['file_id'] for message in data['data'] for content in message['content'] if 'image_file' in content]


# Get the 2nd image and write to sinewave_dark
content = client.files.content(file_ids[0])
image= content.write_to_file("sinewave_dark.png")

            