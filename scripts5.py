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
  name="CPD helper",
  instructions="Describe the CPD. Answer with markdown.",
  model="gpt-4o2", #Replace with model deployment name
  tools=[{"type": "file_search"}],
  tool_resources={"file_search": {"vector_store_ids": ['vs_tNesQWFZkMa11VbjdwfuC5pq']}}
  
)

print

# Create a thread
thread = client.beta.threads.create()
print(thread)

# Add a user question to the thread
while True:
    question = input("Enter a question: ")
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=question
    )

    # Run the thread
    run = client.beta.threads.runs.create(
    thread_id=thread.id,
    assistant_id=assistant.id,
    #instructions="New instructions" #You can optionally provide new instructions but these will override the default instructions
    )

    # Wait until completed
    status = run.status
    while status != "completed":
        time.sleep(5)
        run = client.beta.threads.runs.retrieve(thread_id=thread.id,run_id=run.id)
        status = run.status

    messages = client.beta.threads.messages.list(
    thread_id=thread.id
    )
    response = messages.data[0].content[0].text.value
    print(response)
