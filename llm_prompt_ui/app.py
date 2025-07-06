from flask import Flask, render_template

# When running this app.py, Flask will look for 'templates' and 'static'
# folders in the same directory as app.py (i.e., within 'llm_prompt_ui/').
# The project structure is:
# llm_prompt_ui/
#   app.py
#   static/
#   templates/
# This is standard and should work without explicit static_folder/template_folder.
app = Flask(__name__)


@app.route("/")
def home():
    # This will look for 'index.html' in the 'llm_prompt_ui/templates/' directory.
    return render_template("index.html")


if __name__ == "__main__":
    # It's good practice to specify host and port for clarity,
    # especially if it might be run in different environments.
    # For development, 0.0.0.0 makes it accessible from other devices on the network.
    app.run(host="0.0.0.0", port=5000, debug=True)
