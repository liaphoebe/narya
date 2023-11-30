class Composer:
    def __init__(self, filename):
        self.filename = filename
        self.lines = self.decompose()

    def decompose(self):
        with open(self.filename, 'r') as f:
            lines = [{'line_number': idx+1, 
                      'code': line.lstrip().rstrip(), 
                      'manipulated': False, 
                      'indent': (len(line) - len(line.lstrip())) // 4} 
                      for idx,line in enumerate(f.readlines())]
        return lines

    def modify(self, existing_code, replacement_code):
        for i in range(len(self.lines) - len(existing_code) + 1):
            if [line['code'] for line in self.lines[i:i+len(existing_code)]] == existing_code:
                del self.lines[i:i+len(existing_code)]
                for j, _code in enumerate(replacement_code):
                    self.lines.insert(i+j, {'line_number': i+1+j,
                                             'code': _code,
                                             'manipulated': True,
                                             'indent': self.lines[i]['indent']})
                break
        self.massage()

    def insert_code_above(self, code, line):
        for i in range(len(self.lines) - 1, -1, -1):
            if self.lines[i]['code'] == line:
                for j, _code in enumerate(code):
                    self.lines.insert(i+j, {'line_number': i+1+j,
                                             'code': _code,
                                             'manipulated': True,
                                             'indent': self.lines[i]['indent']})
                break
        self.massage()

    def insert(self, code, at):
        for i, _code in enumerate(code):
            self.lines.insert(at-1+i, {'line_number': at+i, 
                                        'code': _code, 
                                        'manipulated': True, 
                                        'indent': (len(_code) - len(_code.lstrip())) // 4})
        self.massage()

    def replace(self, code, _from, to):
        del self.lines[_from-1:to]
        for i, _code in enumerate(code):
            self.lines.insert(_from-1+i, {'line_number': _from+i, 
                                           'code': _code, 
                                           'manipulated': True, 
                                           'indent': (len(_code) - len(_code.lstrip())) // 4})
        self.massage()

    def remove(self, at):
        del self.lines[at-1]
        self.massage()

    def debug(self, at):
        debug_statement = '''import pdb; pdb.set_trace()\n'''
        indent = self.lines[at-1]['indent']
        self.lines.insert(at-1, {'line_number': at, 
                                  'code': debug_statement, 
                                  'manipulated': True, 
                                  'indent': indent})
        self.massage()

    def massage(self):
        for idx, line in enumerate(self.lines):
            line['line_number'] = idx+1
            line['manipulated'] = False

    def recompose(self):
        # new_filename = 'MOD_' + self.filename
        with open(self.filename, 'w') as f:
            for line in self.lines:
                f.write(line['indent'] * '    ' + line['code'] + '\n')
