import os
import ast
from utils import create_key_from_path, get_value
from collections import defaultdict
from typing import Dict
import pyperclip

class Viewer:
    _instance = None

    def __new__(cls, path):
        if not cls._instance:
            cls._instance = super(Viewer, cls).__new__(cls)
            cls._instance.path = path
        return cls._instance

    def __init__(self, path):
        # Viewer#file_dict: Dict {
        #    filepath (string): Dict {
        #        function_name (string): Tuple {
        #            Mechanism,
        #            List {
        #                line (Dict {
        #                'text': line_of_code (string),
        #                'indent': indent_level (integer)
        #                }),
        #                line (Dict {
        #                    ...
        #                }),
        #                ...
        self.file_dict = self.map_directory(path)

    @property
    def mechanisms(self):
        mechanisms_list = []
        for filepath in self.file_dict.keys():
            file_data = self.file_dict[filepath]
            for func_name, func_info in file_data.items():
                mechanisms_list.append(func_info[0])
                
        return mechanisms_list

    def generate_report(self, whitelist=None):
        from utils import count_tokens_with_tiktoken

        if not whitelist:
            from conf import WHITELIST
            whitelist = WHITELIST

        # Generate the dir_dump report
        report = "----\ndir_dump\n----\n"
        report += self.dir_dump()

        # Generate the spec_dump report
        spec_dump = self.spec_dump()
        report += "\n----\nspec_dump\n----\n"
        report += spec_dump

        report += "\n----\nfs_dump\n----\n"
        report += self.fs_dump(whitelist=whitelist)

        # Append token count to the end of the report
        token_count = count_tokens_with_tiktoken(report)
        report += f"\nTLEN={token_count}"

        # Combine the reports and create the project report
        project_report = f"let project_report = \n`{report}`;"

        return project_report

    def copy_report_to_clipboard(self):
        pyperclip.copy(self.generate_report())
        print("Report copied to clipboard!")

    def spec_dump(self):
        from conf import SPEC_INCLUDE
        from main import session
        from models.specification import Specification
        
        # Query the specifications from the database based on SPEC_INCLUDE
        included_specs = session.query(Specification).filter(Specification.id.in_(SPEC_INCLUDE)).all()
        
        # Generate the spec_dump report
        report = ""
        for spec in included_specs:
            report += str(spec) + "\n"
        
        return report

    def dir_dump(self):
        output = ""
        for root, dirs, files in os.walk(self.path):
            # Skip directories that start with an underscore, period, or "alembic"
            dirs[:] = [d for d in dirs if not d[0] in ['_', '.'] and d != "alembic"]
            
            # Add directories to output string
            for dir in dirs:
                output += os.path.join(root, dir) + "\n"
            
            # Add files to output string
            for file in files:
                output += os.path.join(root, file) + "\n"
                
        return output

    def fs_dump(self, whitelist=None):
        if not whitelist:
            from conf import WHITELIST
            whitelist = WHITELIST

        project_representation = ''
    
        for file_key, methods in self.file_dict.items():
            filepath = file_key.replace('_', os.sep).lstrip(os.sep) + '.py'

            whitelist_value = get_value(whitelist, filepath)
    
            if whitelist_value is True:
                with open(filepath, 'r') as file:
                    project_representation += f"\n~~ {filepath} ~~\n"
                    project_representation += file.read() + "\n"
                    
            else:
                project_representation += f"\n~~ {filepath} ~~\n"
                last_class_name = None
    
                for method_name, (mechanism, code_lines) in sorted(methods.items()):
                    if mechanism.class_name != last_class_name:
                        project_representation += f"\nclass {mechanism.class_name}:\n"
                        last_class_name = mechanism.class_name
    
                    param_strings = [f"{param}={value}" if value is not None else param for param, value in mechanism.params.items()]
                    project_representation += f"    def {method_name}({', '.join(param_strings)}):\n" 
    
                    if whitelist_value and method_name in whitelist_value:
                        formatted_code = "\n".join(["    " * c["indent"] + c["text"] for c in code_lines[1:]])
                        project_representation += formatted_code + "\n"
                    else:
                        project_representation += "        ...\n"
    
        return project_representation

    def get_file_funcs(self, filepath):
        from models.mechanism import Mechanism

        with open(filepath, "r") as source:
            source_content = source.read()
            tree = ast.parse(source_content)

        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]

        functions = [f for f in tree.body if isinstance(f, ast.FunctionDef) and not any(isinstance(node, ast.ClassDef) for node in ast.walk(f))]
        
        func_dict = {}
        for cls in classes:
            for f in cls.body:
                if isinstance(f, ast.FunctionDef):
                    code = ast.get_source_segment(source_content, f)
                    code_lines = [{'text': line.lstrip(), 'indent': (len(line) - len(line.lstrip())) // 4}
                                  for line in code.split('\n')]
                    params = {}
    
                    defaults = list(f.args.defaults)
                    defaults = [None] * (len(f.args.args) - len(defaults)) + defaults
    
                    for arg, default_value in zip(f.args.args, defaults):
                        arg_name = arg.arg
                        default_value = ast.literal_eval(default_value) if default_value is not None else None
                        params[arg_name] = default_value
    
                    mechanism = Mechanism.create(name=f.name,
                                                 params=params,
                                                 class_name=cls.name)
                    func_dict[f.name] = (mechanism, code_lines)

        for f in functions:
            code = ast.get_source_segment(source_content, f)
            code_lines = [{'text': line.lstrip(), 'indent': (len(line) - len(line.lstrip())) // 4}
                          for line in code.split('\n')]
            params = {}

            defaults = list(f.args.defaults)
            defaults = [None] * (len(f.args.args) - len(defaults)) + defaults

            for arg, default_value in zip(f.args.args, defaults):
                arg_name = arg.arg
                default_value = ast.literal_eval(default_value) if default_value is not None else None
                params[arg_name] = default_value

            mechanism = Mechanism.create(name=f.name,
                                         params=params,
                                         class_name=None)
            func_dict[f.name] = (mechanism, code_lines)
        
        return func_dict
 
    def old_get_file_funcs(self, filepath):
        from models.mechanism import Mechanism
    
        with open(filepath, "r") as source:
            source_content = source.read()
            tree = ast.parse(source_content)
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    
        func_dict = {}
        for cls in classes:
            for f in cls.body:
                if isinstance(f, ast.FunctionDef):
                    code = ast.get_source_segment(source_content, f)
                    code_lines = [{'text': line.lstrip(), 'indent': (len(line) - len(line.lstrip())) // 4}
                                for line in code.split('\n')]
                    params = {}
    
                    defaults = list(f.args.defaults)
                    defaults = [None] * (len(f.args.args) - len(defaults)) + defaults
    
                    for arg, default_value in zip(f.args.args, defaults):
                        arg_name = arg.arg
                        default_value = ast.literal_eval(default_value) if default_value is not None else None
                        params[arg_name] = default_value
    
                    mechanism = Mechanism.create(name=f.name,
                                            params=params,
                                            class_name=cls.name)
                    func_dict[f.name] = (mechanism, code_lines)
        return func_dict

    def map_directory(self, path):
        file_dict = {}
        for root, dirs, files in os.walk(path):
            # Skip alembic directories
            if 'alembic' in dirs:
                dirs.remove('alembic')
            for file in files:
                if file.endswith(".py"):
                    nested_path = os.path.join(root, file).split(path)[1].split(os.sep)
                    key = create_key_from_path(os.path.join(root, file))
                    file_dict[key] = self.get_file_funcs(os.path.join(root, file))
        return file_dict 

    def get_method(self, func_name_with_path):
        func_key, func_name = func_name_with_path.split("#")
    
        methods = self.file_dict.get(func_key, None)
        if methods is not None:
            for method_key, method_info in methods.items():
                if method_key == func_name:
                    mechanism, code_lines = method_info
                    formatted_code = "\n".join([
                        "    " * c["indent"] + c["text"] for c in code_lines
                    ])
                    class_def = f"class {mechanism.class_name}:"

                    param_strings = [f"{param}={value}" if value else param for param, value in mechanism.params.items()]
                    func_def = f"    def {method_key}({', '.join(param_strings)}):"

                    return class_def + "\n" + func_def + formatted_code
        return None

