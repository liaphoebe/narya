import json
import os
from typing import List, Dict
from utils import count_tokens_with_tiktoken, xml_to_dict
from models.request import Request

TPLS = {

# Ping!
'ping': '''
Ping!
''',

# Function summary generator
'function_summary_generator': '''
let functions = {functions};

For each function in functions, please write a brief description of its inputs, outputs, and transformation logic. In essence, per function seek to answer the question
"What is the purpose of this code?"

Your output should be well-formed JSON in this format:
[
{{
class_name: ...,
function_name: ...,
summary: ...
}},
...
]
''',

# Json to XML
'json_to_xml': '''
let json_object = {{ 'content': {json_object} }};

What would json_object look like if it were XML of this format?:
<root>
# json_object here
</root>
''',

# Debugger
'debugger': '''
{tracecback}

Fill in the blanks of this JSON, regarding the failing line: 
{{
"line": ... # hint: write the failing line of code,
"filename": ... # hint: write the file where the failing line is,
"vars": [ ..., ... ] # hint: what variables are invoked on this line?,
"funcs": [ ..., ...] # hint: what function outputs are used on this line?,
"ops": [ ..., ...] # hint: what operations are performed on this line?,
"irrelevant_values": {prevs} # DO NOT MODIFY,
"most_relevant_value": ... # hint: what variable, function output, or operation is most relevant to the failure? ,
"debug_mode": [ '# [DEBUG_MODE]', ..., ..., <failing_line>] # hint: Instead of the line as it is, how would it look to rewrite the line in multiple lines, 
                                                  including a print statement that would show us the most_relevant_value before the error is thrown?
}}
''',

# Old Debugger
'old_debugger': '''
{code_report}
let stacktrace = {stacktrace};
let variables_debugged = {variables_debugged};

Time to put your sleuthing hat on! Based on the provided stacktrace, corresponding code report, and the debugging actions already taken,
seek to understand and address the ROOT CAUSE of the runtime error described by the provided stacktrace by filling in the blanks of this well-formed JSON:

{{
# interpretation of all relevant code:
"primary_effect":  # hint: here you should answer the question "Over the course of execution, what is this code seeking to accomplish?"
"side_effects":    # hint: here you should answer the question "Over the course of execution, what effects does this code have that aren't necessarily related to the primary effect?"
"interpretation":  # hint: here you should answer the question "Start to finish, what is this code trying to do?",

# preliminary, potentially ambiguous explanation of code failure
"explanation":     # hint: here you should answer the question "What does the runtime error say about how the code is failing in what it is attempting?",

# investigation_direction
"investigation":   # hint: here you should fill in the blank in "In order to address any ambiguity in my initial explanation and ignorance in my understanding, I should _",

"debug_variables": # hint: here you should build a list of variables you wish to debug, that have not already been debugged as described by variables_debugged, by
                #   filling out this list:
[
{{
    "variable_to_debug": # hint: what variable would you like to see the value of?
    "filename":          # path/to/file.py
    "line_number":       # hint: what is the line number above which you wish to place the debug line?
    "code_to_debug":     # hint: what is the line of code itself above which you wish to place the debug line?
}},
{{
    "variable_to_debug": ...,
    "filename": ...,
    "line_number": ...,
    "code_to_debug": ...
}},
...
],

# call_to_action
"end": # hint: Just a very brief sentence concluding your response.

}}
''',

# Debugging Evaluation
'debug_eval': '''
{code_report}
let stdout = {stdout};
let stderr = {stderr};
let error_report = {error_report};

You are about to adopt the persona of an expert code analyst. His name is Kenneth.

Kenneth, you are working with GPT-3.5-turbo. You know as well as I do that it sucks, so you must be clever. Based on the provided stderr, stdout, corresponding code report, and finally error report, it is up
to you to decide whether or not we need to do further debugging. In order to do this, simply fill in this well-formed JSON:
{{
"stdout_analysis":     # The stdout you are seeing contains data about variables we are tracking. How does this data clarify your understanding of the error described by stderr and the error report? Or, does it not?
"discussion   ":       # Based on your analysis, how confident are you we do not need to perform further debugging?
                    # In the next field you will quantify your certainty on a scale [0.0,1.0], so briefly describe any ambiguity you are still facing.
"possible_solution":   # Based on your analysis and discussion, briefly describe any possible solution you can come up with.
"solution_confidence": # On a scale [0.0, 1.0], quantify your possible solution based on your analysis and discussion. 0.0 implies total uncertainty, 1.0 implies total certainty.
"decision":            # Based on your analysis, discussion, and overall confidence, decide whether we must do further debugging. Write either "debug_further" or "solution_apparent".
}}
'''
}

class Interactor:

    def __init__(self, model='gpt-3.5-turbo', temperature=1):
        self.templates = TPLS
        self.model = model
        self.temp = temperature

    def gpt(self, template_name, data: dict, **opts):

        payload = {
            "model": self.model,
            "messages": [{
                "role": "system",
                "content": self.templates[template_name].format(**data)
            }],
            "temperature": self.temp
        }

        resume = opts.get('resume_override', True)

        ###
        # Example Response
        #
        # {'choices': [
        #    {
        #      'finish_reason': 'stop',
        #      'index': 0,
        #      'message': {
        #          'content': 'Hello! How can I assist you today?',
        #          'role': 'assistant'
        #      }
        #    }
        # ],
        # 'created': 1701009913,
        # 'id': 'chatcmpl-8PAfhzlzHebDEU2wbkwqeOQrkc1Fg',
        # 'model': 'gpt-3.5-turbo-0613',
        # 'object': 'chat.completion',
        # 'usage': {'completion_tokens': 9, 'prompt_tokens': 10, 'total_tokens': 19}}
        ###
        out = Request(template_name, payload, resume=resume).response["choices"][0]["message"]["content"]

        if opts.get('skip_format_step'):
            return out

        ###
        # Example Response
        #
        # {'root': {'content': 'Pong! How can I help you today?'}}
        ###
        out = xml_to_dict(self.gpt('json_to_xml', { 'json_object': out }, skip_format_step=True, resume_override=resume))

        return out['root']['content']

    @classmethod
    def ping(cls):
        actor = cls()
        return actor.gpt('ping', {}, resume_override=False)

    def summarize_functions(self, regenerate: bool = False) -> Dict:
        from main import app_instance

        tpl = 'function_summary_generator'

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
    
            if (code_tokens + batch_tokens) > 2500:
                summaries_results.update(self.gpt(tpl, { 'functions': batch }))
                batch = [code]
                batch_tokens = code_tokens
            else:
                batch.append(code)
                batch_tokens += code_tokens

        summaries_results.update(self.gpt(tpl, { 'functions': batch }))
        
        return summaries_results

class Debugger(Interactor):

    def __init__(self, traceback):
        super().__init__()
        self.traceback = traceback
        self.cache = { 'debug_prevs': [] }

    def run(self):
        report = self.gpt( 'debugger', { 'traceback': self.traceback, 'prevs': self.cache['debug_prevs'] }, resume_override=False )

        self.cache['debug_prevs'].append(report['most_relevant_value'])

        return report
