from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import json
import uuid
import threading
import queue
import sys
import time
import traceback
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

@app.route('/api/check_visualization_files', methods=['GET'])
def check_visualization_files():
    session_id = request.args.get('session_id')
    
    if not session_id or session_id not in sessions:
        return jsonify({'error': '无效的会话ID'}), 400
    
    system = sessions[session_id]
    session_dir = system.session_manager.get_session_dir()
    
    print(f"检查可视化文件夹: {session_dir}")
    
    files = {}
    
    # 检查特定文件是否存在
    room_graph_file = os.path.join(session_dir, "constraints_visualization.png")
    if os.path.exists(room_graph_file):
        files['room_graph'] = f'/sessions/{os.path.basename(session_dir)}/constraints_visualization.png'
        print(f"找到房间图: {room_graph_file}")
    
    table_file = os.path.join(session_dir, "constraints_visualization_table.png")
    if os.path.exists(table_file):
        files['constraints_table'] = f'/sessions/{os.path.basename(session_dir)}/constraints_visualization_table.png'
        print(f"找到约束表格: {table_file}")
    
    # 检查是否有布局方案相关文件（模式匹配）
    layout_files = []
    for f in os.listdir(session_dir):
        if (f.startswith('solution') or 'layout' in f.lower()) and f.endswith('.png'):
            layout_files.append(f)
    
    if layout_files:
        files['layout'] = f'/sessions/{os.path.basename(session_dir)}/{layout_files[0]}'
        print(f"找到布局方案: {layout_files[0]}")
    
    return jsonify({'files': files if files else None})

@app.route('/api/list_sessions', methods=['GET'])
def list_sessions():
    """List all available sessions in reverse chronological order (newest first)"""
    sessions_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sessions')
    
    if not os.path.exists(sessions_dir):
        return jsonify({'sessions': []})
    
    # Get all session directories
    session_dirs = []
    for item in os.listdir(sessions_dir):
        item_path = os.path.join(sessions_dir, item)
        if os.path.isdir(item_path):
            # Check if it contains session_record.json to confirm it's a valid session
            if os.path.exists(os.path.join(item_path, 'session_record.json')):
                # Get directory creation time for sorting
                try:
                    creation_time = os.path.getctime(item_path)
                    session_dirs.append((item, creation_time))
                except:
                    # If can't get creation time, use 0 (will be at the end)
                    session_dirs.append((item, 0))
    
    # Sort by creation time (newest first)
    session_dirs.sort(key=lambda x: x[1], reverse=True)
    
    # Return just the directory names
    return jsonify({'sessions': [s[0] for s in session_dirs]})

@app.route('/api/resume', methods=['POST'])
def resume_session():
    data = request.json
    session_path = data.get('session_path')
    
    if not session_path:
        return jsonify({'error': 'Session path is required'}), 400
    
    # Convert relative path to full path if needed
    if not os.path.isabs(session_path):
        sessions_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sessions')
        full_path = os.path.join(sessions_dir, session_path)
    else:
        full_path = session_path
    
    if not os.path.exists(full_path):
        return jsonify({'error': f'Session path not found: {full_path}'}), 400
    
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
            system = ArchitectureAISystem(resume_session_path=full_path)
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
                    # Report progress via stdout (which is captured by OutputCapture)
                    print("Starting constraint generation process...")
                    
                    # Generate constraints
                    try:
                        # Generate constraints
                        system.finalize_constraints()
                        
                        print("Constraint generation complete! Moving to visualization stage...")
                        
                        # Move to visualization stage
                        system.workflow_manager.advance_to_next_stage()
                        
                        # Visualization will happen automatically in the next stage
                        print("Generating constraint visualizations...")
                        
                        try:
                            # We need to explicitly call visualization here since the main loop won't do it
                            output_dir = os.path.join(system.session_manager.get_session_dir(), "constraints_visualization.png")
                            viz_result = system.constraint_visualization.visualize_constraints(
                                system.constraints_all,
                                output_path=output_dir
                            )
                            
                            print(f"Visualization complete! Files created at: {output_dir}")
                            
                            # Advance to refinement stage after a delay to allow frontend to update
                            time.sleep(2)
                            system.workflow_manager.advance_to_next_stage()
                            print("Advanced to refinement stage!")
                        except Exception as viz_error:
                            print(f"Error during visualization: {str(viz_error)}")
                            traceback.print_exc()
                            
                    except Exception as e:
                        print(f"Error in constraint generation: {str(e)}")
                        traceback.print_exc()
                
                threading.Thread(target=generate_constraints, daemon=True).start()
            
            # If moving to solution generation, start that process
            elif new_stage == system.workflow_manager.STAGE_SOLUTION_GENERATION:
                # Launch solution generation in a background thread
                def generate_solution():
                    print("Starting solution generation process...")
                    
                    # Generate solution
                    system.current_solution = system.call_solver(system.constraints_all)
                    
                    # Record solution
                    system.session_manager.add_intermediate_state(
                        f"solution_generation_{system.workflow_manager.current_iteration}",
                        {"solution": system.current_solution}
                    )
                    
                    print("Solution generation complete! Moving to refinement stage...")
                    
                    # Move to refinement stage
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
    
    # Check for constraint generation progress (simulated in this example)
    constraint_progress = None
    if current_stage == system.workflow_manager.STAGE_CONSTRAINT_GENERATION:
        # For now, we'll simulate progress. In a real implementation,
        # you'd need to track this in your main system logic.
        output_queue = output_queues.get(session_id)
        if output_queue and not output_queue.empty():
            # Check if there's any output about generation progress
            try:
                while not output_queue.empty():
                    message = output_queue.get_nowait()
                    if "generating" in message.lower() or "processing" in message.lower():
                        constraint_progress = {
                            'message': message,
                            'progress': 50  # Simulate 50% progress
                        }
            except:
                pass
    
    # Determine if all key questions are known
    all_key_questions_known = False
    if system.key_questions:
        all_key_questions_known = all(q.get('status') == '已知' for q in system.key_questions)
    
    return jsonify({
        'current_stage': current_stage,
        'stage_description': system.workflow_manager.get_stage_description(),
        'user_requirement_guess': system.user_requirement_guess,
        'spatial_understanding_record': system.spatial_understanding_record,
        'key_questions': system.key_questions,
        'all_key_questions_known': all_key_questions_known,
        'constraint_progress': constraint_progress
    })

@app.route('/api/visualize', methods=['GET'])
def get_visualization():
    session_id = request.args.get('session_id')
    
    if not session_id or session_id not in sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    system = sessions[session_id]
    session_dir = system.session_manager.get_session_dir()
    
    print(f"查找可视化图片文件夹: {session_dir}")
    
    # 返回可视化图片路径
    visualizations = []
    if os.path.exists(session_dir):
        for filename in os.listdir(session_dir):
            if filename.endswith('.png'):
                full_path = os.path.join(session_dir, filename)
                print(f"找到图片文件: {full_path}")
                url_path = f'/sessions/{os.path.basename(session_dir)}/{filename}'
                visualizations.append(url_path)
    
    print(f"找到 {len(visualizations)} 个可视化图片")
    
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
    
    print(f"Skipping stage: {current_stage}")
    
    # Advance to the next stage
    system.workflow_manager.advance_to_next_stage()
    new_stage = system.workflow_manager.get_current_stage()
    
    print(f"Advanced to stage: {new_stage}")
    
    # Handle special actions for certain stages
    if new_stage == system.workflow_manager.STAGE_CONSTRAINT_GENERATION:
        # Launch constraint generation in a background thread
        def generate_constraints():
            print("Skip triggered constraint generation...")
            try:
                system.finalize_constraints()
                print("Constraint generation complete!")
                system.workflow_manager.advance_to_next_stage()
                
                viz_stage = system.workflow_manager.get_current_stage()
                print(f"Now in stage: {viz_stage}")
                
                # Generate visualization
                print("Generating visualization...")
                output_dir = os.path.join(system.session_manager.get_session_dir(), "constraints_visualization.png")
                system.constraint_visualization.visualize_constraints(
                    system.constraints_all,
                    output_path=output_dir
                )
                print(f"Visualization complete! Files created at: {output_dir}")
                
                # Wait briefly to allow frontend to update
                time.sleep(2)
                
                # Advance to refinement stage
                system.workflow_manager.advance_to_next_stage()
                refinement_stage = system.workflow_manager.get_current_stage()
                print(f"Advanced to stage: {refinement_stage}")
            except Exception as e:
                print(f"Error in constraint generation after skip: {str(e)}")
                traceback.print_exc()
        
        threading.Thread(target=generate_constraints, daemon=True).start()
    
    elif new_stage == system.workflow_manager.STAGE_SOLUTION_GENERATION:
        # Launch solution generation in a background thread
        def generate_solution():
            try:
                print("Skip triggered solution generation...")
                system.current_solution = system.call_solver(system.constraints_all)
                system.session_manager.add_intermediate_state(
                    f"solution_generation_{system.workflow_manager.current_iteration}",
                    {"solution": system.current_solution}
                )
                print("Solution generation complete!")
                system.workflow_manager.advance_to_next_stage()
                refinement_stage = system.workflow_manager.get_current_stage()
                print(f"Advanced to solution refinement stage: {refinement_stage}")
            except Exception as e:
                print(f"Error in solution generation after skip: {str(e)}")
                traceback.print_exc()
        
        threading.Thread(target=generate_solution, daemon=True).start()
    
    return jsonify({
        'previous_stage': current_stage,
        'current_stage': new_stage,
        'stage_description': system.workflow_manager.get_stage_description()
    })
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)