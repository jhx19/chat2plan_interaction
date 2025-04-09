# Step-by-Step Guide to Setting Up the Web Interface

This guide provides detailed instructions for setting up and running the web interface for your Architecture AI Design System, even if you have no previous experience with web development.

## 1. Setting Up the Directory Structure

First, let's create the required directory structure:

1. Create a `templates` folder in your project root (if it doesn't already exist)
2. Create a `static` folder in your project root (if it doesn't already exist)
3. Inside the `static` folder, create a `css` folder and a `js` folder

Your directory structure should look like this:

```
project_root/
├── main.py                 # Your existing main.py file
├── templates/              # For HTML templates
├── static/                 # For static files
│   ├── css/                # For CSS stylesheets
│   └── js/                 # For JavaScript files
```

## 2. Creating the Files

Now, let's create all the necessary files:

1. In the project root, create a file named `app.py` with the content from the "app.py" artifact
2. In the `templates` folder, create a file named `index.html` with the content from the "templates/index.html" artifact
3. In the `static/css` folder, create a file named `styles.css` with the content from the "static/css/styles.css" artifact
4. In the `static/js` folder, create a file named `main.js` with the content from the "static/js/main.js" artifact

## 3. Installing Required Packages

You'll need to install Flask and other required packages. Open your terminal or command prompt and run:

```bash
pip install flask python-dotenv requests
```

If you haven't already installed the dependencies for your main system, you should also run:

```bash
pip install -r requirements.txt
```

## 4. Running the Web Interface

Now you're ready to run the web interface:

1. Open your terminal or command prompt
2. Navigate to your project root directory
3. Run the following command:

```bash
python app.py
```

4. You should see output similar to this:

```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://0.0.0.0:5000 (Press CTRL+C to quit)
```

5. Open your web browser and go to: `http://localhost:5000`

## 5. Using the Web Interface

1. **Start a new session**:
   - Click the "New Session" button in the top right corner
   - The system will initialize and show you the first stage: "Requirement Gathering"

2. **Interact with the system**:
   - Type your building project requirements in the input field at the bottom
   - Press "Send" or hit Enter to submit your message
   - The system will respond and guide you through the process

3. **Monitor progress**:
   - The progress bar at the top shows your current stage
   - The "System State" panel at the bottom shows detailed information about requirements, spatial understanding, and key questions

4. **View visualizations**:
   - As you progress through the stages, visualizations will appear on the right side
   - Use the tabs to switch between different visualizations

5. **Advanced: Resume a session**:
   - If you need to close the browser but want to continue later
   - Look for your session ID in the terminal output or check the "sessions" folder
   - When you restart, click "Resume Session" and enter the session path (e.g., "sessions/20240410_123456")

## 6. Troubleshooting

If you encounter any issues:

1. **Web interface doesn't load**:
   - Check that the Flask application is running in your terminal
   - Ensure no other application is using port 5000
   - Try accessing the URL: `http://127.0.0.1:5000` instead of localhost

2. **Visualizations don't appear**:
   - Check if the "sessions" directory exists and has write permissions
   - Look at the terminal output for any error messages related to file creation

3. **Error messages in the chat**:
   - Check the terminal running Flask for more detailed error logs
   - If the system mentions API keys, ensure your environment variables are set correctly

4. **Web interface freezes**:
   - The system may be processing a complex request
   - Check the terminal output to see if the system is still working
   - If necessary, restart the Flask application with `python app.py`

## 7. Customization (Optional)

If you want to change the appearance or behavior:

- **Colors and styling**: Edit the `static/css/styles.css` file
- **Page layout**: Edit the `templates/index.html` file
- **Interaction behavior**: Edit the `static/js/main.js` file
- **Backend functionality**: Edit the `app.py` file

Remember to refresh your browser after making changes to see the updates.