import datetime
import streamlit as st
from get_results import *
import requests
import pandas as pd


if 'start_point' not in st.session_state:
    st.session_state['start_point'] = 0

@st.cache_data(show_spinner=False)
def upload_audio(file):
    return upload_to_AssemblyAI(file)

@st.cache_data(show_spinner=False)
def poll_endpoint(endpoint):
    status = 'submitted'
    while status != "completed":
        polling_response = requests.get(endpoint, headers=headers)
        status = polling_response.json()['status']
    return polling_response.json()

def update_start(start_t):
    st.session_state['start_point'] = int(start_t/1000)
    return None

st.title("Event Summarizer")
uploaded_file = st.file_uploader('Upload audio to get MOM')
start = datetime.datetime.now()
print("Start Time: ",start)


if uploaded_file is not None:
    st.audio(uploaded_file, start_time=st.session_state['start_point'])
    polling_response = poll_endpoint(upload_audio(uploaded_file))
    
    st.text("")                    
    st.subheader("Main themes")
    with st.expander("Themes"):
        categories = polling_response['iab_categories_result']['summary']
        for cat in categories:
            st.markdown("* " + cat)
        
    st.text("")   
    st.subheader("Summary notes of this meeting")
    chapters = polling_response['chapters']
    chapters_df = pd.DataFrame(chapters)
    chapters_df['start_str'] = chapters_df['start'].apply(convertMillis)
    chapters_df['end_str'] = chapters_df['end'].apply(convertMillis)
    
    for idex,row in chapters_df.iterrows():
        with st.expander(row['gist']):
            st.write(row['summary'])
            st.button(row['start_str'], on_click=update_start, args=(row['start'],))
    
    spk_count = polling_response['speakers_expected']
    utterences = polling_response['utterances']
    utterences_df = pd.DataFrame(utterences)
    
    df_speakers = {}
    
    st.text("")   
    st.subheader("Speakers")
    for idex,row in utterences_df.iterrows():
        if row['speaker'] in df_speakers:
            df_speakers[row['speaker']].append({
                'text':row['text'],
                'start_o':row['start'],
                'start':convertMillis(row['start']),
                'end':convertMillis(row['end'])
                })
        else:
            df_speakers[row['speaker']] = [{
                'text':row['text'],
                'start_o':row['start'],
                'start':convertMillis(row['start']),
                'end':convertMillis(row['end'])
                }]
    
    for key,value in df_speakers.items():
        with st.expander("Speaker- "+key):
            c = 1
            for utter in value:
                st.markdown(str(c)+'. '+utter['text'])
                st.button(utter['start'], key=key+str(c), on_click=update_start, args=(utter['start_o'],))
                st.text("")
                c += 1
    end = datetime.datetime.now()
    diff = end - start
    print("Time taken:", diff.total_seconds() / 60,'mins')