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

    # Create initial and final states
    tm.node('q0', shape='circle')
    tm.node('q_accept', shape='doublecircle')
    tm.node('q_halt', shape='doublecircle')
    
    # Initialize current state
    current_state = 'q0'
    
    # Process each character in the misspelled and corrected words
    for i, (misspelled_char, corrected_char) in enumerate(zip(misspelled_word, corrected_word)):
        next_state = f'q{i+1}'
        move = 'R'  # Move right after processing each character
        color = 'black' if misspelled_char == corrected_char else 'red'
        transition_label = f'{misspelled_char}/{corrected_char},{move} ({"match" if misspelled_char == corrected_char else "mismatch"})'
        tm.edge(current_state, next_state, label=transition_label, color=color)
        current_state = next_state

    # Handle the case where corrected word is longer than the misspelled word
    if len(corrected_word) > len(misspelled_word):
        for j in range(len(misspelled_word), len(corrected_word)):
            next_state = f'q{j+1}'
            tm.edge(current_state, next_state, label=f'B/{corrected_word[j]},R (insert)', color='blue')
            current_state = next_state

    # Handle the case where misspelled word is longer than the corrected word
    if len(misspelled_word) > len(corrected_word):
        for j in range(len(corrected_word), len(misspelled_word)):
            next_state = f'q{j+1}'
            tm.edge(current_state, next_state, label=f'{misspelled_word[j]}/B,R (delete)', color='green')
            current_state = next_state

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
