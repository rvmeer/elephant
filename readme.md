# Azure Open AI Function Caller Helper.

How to put an elephant in the fridge?

## Introduction

This Python library allows you to easily specify functions that can be called from the function calling tool of the Azure Open AI Assistant.

1. Define your local function
2. Decorate then with a clear description of what the function does
3. The helper will pass the applicable tools to the assistant and helps in executing the assistant thread.

## Install

Put the afch folder in your Python project. Now you can import the AssistantFunctionCallingHelper from afch and
use the decorator.

Current afch is not available as pip package.

## Getting started

1. Install Python 3.12
2. `pip install openai`

Create an instance of the AssistantFunctionCallingHelper

```
from afch import AssistantFunctionCallingHelper

afc = AssistantFunctionCallingHelper()
```

And use the decorator to define your functions. A function name and description is enough. The
AssistantFunctionCallingHelper will make sure the Assistant will get all information needed to call
the function if applicable.
```
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
```

Now use the Open AI Assistant API to define an Assistant and create a thread with a message. Make sure
you store your Open AI API key in the `AZURE_OPENAI_API_KEY` environment variable, as well as your AZURE_OPENAI_ENDPOINT.

When defining the Assistant, use the `tools` provided by the AssistantFunctionCallingHelper.

```
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
    model="gpt-4o",
    tools=afc.tools
)

# Create a thread with a message
thread = client.beta.threads.create()
client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content=instructions
)
```

Now run the assistent with your instructions, your defined functions will be called locally!


```
instructions="""
I want you to perform the following steps:
1. First put an elephant in the fridge
2. Then put a giraffe in the fridge

Always make sure the fridge is empty before putting an animal in it.
"""

# Run the thread on the assistant
run = afc.create_thread_run(client, thread, assistant)
run.execute()
```

The result will be:

```
Opening the fridge
Checking if an animal is present in the fridge
Putting elephant in the fridge
Closing the fridge
Opening the fridge
Removing elephant from the fridge
Putting giraffe in the fridge
Closing the fridge
```




