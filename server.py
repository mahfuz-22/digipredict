from copy import deepcopy
import json
import streamlit as st
from datetime import time, datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore, auth
'''
#
# BUG: Questionnaire due date is on the day after as well as time offset of 12hrs
#
#'''


@st.cache_resource
def initFirebase():
    cred = credentials.Certificate("asthma-adminsdk.json")
    firebase_admin.initialize_app(cred)


def onBoardParticipant(email: str, password: str, userInfo: dict, questionnaireInfo: dict, structure: dict) -> str:
    # Check if user already exists
    try:
        auth.get_user_by_email(email)
        return "User already exists"
    except auth.UserNotFoundError:
        pass
    except ValueError:
        return "Invalid email or password"

    # Create user
    try:
        user = auth.create_user(email=email, password=password)
    except ValueError as e:
        return e

    structure["Basic Info"]["Gender"] = usrInfo["Gender"]
    calendar = deepcopy(structure["Calendar"].pop("date"))
    questionnaireCount = 14
    for date, x in [[(userInfo["start_date"] + timedelta(days=x)), x] for x in range(int(userInfo["time_frame"]))]:
        data = deepcopy(calendar)
        for key in data.keys():
            data[key]["Due time"] = date

        if questionnaireCount >= questionnaireInfo["frequency"]:
            questionnaireCount = 0
            data |= {"Questionnaire": {
                "Completed": False,
                "Due time": date.replace(hour=questionnaireInfo["time"].hour, minute=questionnaireInfo["time"].minute, second=questionnaireInfo["time"].second),
                "Link": questionnaireInfo["link"]
            }}
        else:
            questionnaireCount += 1

        structure["Calendar"] |= {date.strftime("%Y-%m-%d"): deepcopy(data)}

    db = firestore.client()
    for key in structure.keys():
        db.collection(user.uid).document(key).set(structure[key])

    return ""


if __name__ == "__main__":
    # Initialize firebase
    initFirebase()

    st.title("DigiPredict Clinician Onboarding Portal")
    usrInfo = {}
    questionnaireInfo = {}

    with st.form(key="onboarding"):
        st.header("Clinician Onboarding")
        st.info("Please enter your details below")

        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        gender = st.selectbox("Gender", ("Female", "Male"))
        startDate = st.date_input("Start Date")
        morningTaskTime = st.time_input(
            "Morning Task Time", value=time(8, 30, 0), step=60*5)
        timeFrame = st.slider("Time Frame (months)",
                              min_value=1, max_value=12, value=6, step=1)
        questionnaireTime = st.time_input(
            "Questionnaire Time", value=time(18, 30, 0), step=60*5)

        submit_button = st.form_submit_button(label="Submit")
        if submit_button:
            # Check email and password not empty
            if email == "" or password == "":
                st.error("Please enter both email and password")
            else:
                usrInfo = {
                    "Gender": gender,
                    "start_date": datetime.combine(startDate, morningTaskTime),
                    "time_frame": timeFrame * 30,
                }

                questionnaireInfo = {
                    "time": questionnaireTime,
                    "frequency": 14,
                    "link": "https://binarypiano.com/"
                }

                with open("structure.json", "r") as f:
                    structure = json.load(f)

                err = onBoardParticipant(
                    email, password, usrInfo, questionnaireInfo, structure)
                if err != "":
                    st.error(err)
                else:
                    st.success("Participant successfully onboarded!")
