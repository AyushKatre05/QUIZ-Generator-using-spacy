import io
import PyPDF2
import streamlit as st
import spacy
import random
from collections import Counter
from typing import List

# Load English tokenizer, tagger, parser, NER, and word vectors
nlp = spacy.load("en_core_web_sm")

def generate_mcqs(text: str, num_questions: int = 5):
    if text is None:
        return []

    # Process the text with spaCy
    doc = nlp(text)

    # Extract sentences from the text
    sentences = [sent.text for sent in doc.sents]

    # Ensure that the number of questions does not exceed the number of sentences
    num_questions = min(num_questions, len(sentences))

    # Randomly select sentences to form questions
    selected_sentences = random.sample(sentences, num_questions)

    # Initialize list to store generated MCQs
    mcqs = []

    # Generate MCQs for each selected sentence
    for sentence in selected_sentences:
        # Process the sentence with spaCy
        sent_doc = nlp(sentence)

        # Extract entities (nouns) from the sentence
        nouns = [token.text for token in sent_doc if token.pos_ == "NOUN"]

        # Ensure there are enough nouns to generate MCQs
        if len(nouns) < 2:
            continue

        # Count the occurrence of each noun
        if nouns:  # Check if the list of nouns is not empty
            noun_counts = Counter(nouns)

            # Select the most common noun as the subject of the question
            subject = noun_counts.most_common(1)[0][0]

            # Generate the question stem
            question_stem = sentence.replace(subject, "______")

            # Generate answer choices
            answer_choices = [subject]

            # Add some random words from the text as distractors
            distractors = list(set(nouns) - {subject})

            # Ensure there are at least three distractors
            while len(distractors) < 3:
                distractors.append("[Distractor]")  # Placeholder for missing distractors

            random.shuffle(distractors)
            for distractor in distractors[:3]:
                answer_choices.append(distractor)

            # Shuffle the answer choices
            random.shuffle(answer_choices)

            # Append the generated MCQ to the list
            mcqs.append((question_stem, answer_choices, subject))

    return mcqs


def process_input(option: str):
    if option == "Manual Input":
        text = st.text_area("Enter text:")
    else:
        uploaded_files = st.file_uploader("Upload PDF", type="pdf", accept_multiple_files=True)
        text = ""
        for uploaded_file in uploaded_files:
            text += process_pdf(uploaded_file)
    return text

def process_pdf(file):
    # Initialize an empty string to store the extracted text
    text = ""

    # Check if the uploaded file is a PDF
    if not isinstance(file, io.BytesIO):
        st.error("Please upload a PDF file.")
        return text

    try:
        # Create a PdfReader object
        pdf_reader = PyPDF2.PdfReader(file)

        # Loop through each page of the PDF
        for page_num in range(len(pdf_reader.pages)):
            # Extract text from the current page
            page_text = pdf_reader.pages[page_num].extract_text()
            # Append the extracted text to the overall text
            text += page_text
    except PyPDF2.utils.PdfReadError:
        st.error("Error reading PDF file. Please upload a valid PDF file.")
    except Exception as e:
        st.error(f"An error occurred: {e}")

    return text


def main():
    st.title("Multiple Choice Questions Quiz")

    st.sidebar.subheader("Choose Input Type")
    option = st.sidebar.radio("", ("Manual Input", "Upload PDF"))

    text = process_input(option)

    num_questions = st.sidebar.slider("Select Number of Questions", min_value=1, max_value=10, value=5)

    if st.sidebar.button("Generate Quiz"):
        mcqs = generate_mcqs(text, num_questions)
        st.session_state['mcqs'] = mcqs
        st.session_state['total_questions'] = len(mcqs)
        st.session_state['answered_questions'] = 0
        st.session_state['correct_answers'] = 0
        st.session_state['current_question'] = 0
        st.session_state['selected_option'] = ""

    if 'mcqs' in st.session_state:
        show_question()

def show_question():
    mcqs = st.session_state.get('mcqs', [])
    total_questions = st.session_state.get('total_questions', 0)
    current_question = st.session_state.get('current_question', 0)

    if mcqs and current_question < total_questions:
        st.subheader(f"Question {current_question + 1}/{total_questions}")
        st.write(mcqs[current_question][0])

        options = mcqs[current_question][1]
        selected_option = st.radio("Select an option:", options, key=f"option_{current_question}")

        st.session_state['selected_option'] = selected_option

        if current_question < total_questions - 1:
            if st.button("Next", key=f"next_{current_question}"):
                evaluate_answer()
        else:
            if st.button("Submit", key="submit_button"):
                evaluate_answer()
    else:
        st.write("No questions available. Please generate the quiz.")

def evaluate_answer():
    mcqs = st.session_state.get('mcqs', [])
    current_question = st.session_state.get('current_question', 0)
    selected_option = st.session_state.get('selected_option', "")

    if mcqs and current_question < len(mcqs):
        correct_answer = mcqs[current_question][2]

        if selected_option == correct_answer:
            st.write("Correct!")
            st.session_state['correct_answers'] += 1

        st.session_state['answered_questions'] += 1
        st.session_state['current_question'] += 1

        if st.session_state['answered_questions'] < st.session_state['total_questions']:
            show_question()
        else:
            show_scoreboard()

def show_scoreboard():
    st.subheader("Quiz Results")
    st.write(f"Total Questions: {st.session_state['total_questions']}")
    st.write(f"Correct Answers: {st.session_state['correct_answers']}")
    st.write(f"Incorrect Answers: {st.session_state['total_questions'] - st.session_state['correct_answers']}")

    if st.button("Restart"):
        st.session_state['mcqs'] = None
        st.session_state['total_questions'] = 0
        st.session_state['answered_questions'] = 0
        st.session_state['correct_answers'] = 0
        st.session_state['current_question'] = 0
        st.session_state['selected_option'] = ""
        main()

if __name__ == "__main__":
    main()