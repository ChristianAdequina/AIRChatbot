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
        # Convert the QuestionAnswerPair object to a dictionary, including only the immediate previous pair
        return {
            "question": self.question,
            "answer": self.answer,
            "previous": {
                "question": self.previous.question,
                # "answer": self.previous.answer
            } if self.previous else None
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
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful interviewer."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=100,
        temperature=0.5
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
        model="gpt-4o-mini",
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


def trim_question(question):
    # List of inquisitive words
    inquisitive_words = ["What", "Why", "How", "When", "Who", "Where", "Which", "Is", "Are", "Do", "Does", "Can",
                         "Could", "Would", "Should"]

    # Split the question into words
    words = question.split()

    # Find the index of the first inquisitive word preceded by a "." or ","
    for idx, word in enumerate(words):
        # Check if the word is inquisitive and is either preceded by '.' or ',' or is at the start
        if word.strip("?:,.").capitalize() in inquisitive_words:
            # Rejoin the question starting from the inquisitive word
            if idx == 0 or (words[idx - 1].endswith(".") or words[idx - 1].endswith(",")):
                return " ".join(words[idx:])

    # If no inquisitive word is found, return the original question
    return question


def check_comprehensibility(question, response):
    """
    Checks if the user's response is comprehensible in the context of the interview question.
    :param question: The interview question asked by the bot.
    :param response: The user's response to the interview question.
    :return: "Comprehensible" or "Incomprehensible".
    """
    prompt = (f"As an interviewer, evaluate if the following response is comprehensible and relevant to the given "
              f"question."
              f"Mark it as 'Comprehensible' if it is meaningful, logical, and answers the question. Otherwise, "
              f"mark it as"
              f"'Incomprehensible'. Do not add any other explanation.\n\n"
              f"Question: {question}\n"
              f"Response: {response}\n\n"
              f"Result:")

    # Use the OpenAI API to classify the response
    evaluation = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant for evaluating response relevance."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1,
        temperature=0
    )

    # Extract and return the classification
    classification = evaluation.choices[0].message['content'].strip()
    return classification


# ----- INTERVIEW -----
def start_interview(max_follow_ups=2):
    """
    Starts the interview process with configurable follow-up questions per core question.
    :param max_follow_ups: Number of follow-up questions to ask for each core question.
    """
    interview_data = []
    start_time = time.time()  # Time limit clause
    core_question_index = 0  # Track which core question we're on
    follow_up_count = 0  # Track number of follow-ups asked for the current core question

    names = ["Hannah", "Steve", "Carmen", "John", "Stephen", "Lorraine"]
    name = random.choice(names)

    # Start the interview
    print(f"Good day, my name is {name} and I'll be your interviewer for today.")
    print("Why don't we start off by telling me about yourself?")

    # Begin the first entity
    first_entity = QuestionAnswerPair(question="Why don't we start off by telling me about yourself?")
    current_entity = first_entity

    while True:
        # Get user input
        answer = input("\nYour response: ")

        # Check the tone of the response
        tone = check_tone(answer)
        if tone == "Disrespectful":
            print("You are not being professional. The interview is terminated. Goodbye.")
            print(json.dumps(interview_data, indent=4))
            break

        # Check the comprehensibility of the response
        comprehensibility = check_comprehensibility(current_entity.question, answer)
        if comprehensibility == "Incomprehensible":
            print("I'm sorry, I couldn't understand your response. Could you please clarify?")
            continue  # Ask the user to clarify their response without moving forward

        # Save the answer and add the entity to interview_data
        current_entity.answer = answer
        interview_data = save_interview_to_array(current_entity, interview_data)

        if follow_up_count < max_follow_ups:
            # Generate a follow-up question based on the current answer
            follow_up_question = ask_questions(current_entity)
            print(follow_up_question)

            # Create a new entity for the follow-up question
            new_entity = QuestionAnswerPair(question=follow_up_question)
            new_entity.previous = current_entity
            current_entity = new_entity
            follow_up_count += 1  # Increment follow-up count
        else:
            # Reset follow-up count and move to the next core question
            follow_up_count = 0
            core_question_index += 1
            if core_question_index >= len(sample_anchor_questions):
                print("Thank you for your time. This concludes the interview.")
                print(json.dumps(interview_data, indent=4))
                break

            # Ask the next core question
            next_core_question = sample_anchor_questions[core_question_index]
            print(next_core_question)

            # Create a new entity for the next core question
            new_entity = QuestionAnswerPair(question=next_core_question)
            new_entity.previous = current_entity
            current_entity = new_entity

        # Check if the interview exceeds the time or entity count limit
        elapsed_time = time.time() - start_time
        if elapsed_time > 600 or len(interview_data) >= 10:
            print("Thank you for your time. This concludes the interview.")
            print(json.dumps(interview_data, indent=4))
            break


start_interview()
