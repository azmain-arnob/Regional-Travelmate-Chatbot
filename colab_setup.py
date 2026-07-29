import os
import subprocess

def setup_environment():
    """
    Installs required dependencies for running the application on Google Colab.
    """
    print("Installing project dependencies from requirements.txt...")
    try:
        subprocess.run(["pip", "install", "-r", "requirements.txt"], check=True)
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")

if __name__ == "__main__":
    setup_environment()
