from copy import deepcopy
import json
import streamlit as st
from datetime import time, datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore, auth

def check_auth_and_redirect():
    """Verify authentication before showing page"""
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.error("Please login through the main portal")
        st.stop()
    return True

def onBoardParticipant(email: str, password: str, userInfo: dict, questionnaireInfo: dict, structure: dict) -> str:
    """Your existing onBoardParticipant function"""
    try:
        auth.get_user_by_email(email)
        return "User already exists"
    except auth.UserNotFoundError:
        pass
    except ValueError:
        return "Invalid email or password"

    try:
        user = auth.create_user(email=email, password=password)
    except ValueError as e:
        return e

    structure["Basic Info"]["Gender"] = userInfo["Gender"]
    calendar = deepcopy(structure["Calendar"].pop("date"))
    questionnaireCount = 14
    
    for date, x in [[(userInfo["start_date"] + timedelta(days=x)), x] for x in range(int(userInfo["time_frame"]))]:
        data = deepcopy(calendar)

        if questionnaireCount >= questionnaireInfo["frequency"]:
            questionnaireCount = 1
            data |= {"Questionnaire": {
                "Completed": False,
                "Link": questionnaireInfo["link"]
            }}
        else:
            questionnaireCount += 1

        structure["Calendar"] |= {date.strftime("%Y-%m-%d"): deepcopy(data)}

        for Day in structure["Notifications"]:
            for task in structure["Notifications"][Day]:
                if task == "Questionnaire":
                    structure["Notifications"][Day][task] = datetime.strptime(
                        "2000-01-01 " + questionnaireInfo["time"].strftime("%H:%M:%S"), 
                        "%Y-%m-%d %H:%M:%S"
                    ).astimezone()
                else:
                    structure["Notifications"][Day][task] = datetime.strptime(
                        "2000-01-01 " + userInfo[task+"TaskTime"].strftime("%H:%M:%S"), 
                        "%Y-%m-%d %H:%M:%S"
                    ).astimezone()

    db = firestore.client()
    for key in structure.keys():
        db.collection(user.uid).document(key).set(structure[key])

    return ""

def main():
    if not check_auth_and_redirect():
        return

    st.header("Participant Onboarding")
    st.info("Please enter participant details below")

    usrInfo = {}
    questionnaireInfo = {}

    with st.form(key="onboarding"):
        st.subheader("Basic Information")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        gender = st.selectbox("Sex at Birth", ("Female", "Male"))
        startDate = st.date_input("Start Date")

        st.subheader("Task Timings")
        col1, col2 = st.columns(2)
        with col1:
            checkinTaskTime = st.time_input(
                "Checkin Task Time", value=time(8, 0, 0), step=60*5)
            hailieTaskTime = st.time_input(
                "Hailie Task Time", value=time(8, 0, 0), step=60*5)
        with col2:
            coughMonitorTaskTime = st.time_input(
                "Cough Monitor Task Time", value=time(22, 00, 0), step=60*5)
            questionnaireTime = st.time_input(
                "Questionnaire Time", value=time(20, 00, 0), step=60*5)

        st.subheader("Study Configuration")
        questionnaireLink = st.text_input("Questionnaire Link")
        timeFrame = st.slider("Time Frame (months)",
                          min_value=1, max_value=12, value=7, step=1)

        submit_button = st.form_submit_button(label="Submit")
        if submit_button:
            if not email or not password:
                st.error("Please enter both email and password")
            else:
                usrInfo = {
                    "Gender": gender,
                    "start_date": startDate,
                    "CheckInTaskTime": checkinTaskTime,
                    "HailieTaskTime": hailieTaskTime,
                    "Cough MonitorTaskTime": coughMonitorTaskTime,
                    "time_frame": (timeFrame * 31) - 3,
                }

                questionnaireInfo = {
                    "time": questionnaireTime,
                    "frequency": 14,
                    "link": questionnaireLink
                }

                with open("structure.json", "r") as f:
                    structure = json.load(f)

                err = onBoardParticipant(
                    email, password, usrInfo, questionnaireInfo, structure)
                if err:
                    st.error(err)
                else:
                    st.success("Participant successfully onboarded!")

if __name__ == "__main__":
    st.error("Please access this application through the main portal")
    st.stop()

'''
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

    # # Create user
    try:
        user = auth.create_user(email=email, password=password)
    except ValueError as e:
        return e

    structure["Basic Info"]["Gender"] = usrInfo["Gender"]
    calendar = deepcopy(structure["Calendar"].pop("date"))
    questionnaireCount = 14
    for date, x in [[(userInfo["start_date"] + timedelta(days=x)), x] for x in range(int(userInfo["time_frame"]))]:
        data = deepcopy(calendar)

        if questionnaireCount >= questionnaireInfo["frequency"]:
            questionnaireCount = 1
            data |= {"Questionnaire": {
                "Completed": False,
                "Link": questionnaireInfo["link"]
            }}
        else:
            questionnaireCount += 1

        structure["Calendar"] |= {date.strftime("%Y-%m-%d"): deepcopy(data)}

        for Day in structure["Notifications"]:
            # print(Day)
            for task in structure["Notifications"][Day]:

                if task == "Questionnaire":
                    structure["Notifications"][Day][task] = datetime.strptime(
                        "2000-01-01 " + questionnaireInfo["time"].strftime("%H:%M:%S"), "%Y-%m-%d %H:%M:%S").astimezone()
                else:
                    structure["Notifications"][Day][task] = datetime.strptime(
                        "2000-01-01 " + userInfo[task+"TaskTime"].strftime("%H:%M:%S"), "%Y-%m-%d %H:%M:%S").astimezone()

    db = firestore.client()
    for key in structure.keys():
        db.collection(user.uid).document(key).set(structure[key])

    # print(json.dumps(structure, indent=2))

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

        gender = st.selectbox("Sex at Birth", ("Female", "Male"))
        startDate = st.date_input("Start Date")

        checkinTaskTime = st.time_input(
            "Checkin Task Time", value=time(8, 0, 0), step=60*5)

        hailieTaskTime = st.time_input(
            "Hailie Task Time", value=time(8, 0, 0), step=60*5)

        coughMonitorTaskTime = st.time_input(
            "Cough Monitor Task Time", value=time(22, 00, 0), step=60*5)

        questionnaireTime = st.time_input(
            "Questionnaire Time", value=time(20, 00, 0), step=60*5)

        # questionnaireLink with error checking for web link
        questionnaireLink = st.text_input("Questionnaire Link")

        timeFrame = st.slider("Time Frame (months)",
                              min_value=1, max_value=12, value=7, step=1)

        submit_button = st.form_submit_button(label="Submit")
        if submit_button:
            # Check email and password not empty
            if email == "" or password == "":
                st.error("Please enter both email and password")
            else:
                usrInfo = {
                    "Gender": gender,
                    "start_date": startDate,
                    "CheckInTaskTime": checkinTaskTime,
                    "HailieTaskTime": hailieTaskTime,
                    "Cough MonitorTaskTime": coughMonitorTaskTime,
                    "time_frame": (timeFrame * 31) - 3,
                }

                questionnaireInfo = {
                    "time": questionnaireTime,
                    "frequency": 14,
                    "link": questionnaireLink  # https://binarypiano.com
                }

                with open("structure.json", "r") as f:
                    structure = json.load(f)

                err = onBoardParticipant(
                    email, password, usrInfo, questionnaireInfo, structure)
                if err != "":
                    st.error(err)
                else:
                    st.success("Participant successfully onboarded!")
'''