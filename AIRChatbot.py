import random
import time
import json

import openai

openai.api_key = ("sk-proj"
                  "-Qj7wpmQ4zLeHkxtsF_XDQRQD8HCIEozyOJR2FtAPQDqPoetAp9NR0GlBPIzKrN_bic7h7AimBRT3BlbkFJ2FRaW3pH2IUtFY"
                  "-hl4o1TbdZzVs7MjyWmjKrTqHqeMZRI8-f9xEP8TvUQVGKBVKR5gknlWvRUA")


# ----- CLASS DEFINITION -----
class QuestionAnswerPair:
    def __init__(self, question, answer=None):
        self.question = question
        self.answer = answer
        self.previous = None  # Link to the previous question/answer pair as context

    def to_dict(self):
        # Convert the QuestionAnswerPair object to a dictionary
        return {
            "question": self.question,
            "answer": self.answer,
            "previous": self.previous.to_dict() if self.previous else None
        }


# --------------------

# NOTE: Placeholder at the moment
sample_anchor_questions = [
    "What motivated you to apply for this role?",
    "Describe a challenging project you've worked on.",
    "How do you handle feedback?",
    "What are your long-term career goals?",
    "What do you consider your biggest professional strength?"
]


# --------------------

# ----- HELPER FUNCTIONS DEFINITIONS -----
def ask_questions(entity):
    # Use the last question/answer pair as the context
    prompt = (f"You are an interviewer, interviewing a first-time applicant. Use the following questions as a guide: "
              f"{sample_anchor_questions}."
              f"Latest exchange:\nQuestion: {entity.question}\nAnswer: {entity.answer}\n\n"
              f"Use the latest exchange provided to either ask a relevant follow-up question that builds on the "
              f"conversation, or continue the interview by asking a thoughtful follow-up question."
              f"When asking questions try to make it sound as conversational as possible.")

    # Generate the next question
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # or 'gpt-4' if you have access
        messages=[
            {"role": "system", "content": "You are a helpful interviewer."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=50,
        temperature=0.7
    )

    # Extract and return the model's response
    question = response.choices[0].message['content'].strip()
    return question


def check_tone(response):
    prompt = (f"Please classify this response as either 'Respectful' or 'Disrespectful':"
              f"Response: {response}\n"
              f"Being disrespectful is classified in this case as either being blatantly rude,"
              f"attacking the interviewer in any way, or being mocking in their answer. "
              f"Don't add anything else in your response. Just the words 'Respectful' or 'Disrespectful'"
              )

    evaluation = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a tone classifier."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1,
        temperature=0
    )

    # Extract and return the classification
    classification = evaluation.choices[0].message['content'].strip()
    return classification


def save_interview_to_array(entity, interview_data=None):
    # Convert the entity into a dictionary and add it to the list
    if interview_data is None:
        interview_data = []
    interview_data.append(entity.to_dict())
    return interview_data


# ----- INTERVIEW -----
def start_interview():
    interview_data = []

    # Time limit clause
    start_time = time.time()
    # Entity-maxing clause
    entity_count = 0
    closing_phase = False

    names = ["Hannah", "Steve", "Carmen", "John", "Stephen", "Lorraine"]
    name = random.choice(names)

    # Initialize the interview
    first_entity = QuestionAnswerPair(question=f"Good day, my name is {name} and I'll be your interviewer for today. "
                                               f"Why don't we start off by telling me about yourself?")

    current_entity = first_entity
    print(current_entity.question)

    while True:
        answer = input('\n\n')

        # Check the tone, if the user is disrespectful in any way, force terminate.
        tone = check_tone(answer)
        if tone == "Dis":
            print("You are not being professional right now. You leave me with no choice but to terminate this "
                  "interview. Goodbye.")
            print(json.dumps(interview_data, indent=4))
            break

        # Store the user response as the answer for that question
        current_entity.answer = answer
        entity_count += 1

        # Save entity to the list
        interview_data = save_interview_to_array(current_entity, interview_data)

        if entity_count == 0:
            current_entity.previous = first_entity

        # Check time limit and entity limit
        elapsed_time = time.time() - start_time
        if elapsed_time > 600 or entity_count >= 3:
            closing_phase = True

        if closing_phase:
            # NOTE: Closing phase is temporary. This will soon become the "questions from applicant" process,
            # but will need the company profiles so the model can accurately answer the questions regarding the company.
            print("Thank you for your time. This concludes the interview.")
            print(json.dumps(interview_data, indent=4))
            break

        # Ask the next question
        next_question = ask_questions(current_entity)

        # NOTE: Not sure if this is needed right now, but is good to use as a backup terminating clause.
        # if not next_question:
        #     print("Thank you for completing the interview!")
        #     break

        # Display the next question and create a new entity
        print(next_question)
        new_entity = QuestionAnswerPair(question=next_question)
        new_entity.previous = current_entity
        current_entity = new_entity


start_interview()
