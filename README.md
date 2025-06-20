# Parliament Attendance System

[![Open in Dev Containers](https://img.shields.io/static/v1?label=Dev%20Containers&message=Open&color=blue)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/microsoft/vscode-remote-try-java)

This project is a Parliament Attendance System that allows for tracking attendance of members in a parliamentary setting. It is designed to be run in a development container for ease of setup and consistency across environments.

## Getting Started

To get started with the project, follow these steps:

1. **Clone the Repository**
   ```bash
   git clone https://github.com/diplomegalo/parliament-attendance.git
   cd parliament-attendance
   ```

2. **Open in Development Container**
   If you are using Visual Studio Code, you can open the project in a development container. Make sure you have the Remote - Containers extension installed. Then, use the command palette (Ctrl+Shift+P) and select `Remote-Containers: Open Folder in Container...`.

3. **Install Dependencies**
   The required Python packages are listed in `requirements.txt`. They will be installed automatically when the container is built. If you need to install them manually, run:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application**
   The main entry point of the application is located in `src/main.py`. You can run the application using:
   ```bash
   python src/main.py
   ```

## Project Structure

- **.devcontainer/**: Contains configuration files for the development container.
  - **devcontainer.json**: Configuration for the development container.
  - **Dockerfile**: Defines the environment for the development container.
  
- **src/**: Contains the source code for the application.
  - **main.py**: The main entry point of the application.

- **requirements.txt**: Lists the Python dependencies required for the project.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or improvements.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
