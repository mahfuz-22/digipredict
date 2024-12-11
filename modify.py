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

def checkClientEnrolled(email:str) -> bool:
    """Check if client exists"""
    try:
        auth.get_user_by_email(email)
    except auth.UserNotFoundError:
        return False
    return True

def removeStudyDates(email:str, startDate: datetime.date, endDate: datetime.date) -> bool:
    """Remove study dates for a participant"""
    user = auth.get_user_by_email(email)
    dates = [startDate + timedelta(days=i) for i in range((endDate - startDate).days + 1)]
    db = firestore.client()
    calendar_ref = db.collection(user.uid).document("Calendar")
    for date in dates:
        calendar_ref.update({date.strftime("%Y-%m-%d") : firestore.DELETE_FIELD})
    return True

def extendStudyDates(email:str, startDate: datetime.date, endDate: datetime.date, 
                     questionniare_day:int, questionnaire_link:str) -> bool:
    """Extend study dates for a participant"""
    user = auth.get_user_by_email(email)
    dates = [startDate + timedelta(days=i) for i in range((endDate - startDate).days + 1)]
    db = firestore.client()
    calendar_ref = db.collection(user.uid).document("Calendar")
    qdate = 0
    
    for date in dates:
        tasks = {
            "Hailie": {"Completed": False},
            "Cough Monitor": {"Completed": False},
            "CheckIn": {"Completed": False}
        }

        if date.weekday() == questionniare_day:
            if not qdate < 1:
                tasks |= {"Questionnaire": {
                    "Completed": False,
                    "Link": questionnaire_link
                }}
                qdate = 0
            else:
                qdate += 1

        calendar_ref.update({date.strftime("%Y-%m-%d"): tasks})

    return True

def main():
    if not check_auth_and_redirect():
        return

    st.header("Modify Participant Data")
    st.info("Please enter the participant details below")

    email = st.text_input("Study Email")
    
    col1, col2 = st.columns(2)
    
    with col1:
        pauseStudy = st.toggle("Remove Dates from Study")
        if pauseStudy:
            startPauseDate = st.date_input("Start Removal Date", key="srd")
            endPauseDate = st.date_input("End Removal Date", key="erd")
            if endPauseDate < startPauseDate:
                st.error("End date should be after start date")
    
    with col2:
        extendStudy = st.toggle("Extend Study")
        if extendStudy:
            startExtendDate = st.date_input("Start Extension Date", key="sed")
            endExtendDate = st.date_input("End Extension Date", key="eed")
            if endExtendDate < startExtendDate:
                st.error("End date should be after start date")
            
            questionnaireLink = st.text_input("Questionnaire Link")
            questionnaireDay = st.select_slider(
                "Select Questionnaire Day", 
                options=['Monday', "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            )
            datemap = {
                "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
                "Friday": 4, "Saturday": 5, "Sunday": 6
            }
            questionnaireDay = datemap[questionnaireDay]

    if st.button(label="Submit"):
        if not email:
            st.error("Please enter email")
            return

        if not checkClientEnrolled(email):
            st.error("User doesn't exist")
            return

        if pauseStudy:
            res = removeStudyDates(email, startPauseDate, endPauseDate)
            if res:
                st.success(f"Participant Dates Removed between {startPauseDate} to {endPauseDate}")
            else:
                st.error("Error occurred while removing dates")

        if extendStudy:
            res = extendStudyDates(email, startExtendDate, endExtendDate, 
                                 questionnaireDay, questionnaireLink)
            if res:
                st.success("Successfully Extended Study Dates")
            else:
                st.error("Error occurred while extending dates")

if __name__ == "__main__":
    st.error("Please access this application through the main portal")
    st.stop()

'''
@st.cache_resource
def initFirebase():
    cred = credentials.Certificate("asthma-adminsdk.json")
    firebase_admin.initialize_app(cred)


def checkClientEnrolled(email:str) -> bool:
    try:
        auth.get_user_by_email(email)
    except auth.UserNotFoundError:
        return False
    
    return True

def removeStudyDates(email:str, startDate: datetime.date, endDate: datetime.date) -> bool:
    user = auth.get_user_by_email(email)
    # Generate the dates to remove
    dates = [startDate + timedelta(days=i) for i in range((endDate - startDate).days + 1)]
    db = firestore.client()
    calendar_ref = db.collection(user.uid).document("Calendar")
    for date in dates:
        calendar_ref.update({date.strftime("%Y-%m-%d") : firestore.DELETE_FIELD})
    return True

def extendStudyDates(email:str, startDate: datetime.date, endDate: datetime.date, questionniare_day:int, questionnaire_link:str) -> bool:
    user = auth.get_user_by_email(email)
    dates = [startDate + timedelta(days=i) for i in range((endDate - startDate).days + 1)]

    # Create upload structure for firebase
    db = firestore.client()
    calendar_ref = db.collection(user.uid).document("Calendar")
    qdate = 0
    for date in dates:

        tasks = {
            "Hailie": {
                    "Completed": False
            },
            "Cough Monitor": {
                "Completed": False
            },
            "CheckIn": {
                "Completed": False
            }
        }

        # For questionnaire so that it is every two weeks
        if date.weekday() == questionniare_day:
            if not qdate < 1:
                tasks |= {"Questionnaire" : {"Completed" : False, "Link" : questionnaire_link}}
                qdate = 0
            else:
                qdate += 1

        calendar_ref.update({date.strftime("%Y-%m-%d") : tasks})

    return True




# check if user exists

# if so, modify pause dates

# modify extend dates

if __name__ == "__main__":
    initFirebase()
    st.title("DigiPredict Clinician Modifying Portal")

    # with st.form(key="onboarding"):
    st.header("Clinician Onboarding")
    st.info("Please enter the participants details below")

    email = st.text_input("Study Email")
    
    # Checkbox to pause study
    pauseStudy = st.toggle("Remove Dates from Study")
    
    if pauseStudy:
        # Select dates to pause study
        startPauseDate = st.date_input("Start Removal Date", key="srd")
        endPauseDate = st.date_input("End Removal Date", key="erd")
        
        # Ensure end date is after start date
        if endPauseDate < startPauseDate:
            st.error("End date should be after start date")

    # Checkbox to extend study
    extendStudy = st.toggle("Extend Study")

    if extendStudy:
        startExtendDate = st.date_input("Start Pause Date", key="sed")
        endExtendDate = st.date_input("End Pause Date", key = "eed")

        # Ensure end date is after start date
        if endExtendDate < startExtendDate:
            st.error("End date should be after start date")
        
        # questionnaireLink with error checking for web link
        questionnaireLink = st.text_input("Questionnaire Link")
        questionnaireDay = st.select_slider("Select Questionnaire Day", options=['Monday', "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        datemap = {
            "Monday" : 0,
            "Tuesday" : 1,
            "Wednesday" : 2,
            "Thursday" : 3,
            "Friday" : 4,
            "Saturday" : 5,
            "Sunday" : 6

        }
        questionnaireDay = datemap[questionnaireDay]

    submit_button = st.button(label="Submit")

    if submit_button:
        # Check email and password not empty
        if email == "":
            st.error("Please enter both email")

        # Check if user exists
        if not checkClientEnrolled(email):
            st.error("User doesn't exit...")

        if pauseStudy:
            res = removeStudyDates(email, startPauseDate, endPauseDate)
            if res:

                st.success(f"Participant Dates Removed between {startPauseDate} to {endPauseDate}") 
            else:
                st.error("Error something went wrong...")

        if extendStudy:
            res = extendStudyDates(email, startExtendDate, endExtendDate, questionnaireDay,questionnaireLink)
            if res:
                st.success("Successfully Extended")
            else:
                st.error("Something went wrong")
            

# predictasthma+999@gmail.com
# Cough999!
'''