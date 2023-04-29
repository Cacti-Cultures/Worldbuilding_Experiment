import os
import openai
import sys
import time
import threading
import signal
from dotenv import load_dotenv
from random import seed, choice
from uuid import uuid4

# Set up global variable for spinner object
spinner_obj = None

# Define a signal handler for clean termination of the script
def signal_handler(sig, frame):
    # Access the global spinner object
    global spinner_obj

    # Terminate spinner if it's running
    if spinner_obj is not None:
        spinner_obj.terminate()

    # Clear the spinner from the console
    sys.stdout.write('\r')
    sys.stdout.flush()

    print('Exiting...')
    sys.exit(0)

# Load the environment variables from the .env file
load_dotenv(verbose=True)

# Retrieve the environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")
temperature = float(os.getenv("TEMPERATURE", "0.7"))
model = os.getenv("MODEL")

# Use the environment variables
openai.api_key = openai_api_key

# Initialize the random number generator
seed()

# Define utility functions for file operations

def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as infile:
        return infile.read()

def save_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as outfile:
        outfile.write(content)

def read_list(dir_path, filename):
    filepath = os.path.join(dir_path, filename)
    content = open_file(filepath)
    return content.strip().split('\n')

# Define spinner class for displaying loading status

class Spinner:
    def __init__(self):
        self._running = True

    def terminate(self):
        self._running = False

    def spinner(self):
        while self._running:
            for state in ['\\', '|', '/', '-']:
                sys.stdout.write('\rLoading ' + state)
                sys.stdout.flush()
                time.sleep(0.1)

# Define function for OpenAI GPT-3 chat completion

def chatgpt_completion(messages, temp=0.7, model="gpt-3.5-turbo"):
    global spinner_obj
    spinner_obj = Spinner()
    spinner_thread = threading.Thread(target=spinner_obj.spinner)
    spinner_thread.start()
    max_retry = 7
    retry = 0
    while True:
        try:
            response = openai.ChatCompletion.create(model=model, messages=messages, temperature=temp)
            text = response['choices'][0]['message']['content']
            spinner_obj.terminate()
            spinner_thread.join()
            sys.stdout.write('\r')
            sys.stdout.flush()
            return text
        except Exception as oops:
            retry += 1
            if retry >= max_retry:
                print(f"\rExiting due to an error in ChatGPT: {oops}")
                exit(1)
            print(f'\rError communicating with OpenAI: "{oops}" - Retrying in {2 ** (retry - 1) * 5} seconds...')
            sleep(2 ** (retry - 1) * 5)

# Define function for generating a scenario

def generate_scenario(elements_folder):
    # Define a list of elements
    elements = ['Fantasy_Race_Nouns', 'Physical_Attributes', 'Fantasy_Society_Types', 
                'Positive_Attributes', 'Negative_Attributes', 'Cultural_Traits', 
                'Historical_Events', 'Geographical_Features', 'Religious_Beliefs', 
                'Economic_Systems', 'Dietary_Habits', 'Technological_Level', 
                'Relationship_with_Nature', 'Conflict_Resolution', 'Common_Occupations', 
                'Symbolisms', 'Architecture', 'Language', 'Clothing_Fashion', 
                'Laws_and_Justice_System']

        # Read lists from files and randomly choose an element from each list
    attributes = {element.lower(): choice(read_list(elements_folder, element + '.txt')) for element in elements}

        # Format the scenario as a string
    scenario = "\n".join(f"{key.capitalize()}: {value}" for key, value in attributes.items())
        
    return scenario, attributes

# Main script execution

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    elements_folder = 'elements'
    list_system = read_list(elements_folder, 'list_system.txt')

    try:
        for i in range(2000):
            default_system = choice(list_system)
            scenario_id = str(uuid4())
            scenario, scenario_attributes = generate_scenario(elements_folder)
            messages = [
                {"role": "system", "content": default_system},
                {"role": "user", "content": scenario},
            ]
            response = chatgpt_completion(messages, temp=temperature, model=model)
            print('\n\n---\n\n', scenario, '\n---', '\n\nResponse:\n', response)
            filepath = './scenarios/scenario_%s.md' % scenario_id
            save_file(filepath, response)

            # Save metadata
            filepath = filepath.replace('scenarios','scenario_metadata').replace('.md','.md')
            scenario_metadata = "\n".join(f"{key.capitalize()}: {value}" for key, value in scenario_attributes.items())
            save_file(filepath, scenario_metadata)
        exit()
    except KeyboardInterrupt:
        print("\nScript execution was interrupted by user. Exiting...")
        exit()