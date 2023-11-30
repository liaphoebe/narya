from utils import count_tokens_with_tiktoken

class Logger:

    def __init__(self):
        # Looks like { file.py: [10, 101, ...], ... }
        self.sample_cache = {}

    @classmethod
    def print_sample(self, value, max_len=100):
        token_count = count_tokens_with_tiktoken(value)

        print(value[:int(min(max_len / token_count, 1) * len(value))])

    def old__init__(self, filename):
        self.filename = filename

    def old_log(self, string):
        with open(self.filename, 'a') as file:
            file.write(string + '\n')

def log(string, mode="sample"):
    Logger.print_sample(string)
