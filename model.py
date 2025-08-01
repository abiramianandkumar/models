import os
from datetime import datetime
import streamlit as st
from pymongo import MongoClient
from langchain_huggingface import HuggingFaceEndpoint
from langchain.prompts import ChatPromptTemplate


MONGO_URI = "mongodb://localhost:27017"  
client = MongoClient(MONGO_URI)
db = client["ehr_database"]
collection = db["patients"]


#os.environ['HUGGINGFACEHUB_API_TOKEN'] = "hf_your_actual_token_here"

def query_llm(question):
    """Query the LLM for medical advice."""
    try:
        llm = HuggingFaceEndpoint(
            model="mistralai/Mistral-7B-Instruct-v0.3",  
            temperature=0.7,
            max_new_tokens=500
        )
        prompt = ChatPromptTemplate.from_template("""
        You are a knowledgeable medical assistant integrated into an EHR system.
        Based on the following query, provide accurate, professional, and concise advice.
        
        Query: {input}
        """)
        full_prompt = prompt.format(input=question)
        response = llm.invoke(full_prompt)
        return response.strip() if response else "No response from the LLM."
    except Exception as e:
        return f"An error occurred: {e}"

# Streamlit app
def handle_medical_card():
    st.title("EHR System with LLM Integration")

    card_number = st.text_input("Enter the medical card number:")

    if card_number:
        patient = collection.find_one({"card_number": card_number})

        if patient:
            st.subheader("Patient Details")
            st.write(f"**Name:** {patient['name']}")
            st.write(f"**Age:** {patient['age']}")

            action = st.radio("Select an action:", ("Input Visit Details", "Retrieve Visit Details", "Ask Medical Question"))

            if action == "Input Visit Details":
                visit_details = st.text_input("Enter the visit details in a single sentence:")
                if visit_details:
                    parsed_details = {
                        "disease": "Unknown Disease",
                        "symptoms": ["Symptom1", "Symptom2"],
                        "medicine": "Medicine Name",
                        "dosage": "2 tablets",
                        "duration": "5 days",
                        "date": datetime.now().strftime("%Y-%m-%d")
                    }
                    collection.update_one(
                        {"card_number": card_number},
                        {"$push": {"visits": parsed_details}},
                        upsert=True
                    )
                    st.success("Visit details added successfully.")

            elif action == "Retrieve Visit Details":
                date = st.date_input("Select a date:", datetime.now())
                visit = next(
                    (v for v in patient.get('visits', []) if v.get('date') == date.strftime("%Y-%m-%d")),
                    None
                )
                if visit:
                    st.subheader(f"Visit Details for {date.strftime('%Y-%m-%d')}")
                    st.write(f"**Disease:** {visit.get('disease', 'Not specified')}")
                    st.write(f"**Symptoms:** {', '.join(visit.get('symptoms', ['Not specified']))}")
                    st.write(f"**Medicine:** {visit.get('medicine', 'Not specified')}")
                    st.write(f"**Dosage:** {visit.get('dosage', 'Not specified')}")
                    st.write(f"**Duration:** {visit.get('duration', 'Not specified')}")
                else:
                    st.warning("No visit details found for the selected date.")

            elif action == "Ask Medical Question":
                user_query = st.text_input("Type your medical question:")
                if user_query:
                    st.write("Processing your query...")
                    llm_response = query_llm(user_query)
                    st.write("Response from Medical Assistant:")
                    st.write(llm_response)

        else:
            st.warning("No medical card found for the entered number.")
            if st.button("Create New Medical Card"):
                name = st.text_input("Enter the patient's name:")
                age = st.number_input("Enter the patient's age:", min_value=0, step=1)
                save_button = st.button("Save")
                if save_button:
                    if name and age > 0:
                        new_patient = {
                            "card_number": card_number,
                            "name": name,
                            "age": age,
                            "visits": []
                        }
                        collection.insert_one(new_patient)
                        st.success("Medical card created successfully.")
                    else:
                        st.error("Please provide all required details.")

# Run the Streamlit app
if __name__ == "__main__":
    handle_medical_card()
