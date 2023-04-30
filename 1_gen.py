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

# Define function for generation

def generation_elements(elements_folder):
    # Get all text files in the elements_folder
    elements_files = [f for f in os.listdir(elements_folder) if f.endswith('.txt')]
    
    # Read lists from files and randomly choose an element from each list
    attributes = {os.path.splitext(element_file)[0].lower(): choice(read_list(elements_folder, element_file)) for element_file in elements_files}

    # Format the generation as a string
    generation = "\n".join(f"{key.capitalize()}: {value}" for key, value in attributes.items())
        
    return generation, attributes


# Main script execution

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    elements_folder = 'elements'
    list_system = read_list(elements_folder, 'System.txt')

    try:
        for i in range(2000):
            default_system = choice(list_system)
            generation_id = str(uuid4())
            generation, generation_attributes = generation_elements(elements_folder)
            messages = [
                {"role": "system", "content": default_system},
                {"role": "user", "content": generation},
            ]
            response = chatgpt_completion(messages, temp=temperature, model=model)
            print('\n\n---\n\n', generation, '\n---', '\n\nResponse:\n', response)
            filepath = './1_gen/generation_%s.md' % generation_id
            save_file(filepath, response)

            # Save metadata
            filepath = filepath.replace('1_gen','1_gen_metadata').replace('.md','.md')
            generation_metadata = "\n".join(f"{key.capitalize()}: {value}" for key, value in generation_attributes.items())
            save_file(filepath, generation_metadata)
        exit()
    except KeyboardInterrupt:
        print("\nScript execution was interrupted by user. Exiting...")
        exit()