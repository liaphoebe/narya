import requests
import json
import os
from typing import List, Dict
from utils import count_tokens_with_tiktoken

REPORT_TEMPLATE = '''
You are a helpful assistant. You favor word economy and always speak as tersely as possible. Based on the provided Python code report, you will generate a summary of each function. For each function, write a brief description of its inputs, outputs, and transformation logic. Your output should be well-formed JSON in this format: {{ "class_name#function_name": "summary" }}.
'''

ERROR_DIAGNOSIS_TPL = '''
Time to put your sleuthing hat on! Based on the provided stacktrace, corresponding code report, and the results of any previous investigation rounds, 
  seek to understand and address the ROOT CAUSE of the runtime error described by the provided stacktrace by filling in the blanks of this well-formed JSON:
{
# interpretation of all relevant code:
'primary_effect': # hint: here you should answer the question "Over the course of execution, what is this code seeking to accomplish?"
'side_effects': # hint: here you should answer the question "Over the course of execution, what effects does this code have that aren't necessarily related to the primary effect?"
'overall_interpretation': # hint: here you should answer the question "Start to finish, what is this code trying to do?",

# preliminary, potentially ambiguous explanation of code failure 
'preliminary': # hint: here you should answer the question "What does the runtime error say about how the code is failing in what it is attempting?",

# investigation_direction
'investigation': # hint: here you should fill in the blank in "In order to address any ambiguity in my initial explanation and ignorance in my understanding, I should _",

# debug_action
'debug': # hint: here, you are deciding where to place the line of code "import pdb; pdb.set_trace()" by filling out this list of nested well-formed JSONs, one per file to debug: 
[
  {
    'filename': path/to/file.py,
    'location': # hint: here, you should specify the line of code AS IT IS and ABOVE WHICH you wish to place the debug line. 
    'variables': # hint: here, you should specify in an array of VARIABLE NAMES which variables you wish to see the values of at this point in code execution.
  },
  {
    'filename': path/to/another_file.py,
    'loction': ...,
    'variables': ...
  },
  ... 
],

# call_to_action
'end': Just a very brief sentence concluding your response. 

}
'''


class Interactor:

    def gpt(self, messages, model="gpt-4", temperature=1, max_tokens=None):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
        }
    
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
    
        if max_tokens is not None:
            data["max_tokens"] = max_tokens
    
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, data=json.dumps(data))
    
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            raise Exception(f"Error {response.status_code}: {response.text}")

    def load_response(self, response):
        try:
            return json.loads(response)
        except json.decoder.DecoderError:
            print(response)
            os.exit(1)

    def address_error(self, code_report, stacktrace):
        messages = [{
            "role": "system",
            "content": f"{code_report}\nlet stacktrace = {stacktrace}\n\n{ERROR_DIAGNOSIS_TPL}"
        }]
        response = self.gpt(messages, model='gpt-3.5-turbo', max_tokens=1000)
        return self.load_response(response)

    def prepare_call(self, batch):
        """Prepare OpenAI API call"""
        messages = [{
            "role": "system",
            "content": f"{REPORT_TEMPLATE}\n{''.join(batch)}"
        }]
        raw_summary = self.gpt(messages, model='gpt-3.5-turbo', max_tokens=1000)
        return json.loads(raw_summary)

    def summarize_functions(self, regenerate: bool = False) -> Dict:
        from main import app_instance

        viewer = app_instance.viewer
        mechanisms = viewer.mechanisms
        
        summaries_results = {}
        batch = []
        batch_tokens = 0

        for mechanism in mechanisms:
            if not regenerate and mechanism.summary is not None:
                continue

            code = mechanism.code

            if code is None:
                continue

            code_tokens = count_tokens_with_tiktoken(code)
    
            if (code_tokens + batch_tokens) > 3000:
                summaries_results.update(self.prepare_call(batch))
                batch = [code]
                batch_tokens = code_tokens
            else:
                batch.append(code)
                batch_tokens += code_tokens

        summaries_results.update(self.prepare_call(batch))
       
        return summaries_results
 
