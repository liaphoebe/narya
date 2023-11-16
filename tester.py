import subprocess
import re
from interactor import Interactor
from conf import TEST_CMD
from main import app_instance

class Tester:
    def perform(self):
        # Execute the TEST_CMD from conf.py
        result = subprocess.run(TEST_CMD.split(), capture_output=True, text=True)

        if result.stderr != '':
            whitelist = self.parse_stacktrace(result.stderr)
            code_report = app_instance.viewer.fs_dump(whitelist=whitelist)
            print(Interactor().address_error(code_report, result.stderr))

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
