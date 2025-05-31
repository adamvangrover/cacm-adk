# backend_app.py (Conceptual Flask example)
from flask import Flask, request, jsonify
import subprocess # To run the C program
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

# Path to your compiled C control program
# Assuming it's in the same directory as this script or on PATH
C_CONTROL_PROGRAM = "./adk_controller" # Or "adk_controller.exe" on Windows

@app.route('/api/chatbot', methods=['POST'])
def handle_chatbot_command():
    data = request.get_json()
    user_command = data.get('command')

    if not user_command:
        app.logger.warning("No command received from user.")
        return jsonify({"reply": "Error: No command received."}), 400

    app.logger.info(f"Received command: {user_command}")
    bot_reply = ""
    try:
        # Example: "control java system start_service --id=123"
        # You might need to parse user_command to extract target system (Java/Python)
        # and specific C program arguments.
        # For simplicity, let's assume the C program takes the whole command string.
        #
        # Security Note: Directly passing user input to a subprocess can be risky.
        # Sanitize and validate `user_command` thoroughly.
        # Construct arguments carefully.

        # Example: Distinguish between controlling Python or Java
        # This logic would be more sophisticated based on user input parsing.
        # For instance, user might type: "java agent do_task_X" or "python sensor read_value"

        target_system = "" # Determine this from user_command
        # These args are for the C_CONTROL_PROGRAM, not the command itself initially
        c_program_invocation_args = [C_CONTROL_PROGRAM]

        # Basic parsing to determine target and construct arguments for C_CONTROL_PROGRAM
        # This is a simplified example; real parsing might be more complex.
        command_parts = user_command.lower().split()

        if not command_parts:
            return jsonify({"reply": "Sorry, the command was empty."}), 200

        if "java" in command_parts: # Very basic parsing
            target_system = "java"
            c_program_invocation_args.extend(["--target", "java", "--command", user_command])
        elif "python" in command_parts:
            target_system = "python"
            c_program_invocation_args.extend(["--target", "python", "--command", user_command])
        else:
            # Default behavior: pass the command directly if no clear target is found
            # This might be useful if the C program itself can parse the target
            # Or, return an error if a target is always required
            # For this example, let's assume the C program can handle it or it's an error.
            # Adding a log for this case:
            app.logger.info(f"No specific target (java/python) detected in command: '{user_command}'. Passing full command to adk_controller.")
            # If adk_controller expects --command always, this needs adjustment.
            # For now, let's assume a more flexible adk_controller or one that defaults.
            # A safer default might be to return an error:
            # return jsonify({"reply": "Sorry, I didn't understand which system to control (Python or Java). Please specify 'java' or 'python' in your command."}), 200

            # For this iteration, let's assume the C program is invoked with the raw command if no keyword is found
            # This makes the C program responsible for parsing the command string passed via --command
            c_program_invocation_args.extend(["--command", user_command])


        app.logger.info(f"Executing C program with args: {' '.join(c_program_invocation_args)}")
        # Execute the C control program
        # The C program would then use REST/CLI to talk to the actual ADK agents
        process = subprocess.Popen(c_program_invocation_args,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   text=True)
        stdout, stderr = process.communicate(timeout=30) # Increased timeout

        app.logger.info(f"C program stdout: {stdout}")
        app.logger.info(f"C program stderr: {stderr}")
        app.logger.info(f"C program return code: {process.returncode}")

        if process.returncode == 0:
            if stdout:
                bot_reply = f"Command executed. Output:\n{stdout}"
            else:
                bot_reply = f"Command for {target_system or 'system'} acknowledged and likely succeeded (no specific output)."
        else:
            error_message = f"Error executing command"
            if target_system:
                error_message += f" for {target_system}"
            error_message += f". Return code: {process.returncode}"
            if stderr:
                error_message += f"\nError details:\n{stderr}"
            if stdout: # Include stdout even on error, as it might contain useful info
                error_message += f"\nOutput:\n{stdout}"
            bot_reply = error_message
            app.logger.error(bot_reply)


    except subprocess.TimeoutExpired:
        bot_reply = "Error: The control command timed out after 30 seconds."
        app.logger.error(bot_reply)
    except FileNotFoundError:
        bot_reply = f"Error: C control program '{C_CONTROL_PROGRAM}' not found. Please ensure it is in the 'api/' directory and executable."
        app.logger.error(bot_reply)
    except Exception as e:
        bot_reply = f"An internal server error occurred: {str(e)}"
        app.logger.error(f"Chatbot backend error: {e}", exc_info=True) # Log stack trace

    return jsonify({"reply": bot_reply})

if __name__ == '__main__':
    # For development only. Use a proper WSGI server for production.
    # Ensure host is '0.0.0.0' to be accessible from outside Docker if run in a container
    app.run(host='0.0.0.0', port=5001, debug=True)
