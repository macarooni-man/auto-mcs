import sys
import subprocess
import os

def main():
    os.environ['KIVY_GL_BACKEND'] = 'mock'
    
    root = os.path.abspath(os.path.dirname(__file__))
    existing = os.environ.get('PYTHONPATH', '')
    os.environ['PYTHONPATH'] = f"{root}{os.pathsep}{existing}" if existing else root
    
    pytest_bin = os.path.join("venv", "Scripts", "pytest.exe") if os.name == 'nt' else os.path.join("venv", "bin", "pytest")
    if not os.path.exists(pytest_bin):
        pytest_bin = "pytest"
        
    args = [pytest_bin, "tests", "-v"]
    if len(sys.argv) > 1:
        args.extend(sys.argv[1:])
        
    print(f"Running: {' '.join(args)}")
    sys.exit(subprocess.run(args).returncode)

if __name__ == "__main__":
    main()
