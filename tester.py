import subprocess
import re
import os
from interactor import Interactor, Debugger, CodingPair, Storyteller
from conf import TEST_CMD
from main import app_instance
from composer import Composer
from branch_manager import BranchManager
from utils import drilldown

class Tester:

    def __init__(self):
        self.stderr = None
        self.stdout = None
        self.code_report = None
        self.error_report = None
        self.debug_actions = []

        self.mgr = BranchManager()

    # 1. Run test; 2. Generate debug report; 3. Modify code based on report; 4. Goto #1
    def perform(self, used_values=[]):

        def p():
            print('.', end='')

        p()
        result = subprocess.run(TEST_CMD.split(), capture_output=True, text=True)
        p()

        breakpoint()

        if result.stderr != '':
            debugger = Debugger(result.stderr)
            report = debugger.run()
            p()

            breakpoint()

            used_values.append(report['most_relevant_value'])

            self.mgr.edit_file(report['filename'], report['line'], drilldown(report, 'python_code') )
            p()

            breakpoint()

            rerun = subprocess.run(TEST_CMD.split(), capture_output=True, text=True)
            p()

            storyteller = Storyteller( app_instance.viewer.fs_dump( whitelist= self.parse_stacktrace(result.stderr) ), result.stdout, result.stderr )
            storyteller.run()
            p()

            breakpoint()

            for revision in meeting['endgame']['changes']:
                self.mgr.edit_file(revision['filename'], revision['original_code'], revision['changed_code'])
            p()

            breakpoint()

            self.perform(used_values= used_values)

        print('I guess we are here now...')


    def old_perform(self):
        # Execute the TEST_CMD from conf.py
        print('...') 

        result = subprocess.run(TEST_CMD.split(), capture_output=True, text=True)

        print('Run 1 Complete.')

        breakpoint()

        if result.stderr != '':
            self.stderr = result.stderr
            self.debug_loop()


    def debug_loop(self):
        actor = Interactor()
   
        if self.code_report is None: 
            whitelist = self.parse_stacktrace(self.stderr)
            self.code_report = app_instance.viewer.fs_dump(whitelist=whitelist)
       
        # Stage 1: Declare new debugging actions
        self.error_report = actor.gpt('debugger', {
            'code_report':        self.code_report,
            'stacktrace':         self.stderr,
            'variables_debugged': '\n'.join([ str(x) for x in self.debug_actions ])
        })

        breakpoint()

        print('Error report generated.')
   
        print(self.stderr)
        debug_dict = self.error_report['debug_variables']
        print(debug_dict)
        #   This will populate self.debug_actions
        self.insert_print_statements(debug_dict)
    
        print('Debug statements added.')

        # Stage 2: Collect new data
        debug_run = subprocess.run(TEST_CMD.split(), capture_output=True, text=True)

        print('Run 2 complete.')

        print(debug_run.stdout)

        breakpoint()

        evaluation = actor.gpt('debug_eval', {
            'code_report':  self.code_report,
            'error_report': self.error_report,
            'stdout':       debug_run.stdout,
            'stderr':       self.stderr
        })
   
        print('Debug evaluation complete.')
 
        print(evaluation)

        breakpoint()
        if evaluation['decision'] == 'more_data':
            self.debug_loop()


    def parse_stacktrace(self, stacktrace):
        output = {}
    
        # regex to match file, function and line
        pattern = r'File "(.*?)", line \d+, in (.*?)\n'
        matches = re.findall(pattern, stacktrace)
    
        for match in matches:
            filename, function_name = match
    
            # if file already in output, add the function to existing list
            if filename in output:
                output[filename].append(function_name)
            # if file not in output, add the file and start a new list with the function
            else:
                output[filename] = [function_name]
        
        return output

    def insert_print_statements(self, debug_actions):
        # [ { 'variable_to_debug', 'filename', 'line_number', 'code_to_debug' } ]
        composers = {}
        for action in debug_actions:
            filename = action['filename']

            if not composers.get(filename):
                composers[filename] = Composer(action['filename'])

            variable = action['variable_to_debug']
            composers[filename].insert_code_above( [ f"print(f'[DEBUG] {variable}: " + '{' + variable + "}')" ], action['code_to_debug'] )

        for composer in composers.values():
            composer.recompose()
        
