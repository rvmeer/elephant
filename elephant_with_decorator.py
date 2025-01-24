from openai import AzureOpenAI
import os
from afch import AssistantFunctionCallingHelper

afc = AssistantFunctionCallingHelper()

####
current_animal = None

@afc.function(name='open_fridge', description='Opens the fridge so an animal can be put inside')
def open_fridge():
    print("Opening the fridge")

@afc.function(name='animal_present_in_fridge', description='Check if an animal is present in the fridge, works only if the fridge is open.')
def animal_present_in_fridge():
    print("Checking if an animal is present in the fridge")
    return current_animal is not None

@afc.function(name='close_fridge', description='Closes the fridge')
def close_fridge():
    print("Closing the fridge")

@afc.function(name='put_animal_in_fridge', description='Puts a named animal in the fridge, only works if the fridge is open', 
                    animal_name={"type": "string", "description": "The name of the animal", "required": True})
def put_animal_in_fridge(animal_name):
    global current_animal
    
    print(f"Putting {animal_name} in the fridge")
    current_animal = animal_name

@afc.function(name='remove_animal_from_fridge', description='Removes the current animal from the fridge, only works if the fridge is open')
def remove_animal_from_fridge():
    global current_animal
    
    print(f"Removing {current_animal} from the fridge")
    current_animal = None

####



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
    model="gpt-4o2",
    tools=afc.tools
)

# Create a thread with a message
thread = client.beta.threads.create()
client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content=instructions3
)

# Run the thread on the assistant
run = afc.create_thread_run(client, thread, assistant)
run.execute()