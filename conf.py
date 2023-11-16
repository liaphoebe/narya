PROJECT_DIR = '.'
SPEC_INCLUDE = [ 7 ]
TEST_CMD = "python3 main.py -sa"
WHITELIST = {
    #'viewer.py': [ 'get_file_funcs' ],
    'main.py': True,
    #'models/specification.py': True,
    'conf.py': True,
    'app.py': True,
    'tester.py': True,
    #'utils.py': True,
    #'models/mechanism.py': True,
    'interactor.py': [ 'gpt'  ],
    #'composer.py': True
}

