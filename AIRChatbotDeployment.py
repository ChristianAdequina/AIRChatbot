import random
import time
import openai
import streamlit as st

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
        return {
            "question": self.question,
            "answer": self.answer,
            "previous": self.previous.to_dict() if self.previous else None
        }


# NOTE: Placeholder at the moment
sample_anchor_questions = [
    "What motivated you to apply for this role?",
    "Describe a challenging project you've worked on.",
    "How do you handle feedback?",
    "What are your long-term career goals?",
    "What do you consider your biggest professional strength?"
]

# ----- HELPER FUNCTIONS -----
def ask_questions(entity):
    prompt = (f"You are an interviewer, interviewing a first-time applicant. Use the following questions as a guide: "
              f"{sample_anchor_questions}."
              f"Latest exchange:\nQuestion: {entity.question}\nAnswer: {entity.answer}\n\n"
              f"Use the latest exchange provided to either ask a relevant follow-up question that builds on the "
              f"conversation, or continue the interview by asking a thoughtful follow-up question.")

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful interviewer."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=50,
        temperature=0.7
    )

    question = response.choices[0].message['content'].strip()
    return question


def check_tone(response):
    prompt = (f"Please classify this response as either 'Respectful' or 'Disrespectful':"
              f"Response: {response}\n")

    evaluation = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a tone classifier."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1,
        temperature=0
    )

    classification = evaluation.choices[0].message['content'].strip()
    return classification


def save_interview_to_array(entity, interview_data=None):
    if interview_data is None:
        interview_data = []
    interview_data.append(entity.to_dict())
    return interview_data


# ----- STREAMLIT APP -----
def main():
    st.title("Automated Interview System")

    # Load or initialize interview data
    if "interview_data" not in st.session_state:
        st.session_state["interview_data"] = []
        st.session_state["entity_count"] = 0
        st.session_state["start_time"] = time.time()
        st.session_state["closing_phase"] = False

        names = ["Hannah", "Steve", "Carmen", "John", "Stephen", "Lorraine"]
        name = random.choice(names)
        first_question = (f"Good day, my name is {name} and I'll be your interviewer for today. Why don't we start off "
                          f"by telling me about yourself?")

        st.session_state["current_entity"] = QuestionAnswerPair(question=first_question)

    current_entity = st.session_state["current_entity"]

    # Display the current question
    st.write(f"**Interviewer:** {current_entity.question}")

    # Capture the user's answer
    user_answer = st.text_input("Your Answer")

    if st.button("Submit Answer"):
        if user_answer:
            # Check tone
            tone = check_tone(user_answer)
            if tone == "Disrespectful":
                st.write(
                    "**Interviewer:** You are not being professional. I have to terminate this interview. Goodbye.")
                st.json(st.session_state["interview_data"])
                st.stop()

            # Store answer and increment entity count
            current_entity.answer = user_answer
            st.session_state["entity_count"] += 1

            # Link current entity to previous one
            if st.session_state["entity_count"] > 1:
                current_entity.previous = st.session_state["previous_entity"]

            # Save entity to interview data
            st.session_state["interview_data"] = (
                save_interview_to_array(current_entity, st.session_state["interview_data"]))

            # Set the current entity as previous for the next iteration
            st.session_state["previous_entity"] = current_entity

            # Check for closing conditions
            elapsed_time = time.time() - st.session_state["start_time"]
            if elapsed_time > 600 or st.session_state["entity_count"] >= 3:
                st.session_state["closing_phase"] = True

            if st.session_state["closing_phase"]:
                st.write("**Interviewer:** Thank you for your time. This concludes the interview.")
                st.json(st.session_state["interview_data"])
                st.stop()

            # Get next question
            next_question = ask_questions(current_entity)
            st.session_state["current_entity"] = QuestionAnswerPair(question=next_question)
            st.rerun()  # Rerun to update with the new question


if __name__ == "__main__":
    main()
