from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import json
import uuid
import threading
import queue
import sys
from main import ArchitectureAISystem

app = Flask(__name__, static_folder='static', template_folder='templates')

# Store active sessions
sessions = {}
# Store session output queues
output_queues = {}

class OutputCapture:
    """Capture stdout to intercept terminal output from the system"""
    def __init__(self, queue):
        self.queue = queue
        self.original_stdout = sys.stdout
        
    def write(self, text):
        # Write to the original stdout
        self.original_stdout.write(text)
        # Also put in the queue for the web interface
        if text.strip():  # Ignore empty lines
            self.queue.put(text)
            
    def flush(self):
        self.original_stdout.flush()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/start', methods=['POST'])
def start_session():
    session_id = str(uuid.uuid4())
    
    # Create a queue for capturing output
    output_queue = queue.Queue()
    output_queues[session_id] = output_queue
    
    # Start the system in a background thread
    def run_system():
        # Capture system output
        original_stdout = sys.stdout
        sys.stdout = OutputCapture(output_queue)
        
        try:
            # Initialize the system
            system = ArchitectureAISystem()
            sessions[session_id] = system
            
            # Signal that initialization is complete
            output_queue.put("INIT_COMPLETE")
        finally:
            # Restore stdout
            sys.stdout = original_stdout
    
    thread = threading.Thread(target=run_system)
    thread.daemon = True
    thread.start()
    
    # Wait for initialization to complete
    try:
        msg = output_queue.get(timeout=10)  # 10 second timeout
        if msg == "INIT_COMPLETE":
            pass  # Initialization completed successfully
    except queue.Empty:
        return jsonify({'error': 'Session initialization timed out'}), 500
    
    return jsonify({'session_id': session_id})

@app.route('/api/resume', methods=['POST'])
def resume_session():
    data = request.json
    session_path = data.get('session_path')
    
    if not session_path or not os.path.exists(session_path):
        return jsonify({'error': 'Invalid session path'}), 400
    
    session_id = str(uuid.uuid4())
    
    # Create a queue for capturing output
    output_queue = queue.Queue()
    output_queues[session_id] = output_queue
    
    # Start the system in a background thread
    def run_system():
        # Capture system output
        original_stdout = sys.stdout
        sys.stdout = OutputCapture(output_queue)
        
        try:
            # Initialize the system with resumed session
            system = ArchitectureAISystem(resume_session_path=session_path)
            sessions[session_id] = system
            
            # Signal that initialization is complete
            output_queue.put("INIT_COMPLETE")
        finally:
            # Restore stdout
            sys.stdout = original_stdout
    
    thread = threading.Thread(target=run_system)
    thread.daemon = True
    thread.start()
    
    # Wait for initialization to complete
    try:
        msg = output_queue.get(timeout=10)  # 10 second timeout
        if msg == "INIT_COMPLETE":
            pass  # Initialization completed successfully
    except queue.Empty:
        return jsonify({'error': 'Session initialization timed out'}), 500
    
    return jsonify({'session_id': session_id})

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    session_id = data.get('session_id')
    user_input = data.get('message')
    
    if not session_id or session_id not in sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    system = sessions[session_id]
    output_queue = output_queues[session_id]
    
    # Get current stage before processing input
    current_stage = system.workflow_manager.get_current_stage()
    
    # Create a queue for the response
    response_queue = queue.Queue()
    
    # Process user input in a background thread
    def process_input():
        try:
            # Record the user input using the session manager
            system.session_manager.add_user_input(user_input)
            
            # Process based on current stage
            if current_stage == system.workflow_manager.STAGE_REQUIREMENT_GATHERING:
                # Process user input and get next question
                response = system.process_user_input(user_input)
                
                # Record the system response
                system.session_manager.add_system_response(response)
                
                # Put response in queue
                response_queue.put({
                    'response': response,
                    'new_stage': system.workflow_manager.get_current_stage()
                })
            
            elif current_stage == system.workflow_manager.STAGE_CONSTRAINT_REFINEMENT:
                # Handle skip command
                if user_input.lower() in ["skip", "跳过"]:
                    system.workflow_manager.advance_to_next_stage()
                    response_queue.put({
                        'response': "Skipping constraint refinement stage.",
                        'new_stage': system.workflow_manager.get_current_stage()
                    })
                else:
                    # Refine constraints
                    refined_constraints, diff_table = system.constraint_refinement.refine_constraints(
                        system.constraints_all,
                        user_input,
                        system.spatial_understanding_record
                    )
                    
                    # Update constraints
                    system.constraints_all = refined_constraints
                    system.constraints_rooms = system.converter.all_to_rooms(refined_constraints)
                    
                    # Record constraints state
                    system.session_manager.update_constraints({
                        "all": system.constraints_all, 
                        "rooms": system.constraints_rooms
                    })
                    
                    # Generate visualization
                    system.constraint_visualization.visualize_constraints(
                        system.constraints_all,
                        output_path=os.path.join(
                            system.session_manager.get_session_dir(), 
                            f"constraints_visualization_refined_{system.workflow_manager.current_iteration}.png"
                        )
                    )
                    
                    response_queue.put({
                        'response': "Constraints refined based on your feedback.",
                        'new_stage': system.workflow_manager.get_current_stage()
                    })
            
            elif current_stage == system.workflow_manager.STAGE_SOLUTION_REFINEMENT:
                # Handle skip command
                if user_input.lower() in ["skip", "跳过"]:
                    system.workflow_manager.advance_to_next_stage()
                    response_queue.put({
                        'response': "Skipping solution refinement stage.",
                        'new_stage': system.workflow_manager.get_current_stage()
                    })
                else:
                    # Refine solution
                    refined_constraints, diff_table = system.solution_refinement.refine_solution(
                        system.constraints_all,
                        system.current_solution,
                        user_input,
                        system.spatial_understanding_record
                    )
                    
                    # Update constraints
                    system.constraints_all = refined_constraints
                    system.constraints_rooms = system.converter.all_to_rooms(refined_constraints)
                    
                    # Record constraints state
                    system.session_manager.update_constraints({
                        "all": system.constraints_all, 
                        "rooms": system.constraints_rooms
                    })
                    
                    # Advance to solution generation stage
                    system.workflow_manager.advance_to_next_stage()
                    
                    response_queue.put({
                        'response': "Layout feedback recorded. Regenerating solution...",
                        'new_stage': system.workflow_manager.get_current_stage()
                    })
        except Exception as e:
            import traceback
            traceback.print_exc()
            response_queue.put({
                'error': str(e),
                'new_stage': system.workflow_manager.get_current_stage()
            })
    
    # Start processing thread
    thread = threading.Thread(target=process_input)
    thread.daemon = True
    thread.start()
    
    # Wait for response with timeout
    try:
        result = response_queue.get(timeout=60)  # 60 second timeout
        
        # Check if stage changed
        new_stage = result.get('new_stage')
        stage_changed = new_stage != current_stage
        
        response = {
            'response': result.get('response', ''),
            'stage_change': stage_changed,
            'current_stage': new_stage,
            'stage_description': system.workflow_manager.get_stage_description()
        }
        
        if stage_changed:
            response['next_stage'] = new_stage
            
            # If moving to constraint generation, start that process
            if new_stage == system.workflow_manager.STAGE_CONSTRAINT_GENERATION:
                # Launch constraint generation in a background thread
                def generate_constraints():
                    system.finalize_constraints()
                    system.workflow_manager.advance_to_next_stage()
                
                threading.Thread(target=generate_constraints, daemon=True).start()
            
            # If moving to solution generation, start that process
            elif new_stage == system.workflow_manager.STAGE_SOLUTION_GENERATION:
                # Launch solution generation in a background thread
                def generate_solution():
                    system.current_solution = system.call_solver(system.constraints_all)
                    system.session_manager.add_intermediate_state(
                        f"solution_generation_{system.workflow_manager.current_iteration}",
                        {"solution": system.current_solution}
                    )
                    system.workflow_manager.advance_to_next_stage()
                
                threading.Thread(target=generate_solution, daemon=True).start()
            
        return jsonify(response)
        
    except queue.Empty:
        return jsonify({'error': 'Processing timed out'}), 500

@app.route('/api/state', methods=['GET'])
def get_state():
    session_id = request.args.get('session_id')
    
    if not session_id or session_id not in sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    system = sessions[session_id]
    current_stage = system.workflow_manager.get_current_stage()
    
    return jsonify({
        'current_stage': current_stage,
        'stage_description': system.workflow_manager.get_stage_description(),
        'user_requirement_guess': system.user_requirement_guess,
        'spatial_understanding_record': system.spatial_understanding_record,
        'key_questions': system.key_questions
    })

@app.route('/api/visualize', methods=['GET'])
def get_visualization():
    session_id = request.args.get('session_id')
    
    if not session_id or session_id not in sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    system = sessions[session_id]
    session_dir = system.session_manager.get_session_dir()
    
    # Return paths to visualization images
    visualizations = []
    if os.path.exists(session_dir):
        for filename in os.listdir(session_dir):
            if filename.endswith('.png'):
                visualizations.append(f'/sessions/{os.path.basename(session_dir)}/{filename}')
    
    return jsonify({'visualizations': visualizations})

@app.route('/sessions/<path:path>')
def serve_session_file(path):
    sessions_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sessions')
    return send_from_directory(sessions_dir, path)

@app.route('/api/skip_stage', methods=['POST'])
def skip_stage():
    session_id = request.json.get('session_id')
    
    if not session_id or session_id not in sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    system = sessions[session_id]
    current_stage = system.workflow_manager.get_current_stage()
    
    # Advance to the next stage
    system.workflow_manager.advance_to_next_stage()
    new_stage = system.workflow_manager.get_current_stage()
    
    # Handle special actions for certain stages
    if new_stage == system.workflow_manager.STAGE_CONSTRAINT_GENERATION:
        # Launch constraint generation in a background thread
        def generate_constraints():
            system.finalize_constraints()
            system.workflow_manager.advance_to_next_stage()
        
        threading.Thread(target=generate_constraints, daemon=True).start()
    
    elif new_stage == system.workflow_manager.STAGE_SOLUTION_GENERATION:
        # Launch solution generation in a background thread
        def generate_solution():
            system.current_solution = system.call_solver(system.constraints_all)
            system.session_manager.add_intermediate_state(
                f"solution_generation_{system.workflow_manager.current_iteration}",
                {"solution": system.current_solution}
            )
            system.workflow_manager.advance_to_next_stage()
        
        threading.Thread(target=generate_solution, daemon=True).start()
    
    return jsonify({
        'previous_stage': current_stage,
        'current_stage': new_stage,
        'stage_description': system.workflow_manager.get_stage_description()
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)