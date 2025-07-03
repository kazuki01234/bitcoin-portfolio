import sys
from .gui import launch_gui
from .cli import run_cli

def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'cli':
        run_cli()
    else:
        launch_gui()

if __name__ == "__main__":
    main()
