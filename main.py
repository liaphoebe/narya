import argparse
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models.base import Base
from models.project import Project
from models.dependency import Dependency
from models.specification import Specification
from conf import PROJECT_DIR
from app import Application
from interactor import Interactor

engine = create_engine('sqlite:///example.db', echo=False)
session = Session(engine)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Generate a code summary report.")
    parser.add_argument("-sa", action="store_true",
                        help="Generate a summary for all files in the directory.")
    parser.add_argument("-c", action="store_true",
                        help="Copy report to clipboard.")
    parser.add_argument("-s", nargs=2, help="Specify goal for a particular file.")
    parser.add_argument("-t", action="store_true", help="Perform the test.")
    parser.add_argument("-p", action="store_true", help="Ping GPT.")
    args = parser.parse_args()

    # Database setup
    Base.metadata.create_all(engine)  # Create tables; won't affect existing tables

    # Create application instance
    app = Application.create_application(PROJECT_DIR)

    if args.s:
        filename, goal_string = args.s
        with open(filename, 'r') as file:
            direction = file.read()
        Specification.insert(session, None, goal_string, direction, 0, 0)
        print('Specification inserted successfully.')

    if args.sa:
        from models.mechanism import Mechanism

        interactor = Interactor()
        func_summaries = interactor.summarize_functions()

        # update the summaries to the corresponding mechanisms in the database
        for func_name, func_summary in func_summaries.items():
            class_name, name = func_name.split("#")
            mechanism = session.query(Mechanism).filter_by(name=name, class_name=class_name).first()
            if mechanism is not None:
                mechanism.summary = func_summary
        session.commit()

        print('Done.')
    
    if args.c:
        app.viewer.copy_report_to_clipboard()

    if args.t:
        from tester import Tester

        tester = Tester()
        tester.perform()

    if args.p:
        print(Interactor.ping())
        

    return app

if __name__ == "__main__":
    main()
else:
    app_instance = Application('')

