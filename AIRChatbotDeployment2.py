import openai
import streamlit as st
import random
import json
import time

# Streamlit App Title
st.title("AIRS Interview Chatbot")

openai.api_key = st.secrets["OPENAI_API_KEY"]

# Initialize session state for chat history and interview data
if "messages" not in st.session_state:
    st.session_state.messages = []

if "interview_data" not in st.session_state:
    st.session_state.interview_data = []

if "core_question_index" not in st.session_state:
    st.session_state.core_question_index = 0

if "follow_up_count" not in st.session_state:
    st.session_state.follow_up_count = 0

if "current_entity" not in st.session_state:
    st.session_state.current_entity = None

# Sample core questions for the interview
sample_anchor_questions = [
    "What motivated you to apply for this role?",
    "Describe a challenging project you've worked on.",
    "How do you handle feedback?",
    "What are your long-term career goals?",
    "What do you consider your biggest professional strength?"
]


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
            "previous": {
                "question": self.previous.question,
            } if self.previous else None
        }


# ----- HELPER FUNCTIONS -----
def ask_questions(entity):
    prompt = (f"You are an interviewer, interviewing a first-time applicant. Use the following questions as a guide: "
              f"{sample_anchor_questions}."
              f"Latest exchange:\nQuestion: {entity.question}\nAnswer: {entity.answer}\n\n"
              f"Use the latest exchange provided to either ask a relevant follow-up question that builds on the "
              f"conversation, or continue the interview with a thoughtful question. Keep it conversational.")

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful interviewer."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=100,
        temperature=0.5
    )

    return response.choices[0].message['content'].strip()


def check_tone(response):
    prompt = (f"Classify this response as 'Respectful' or 'Disrespectful':"
              f"Response: {response}\n")

    evaluation = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a tone classifier."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1,
        temperature=0
    )

    return evaluation.choices[0].message['content'].strip()


def check_comprehensibility(question, response):
    prompt = (f"Evaluate if the response is comprehensible and relevant to the given question."
              f"Mark it as 'Comprehensible' or 'Incomprehensible'."
              f"\nQuestion: {question}\nResponse: {response}\n")

    evaluation = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a response evaluator."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1,
        temperature=0
    )

    return evaluation.choices[0].message['content'].strip()


def save_interview_to_array(entity):
    st.session_state.interview_data.append(entity.to_dict())


# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ----- INTERVIEW FLOW -----
names = ["Hannah", "Steve", "Carmen", "John", "Stephen", "Lorraine"]
if "name" not in st.session_state:
    st.session_state.name = random.choice(names)

if st.session_state.current_entity is None:
    st.session_state.current_entity = QuestionAnswerPair("Why don't we start off by telling me about yourself?")
    # st.chat_message("assistant").markdown(
    #     f"Good day, my name is {st.session_state.name}, and I'll be your interviewer for today. "
    #     "Why don't we start off by telling me about yourself?"
    # )
    bot_intro = (f"Good day, my name is {st.session_state.name}, and I'll be your interviewer for today. "
                 "Why don't we start off by telling me about yourself?")
    st.session_state.messages.append({"role": "assistant", "content": bot_intro})
    with st.chat_message("assistant"):
        st.markdown(bot_intro)

# Get user input
user_input = st.chat_input("Your response:")
if user_input:
    # Display user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Tone Check
    tone = check_tone(user_input)
    if tone == "Disrespectful":
        bot_response = "You are not being professional. The interview is terminated. Goodbye."
        st.session_state.messages.append({"role": "assistant", "content": bot_response})
        with st.chat_message("assistant"):
            st.markdown(bot_response)
        st.write(json.dumps(st.session_state.interview_data, indent=4))
        st.stop()

    # Comprehensibility Check
    comprehensibility = check_comprehensibility(st.session_state.current_entity.question, user_input)
    if comprehensibility == "Incomprehensible":
        bot_response = "I'm sorry, I couldn't understand your response. Could you please clarify?"
        st.session_state.messages.append({"role": "assistant", "content": bot_response})
        with st.chat_message("assistant"):
            st.markdown(bot_response)
    else:
        # Save the user's response
        st.session_state.current_entity.answer = user_input
        save_interview_to_array(st.session_state.current_entity)

        # Follow-up or next core question
        if st.session_state.follow_up_count < 2:
            follow_up_question = ask_questions(st.session_state.current_entity)
            st.session_state.messages.append({"role": "assistant", "content": follow_up_question})
            with st.chat_message("assistant"):
                st.markdown(follow_up_question)

            # Update entity and follow-up count
            new_entity = QuestionAnswerPair(question=follow_up_question)
            new_entity.previous = st.session_state.current_entity
            st.session_state.current_entity = new_entity
            st.session_state.follow_up_count += 1
        else:
            st.session_state.follow_up_count = 0
            st.session_state.core_question_index += 1

            if st.session_state.core_question_index >= len(sample_anchor_questions):
                bot_response = "Thank you for your time. This concludes the interview."
                st.session_state.messages.append({"role": "assistant", "content": bot_response})
                with st.chat_message("assistant"):
                    st.markdown(bot_response)
                st.write(json.dumps(st.session_state.interview_data, indent=4))
                st.stop()
            else:
                next_core_question = sample_anchor_questions[st.session_state.core_question_index]
                st.session_state.messages.append({"role": "assistant", "content": next_core_question})
                with st.chat_message("assistant"):
                    st.markdown(next_core_question)

                # Update entity for the next core question
                new_entity = QuestionAnswerPair(question=next_core_question)
                new_entity.previous = st.session_state.current_entity
                st.session_state.current_entity = new_entity

# import openai
# import streamlit as st
#
# st.title("AIRS Chatbot")
#
# openai.api_key = st.secrets["OPENAI_API_KEY"]
# # Initialize Chat history
#
# if "openai_model" not in st.session_state:
#     st.session_state["openai_model"] = "gpt-4o-mini"
#
# if "messages" not in st.session_state:
#     st.session_state.messages = []
#
# # Display chat messages from history on app rerun
# for message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         st.markdown(message["content"])
#
# # React to User input
# prompt = st.chat_input("What is up?")
# if prompt:
#     # Display user message in chat message container
#     with st.chat_message("user"):
#         st.markdown(prompt)
#     # Add user message to chat history
#     st.session_state.messages.append({"role": "user", "content": prompt})
#
#     with st.chat_message("assistant"):
#         message_placeholder = st.empty()
#         full_response = ""
#         for response in openai.ChatCompletion.create(
#             model=st.session_state["openai_model"],
#             messages=[
#                 {"role": m["role"], "content": m["content"]}
#                 for m in st.session_state.messages
#             ],
#             stream=True,
#         ):
#             full_response += response.choices[0].delta.get("content", "")
#             message_placeholder.markdown(full_response + "| ")
#         message_placeholder.markdown(full_response)
#     st.session_state.messages.append({"role": "assistant", "content": full_response})
