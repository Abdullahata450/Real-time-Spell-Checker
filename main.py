from flask import Flask, render_template, request, jsonify
from spellchecker import SpellChecker
import graphviz
import os

app = Flask(__name__)
spell = SpellChecker()

# Ensure the 'static' directory exists for saving the graph images
os.makedirs('static', exist_ok=True)

# Function to generate Turing machine transitions and visualize it
def generate_turing_machine(misspelled_word, corrected_word):
    tm = graphviz.Digraph()

    # Create states
    states = ['q0', 'q_accept', 'q_halt', 'q_correct', 'q_compare', 'q_insert', 'q_delete']
    for state in states:
        tm.node(state, shape='doublecircle' if state in ['q_accept', 'q_halt'] else 'circle')
    
    current_state = 'q0'
    
    # Add transitions for comparison
    for i in range(max(len(misspelled_word), len(corrected_word))):
        if i < len(misspelled_word) and i < len(corrected_word):
            if misspelled_word[i] == corrected_word[i]:
                tm.edge(current_state, 'q_compare', label=f'{misspelled_word[i]}/{corrected_word[i]},R (match)', color='black')
                current_state = 'q_compare'
            else:
                tm.edge(current_state, 'q_correct', label=f'{misspelled_word[i]}/{corrected_word[i]},R (mismatch)', color='red')
                current_state = 'q_correct'
        elif i >= len(misspelled_word):
            tm.edge(current_state, 'q_insert', label=f'B/{corrected_word[i]},R (insert)', color='blue')
            current_state = 'q_insert'
        elif i >= len(corrected_word):
            tm.edge(current_state, 'q_delete', label=f'{misspelled_word[i]}/B,R (delete)', color='green')
            current_state = 'q_delete'
    
    # Link the last state to the accept state
    tm.edge(current_state, 'q_accept', label='B/B,R (accept)', color='purple')

    # Add an extra node for the corrected word
    tm.node('corrected', label=f'Corrected Word: {corrected_word}', shape='box', style='filled', color='lightgrey')

    # Link the accept state to the corrected word node
    tm.edge('q_accept', 'corrected', style='dashed', label='Output Corrected Word')

    # Add a transition to the halting state
    tm.edge('corrected', 'q_halt', label='B/B,R (halt)', style='dashed')

    # Save the graph
    graph_path = 'static/turing_machine_graph'
    tm.render(graph_path, format='png', cleanup=True)
    return f'{graph_path}.png'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check', methods=['POST'])
def check():
    user_input = request.json['text']
    words = user_input.split()
    corrected_words = [spell.correction(word) for word in words]
    corrected_phrase = ' '.join(corrected_words)

    is_correct = user_input.lower() == corrected_phrase.lower()

    if is_correct:
        message = f"The input '{user_input}' is spelled correctly."
        graph_path = generate_turing_machine(user_input, corrected_phrase)
    else:
        message = f"The input '{user_input}' has misspelled words. Correcting to '{corrected_phrase}'."
        graph_path = generate_turing_machine(user_input, corrected_phrase)

    return jsonify({'message': message, 'graph_path': graph_path})

if __name__ == '__main__':
    app.run(debug=True)
