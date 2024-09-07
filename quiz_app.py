from fasthtml.common import *
import json
import random
import os
from prompt_toolkit import prompt
from prompt_toolkit.completion import FuzzyWordCompleter


app, rt = fast_app()

current_question = 0
score = 0
incorrect_questions = []
shuffled_choices = []


def select_json_file():
    json_files = [f for f in os.listdir() if f.endswith('.json')]
    if not json_files:
        print("No JSON files found in the current directory.")
        return None
    
    completer = FuzzyWordCompleter(json_files)
    selected_file = prompt("Select a JSON file: ", completer=completer)
    
    if selected_file not in json_files:
        print("Invalid selection. Please run the script again.")
        return None
    
    return selected_file


@rt("/")
def get(error: str = ""):
    global current_question, score, incorrect_questions, shuffled_choices
    if current_question >= len(questions):
        # Quiz finished, show score and missed questions
        return Titled("Quiz Complete", 
            H2(f"Your score: {score}/{len(questions)}"),
            *[P(f"Question {q[1]+1}: {questions[q[1]]['question']}",
                Br(),
                f"Your answer: ",
                Span(questions[q[1]]["choices"][q[0]], style="color: red;"),
                Br(),
                f"Correct answer: ",
                Span(questions[q[1]]["choices"][0], style="color: green;"))
              for q in incorrect_questions],
            A("Restart Quiz", href="/restart")
        )
    
    question = questions[current_question]
    shuffled_choices = question["choices"][1:] + [question["choices"][0]]
    random.shuffle(shuffled_choices)
    return Titled("Quiz App",
        H2(question["question"]),
        P("Please select an answer before submitting.", style="color: red;") if error == "no_answer" else "",
        Form(
            *[(Input(type="radio", name="answer", value=str(i), id=f"answer_{i}"),
               Label(choice, fr=f"answer_{i}"),
               Br())
              for i, choice in enumerate(shuffled_choices)],
            Input(type="submit", value="Next"),
            action="/submit",
            method="post"
        )
    )


@rt("/submit")
async def post(req):
    global current_question, score, incorrect_questions, shuffled_choices
    try:
        form_data = await req.form()
        answer = form_data.get("answer")
    except:
        # If form parsing fails, treat it as no answer selected
        return RedirectResponse("/?error=no_answer", status_code=303)
    
    if answer is None:
        # No answer selected, return to the same question with an error message
        return RedirectResponse("/?error=no_answer", status_code=303)
    
    answer = int(answer)
    
    if shuffled_choices[answer] == questions[current_question]["choices"][0]:
        score += 1
    else:
        incorrect_questions.append((answer, current_question))
    
    current_question += 1
    return RedirectResponse("/", status_code=303)


@rt("/restart", methods=["GET", "POST"])
async def restart(req):
    global current_question, score, incorrect_questions
    current_question = 0
    score = 0
    incorrect_questions = []
    return RedirectResponse("/", status_code=303)


if __name__ == "__main__":
    selected_file = select_json_file()
    if selected_file:
        with open(selected_file, "r") as f:
            questions = json.load(f)
            questions = questions["questions"]
        
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        print("Exiting the application.")