import streamlit as st
import os
from PIL import Image
from streamlit_modal import Modal
from supabase import create_client, Client
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except KeyError as e:
    st.error(f"Supabase secret not found: {e}. Please ensure you have configured .streamlit/secrets.toml correctly.")
    st.stop()



st.set_page_config(
    page_title="Single-File Multi-Page App",
    page_icon="📄",
    layout="wide")
def home_page():
    """Displays the home page content."""
    st.title("Ticket Runbook")
    st.write("Priority Pages")
    st.markdown(
        """
        Page 1: Priority 1 Tickets Directions
        """)
    st.markdown(
        """
        Page 2: Priority 2 Tickets Directions
        """)
    st.markdown(
        """
        Page 3: Priority 3 Tickets Directions
        """)
    st.markdown(
        """
        Page 4: Priority 4 Tickets Directions
        """)

def Priority_1_Tickets():
    st.title("P1 Runbook")
    st.write("---")
    st.write("I. In ConnectWise, click on the ticket")

    img_path = "Screenshot 2025-05-13 130224.png"
    if not os.path.exists(img_path):
        st.error(f"Error: Image file not found at '{img_path}'. Please check the path.")
        return
    try:
        img = Image.open(img_path)
    except Exception as e:
        st.error(f"Error loading image: {e}")
        return
    modal = Modal(key="CW Screenshot", title="Connectwise Company Box Screenshot")
    st.image(img, width=300)
    if st.button("Then Click Here"):
        modal.open()
    if modal.is_open():
        with modal.container():
            st.header("Connectwise Company Box - Detailed View")
            st.image(img, use_container_width=True)
            st.markdown("""
            **Site Directions:**
            1. Check the Site Field in the Company: DXC-HP box in ConnectWise
                1. If the Field: Site has a 3 Letter Code, Look in the description and validate that code.
                2. If the Field: Site says Additional Site, then find the Sites Continued section in the Initial Description box and change the Field: Site to that code.
            """)
    st.write("---")
    st.write("II: Identify the Service Window")
    st.markdown("""
                ** Steps: **
                1. Look at the Start Date of Request and Start Time of Request in the ConnectWise Ticket
                2. Look at End Date of Request and End Time of Request in the ConnectWise Ticket
                    1. **If these are the same day, then this is a hard start arrival, this means that the technician must be available to be on site at this start time.**
                    2. **If these are on different days, then this is a schedulable window, schedule the service window during normal business hours unless specified otherwise.**
                """)
    st.write("III. Identify a Technician for the Site:")
    site_code_input = st.text_input(
        "Enter 3-Letter Site Code:",
        max_chars=3,
        help="e.g., 'ABC', 'XYZ'. This will filter technicians by site.").upper().strip()
    if site_code_input:
        st.write(f"Searching for technicians for site: **{site_code_input}**")
        try:
            tech_info_response = supabase.from_('TECH INFORMATION').select("*").eq('SITE', site_code_input).execute()
            tech_info_data = tech_info_response.data
            names_and_sites_response = supabase.from_('names_and_sites').select("*").execute()
            names_and_sites_data = names_and_sites_response.data
            if tech_info_data and names_and_sites_data:
                import pandas as pd
                df_tech_info = pd.DataFrame(tech_info_data)
                df_names_and_sites = pd.DataFrame(names_and_sites_data)
                df_tech_info['Full Name'] = df_tech_info['FIRST NAME'].fillna('') + ' ' + df_tech_info['LAST NAME'].fillna('')
                df_tech_info['Full Name'] = df_tech_info['Full Name'].str.strip()
                df_names_and_sites_badged = df_names_and_sites[df_names_and_sites['Badge'] == 'YES']
                merged_df = pd.merge(
                    df_tech_info,
                    df_names_and_sites_badged,
                    left_on='Full Name',
                    right_on='Name',
                    how='inner')
                if not merged_df.empty:
                    original_tech_info_columns = [col for col in df_tech_info.columns if col not in ['Full Name']]
                    st.dataframe(merged_df[original_tech_info_columns])
                else:
                    st.info(f"No matching technicians with a 'YES' badge found for site code: **{site_code_input}**")
            elif tech_info_data and not names_and_sites_data:
                st.info("No data found in 'names_and_sites' to cross-reference technicians.")
            elif not tech_info_data and names_and_sites_data:
                st.info(f"No technician information found for site code: **{site_code_input}**")
            else:
                st.info(f"No technician information or badge information found for site code: **{site_code_input}**")
        except Exception as e:
            st.error(f"An error occurred while fetching data from Supabase: {e}")
            st.warning("Please ensure your Supabase URL, Anon Key, and table/column names are correct.")
    else:
        st.info("Please enter a 3-letter site code to search for technicians.")
    st.write("---")
    st.write("IV. Contact the Technician")
    st.markdown("""
                ** Steps: **
                1. Call the Technician
                    1. If the Technician answers and accepts the work order, **tell the technician you will be routing them a work order on field nation**, then move on to section V
                    2. If the Technician declines, then move onto step 2
                    3. If the Technician does not answer, send this text: "Hi TECHNICIAN_NAME, this is YOUR_NAME with Suryl. We have a work order at the SITE_LOCATION for DATE_OF_SERVICE. Are you available to take this work order"
                    4. Then move to step 2
                2. Call the next technician on the list
                    1. If the Technician answers and accepts the work order, **tell the technician you will be routing them a work order on field nation**, then move on to section V
                    2. If the Technician declines, then move onto step 3
                    3. If the Technician does not answer, send this text: "Hi TECHNICIAN_NAME, this is YOUR_NAME with Suryl. We have a work order at the SITE_LOCATION for DATE_OF_SERVICE. Are you available to take this work order"
                    4. Then move to step 3
                3. Call the next technician on the list
                    1. If the Technician answers and accepts the work order, **tell the technician you will be routing them a work order on field nation**, then move on to section V
                    2. If the Technician declines, then move onto step 4
                    3. If the Technician does not answer, send this text: "Hi TECHNICIAN_NAME, this is YOUR_NAME with Suryl. We have a work order at the SITE_LOCATION for DATE_OF_SERVICE. Are you available to take this work order"
                    4. Then move to step 4                
                4. If no Technician has answered the phone or responded by text, then wait 15 minutes
                    1. **If no response after 15 minutes, Escalate to Callaway Crenshaw: 405-403-9513**
                """)
    st.write("---")
    st.write("V. Assigning the Work Order in Field Nation")
    st.markdown("""
                1. In Connectwise:
                    1. Change the ticket status to Dispatched
                    2. Once that status has been changed, save and refresh the ticket
                    3. Keep refreshing until you see a WO# created in the Additional Details section in ConnectWise
                    4. Once the WO# is created in ConnectWise, move the ticket status to Work Order Created and save the ticket
                2. Login to field nation using your credentials
                    1. Here is the Link: https://app.fieldnation.com/workorders
                3. Click on the Work tab at the top of the screen and then click Flightboard
                4. Navigate to the Draft tab on the flightboard
                5. Here you should see the work order as a draft, find the corresponding ID on the Draft page with the ConnectWise WO# and click on the corresponding title
                6. Once in the work order, there are a few things that need to be checked
                    1. Click on the Schedule box inside the work order
                        1. Change Schedule Type to (Hard Start)
                        2. Change the Date and Time to the agreed upon Date/Time and hit Save
                7. Once the work order has been validated, go to the Providors tab inside the work order
                    1. Select Find Providors tab
                    2. Copy and paste the corresponding Field Nation ID from step 3 for the Identified Technician into the find providor search bar and hit enter
                    3. Validate that this is the correct name of the Identified Technician
                    4. Then slect the route button that is purple
                8. Once the work order is routed in FieldNation, go into the ticket in ConnectWise and add a new note in Discussion
                    1. Fill out this form with the Technicians Name, Email, and ETA
                        1. Name: TECHNICIAN NAME, Mail: TECHNICIAN EMAIL, ETA: DATE/TIME
                """)
    st.write("---")
    st.write("VI. Work Order Specifics")
    st.markdown("""
                1. When the status shows Enroute in ConnectWise, go into Microsoft Teams, Create a Site Chat Labeled "SITE_CODE SUPPORT"
                2. Add the Technician using their Suryl email. Then add carolina.leon@dxc.com, k.perezsilva2@dxc.com, and erick.sanchez@dxc.com
                3. Then send this message in the chat: "Hi Team, TECHNICIAN NAME is on their way to the site."
                4. Text the Technician and tell them that you are adding them to a microsoft teams chat that will be where they will send updates and communicate with the team. Remind them that this is used by logging into their Suryl email and accessing the microsoft teams app
                5. If there is a Microsoft teams meeting link in the Initial Description in ConnectWise or in the Discussion notes in ConnectWise, send that in the chat saying "@TECHNICIAN NAME, Here is the Teams Meeting Link for the work order"
                6. If they ask where the device is, there will be notes on the device location in the ConnectWise Initial Description, if there is no description, then ask the DXC team to please advise.
                7. During the work order, keep an eye on the chat and if the Technician is not responding in the chat, text them and ask them to update their status in the teams chat.
                """)
    st.write("---")
    st.write("VII. Post Work Order")
    st.markdown("""
                1. The Technician will be released when the DXC team releases them. We do not give the release approval.
                2. When the Technician is released, thank them in the Microsoft Teams Chat and then remove them from the Chat.
                3. Pull up the Field Nation work order to get the information required for the resolution note.
                4. Then go to the ConnectWise ticket and add a resolution note:
                    1. The Format is as follows:
                        1. Date of Visit:
                        2. Start Time:
                        3. End Time:
                        4. Time Spent:
                        5. Actions Taken: 
                            1. This is taken from the clouseout notes, a copy and paste works
                """)
def Priority_2_Tickets():
    st.title("P2 Runbook")
    st.write("---")
    st.write("I. In ConnectWise, click on the ticket")

    img_path = "Screenshot 2025-05-13 130224.png"
    if not os.path.exists(img_path):
        st.error(f"Error: Image file not found at '{img_path}'. Please check the path.")
        return
    try:
        img = Image.open(img_path)
    except Exception as e:
        st.error(f"Error loading image: {e}")
        return
    modal = Modal(key="CW Screenshot", title="Connectwise Company Box Screenshot")
    st.image(img, width=300)
    if st.button("Then Click Here"):
        modal.open()
    if modal.is_open():
        with modal.container():
            st.header("Connectwise Company Box - Detailed View")
            st.image(img, use_container_width=True)
            st.markdown("""
            **Site Directions:**
            1. Check the Site Field in the Company: DXC-HP box in ConnectWise
                1. If the Field: Site has a 3 Letter Code, Look in the description and validate that code.
                2. If the Field: Site says Additional Site, then find the Sites Continued section in the Initial Description box and change the Field: Site to that code.
            """)
    st.write("---")
    st.write("II: Identify the Service Window")
    st.markdown("""
                ** Steps: **
                1. Look at the Start Date of Request and Start Time of Request in the ConnectWise Ticket
                2. Look at End Date of Request and End Time of Request in the ConnectWise Ticket
                    1. **If these are the same day, then this is a hard start arrival, this means that the technician must be available to be on site at this start time.**
                    2. **If these are on different days, then this is a schedulable window, schedule the service window during normal business hours unless specified otherwise.**
                """)
    st.write("---")
    st.write("III. Identify a Technician for the Site:")
    site_code_input = st.text_input(
        "Enter 3-Letter Site Code:",
        max_chars=3,
        help="e.g., 'ABC', 'XYZ'. This will filter technicians by site.").upper().strip()
    if site_code_input:
        st.write(f"Searching for technicians for site: **{site_code_input}**")
        try:
            response = supabase.from_('TECH INFORMATION').select("*").eq('SITE', site_code_input).execute()
            data = response.data
            if data:
                import pandas as pd
                df = pd.DataFrame(data)
                st.dataframe(df)
            else:
                st.info(f"No technician information found for site code: **{site_code_input}**")
        except Exception as e:
            st.error(f"An error occurred while fetching data from Supabase: {e}")
            st.warning("Please ensure your Supabase URL, Anon Key, and table/column names are correct.")
    else:
        st.info("Please enter a 3-letter site code to search for technicians.")
    st.write("---")
    st.write("IV. Contact the Technician")
    st.markdown("""
                ** Steps: **
                1. Call the Technician
                    1. If the Technician answers and accepts the work order, **tell the technician you will be routing them a work order on field nation**, then move on to section V
                    2. If the Technician declines, then move onto step 2
                    3. If the Technician does not answer, send this text: "Hi TECHNICIAN_NAME, this is YOUR_NAME with Suryl. We have a work order at the SITE_LOCATION for DATE_OF_SERVICE. Are you available to take this work order"
                    4. Then move to step 2
                2. Call the next technician on the list
                    1. If the Technician answers and accepts the work order, **tell the technician you will be routing them a work order on field nation**, then move on to section V
                    2. If the Technician declines, then move onto step 3
                    3. If the Technician does not answer, send this text: "Hi TECHNICIAN_NAME, this is YOUR_NAME with Suryl. We have a work order at the SITE_LOCATION for DATE_OF_SERVICE. Are you available to take this work order"
                    4. Then move to step 3
                3. Call the next technician on the list
                    1. If the Technician answers and accepts the work order, **tell the technician you will be routing them a work order on field nation**, then move on to section V
                    2. If the Technician declines, then move onto step 4
                    3. If the Technician does not answer, send this text: "Hi TECHNICIAN_NAME, this is YOUR_NAME with Suryl. We have a work order at the SITE_LOCATION for DATE_OF_SERVICE. Are you available to take this work order"
                    4. Then move to step 4                
                4. If no Technician has answered the phone or responded by text, then wait 15 minutes
                    1. **If no response after 15 minutes, Escalate to Callaway Crenshaw: 405-403-9513**
                """)
    st.write("---")
    st.write("V. Assigning the Work Order in Field Nation")
    st.markdown("""
                1. In Connectwise:
                    1. Change the ticket status to Dispatched
                    2. Once that status has been changed, save and refresh the ticket
                    3. Keep refreshing until you see a WO# created in the Additional Details section in ConnectWise
                    4. Once the WO# is created in ConnectWise, move the ticket status to Work Order Created and save the ticket
                2. Login to field nation using your credentials
                    1. Here is the Link: https://app.fieldnation.com/workorders
                3. Click on the Work tab at the top of the screen and then click Flightboard
                4. Navigate to the Draft tab on the flightboard
                5. Here you should see the work order as a draft, find the corresponding ID on the Draft page with the ConnectWise WO# and click on the corresponding title
                6. Once in the work order, there are a few things that need to be checked
                    1. Click on the Schedule box inside the work order
                        1. Change Schedule Type to (Hard Start)
                        2. Change the Date and Time to the agreed upon Date/Time and hit Save
                7. Once the work order has been validated, go to the Providors tab inside the work order
                    1. Select Find Providors tab
                    2. Copy and paste the corresponding Field Nation ID from step 3 for the Identified Technician into the find providor search bar and hit enter
                    3. Validate that this is the correct name of the Identified Technician
                    4. Then slect the route button that is purple
                8. Once the work order is routed in FieldNation, go into the ticket in ConnectWise and add a new note in Discussion
                    1. Fill out this form with the Technicians Name, Email, and ETA
                        1. Name: TECHNICIAN NAME, Mail: TECHNICIAN EMAIL, ETA: DATE/TIME
                """)
    st.write("---")
    st.write("VI. Work Order Specifics")
    st.markdown("""
                1. When the status shows Enroute in ConnectWise, go into Microsoft Teams, Create a Site Chat Labeled "SITE_CODE SUPPORT"
                2. Add the Technician using their Suryl email. Then add carolina.leon@dxc.com, k.perezsilva2@dxc.com, and erick.sanchez@dxc.com
                3. Then send this message in the chat: "Hi Team, TECHNICIAN NAME is on their way to the site."
                4. Text the Technician and tell them that you are adding them to a microsoft teams chat that will be where they will send updates and communicate with the team. Remind them that this is used by logging into their Suryl email and accessing the microsoft teams app
                5. If there is a Microsoft teams meeting link in the Initial Description in ConnectWise or in the Discussion notes in ConnectWise, send that in the chat saying "@TECHNICIAN NAME, Here is the Teams Meeting Link for the work order"
                6. If they ask where the device is, there will be notes on the device location in the ConnectWise Initial Description, if there is no description, then ask the DXC team to please advise.
                7. During the work order, keep an eye on the chat and if the Technician is not responding in the chat, text them and ask them to update their status in the teams chat.
                """)
    st.write("---")
    st.write("VII. Post Work Order")
    st.markdown("""
                1. The Technician will be released when the DXC team releases them. We do not give the release approval.
                2. When the Technician is released, thank them in the Microsoft Teams Chat and then remove them from the Chat.
                3. Pull up the Field Nation work order to get the information required for the resolution note.
                4. Then go to the ConnectWise ticket and add a resolution note:
                    1. The Format is as follows:
                        1. Date of Visit:
                        2. Start Time:
                        3. End Time:
                        4. Time Spent:
                        5. Actions Taken: 
                            1. This is taken from the clouseout notes, a copy and paste works
                """)
def Priority_3_Tickets():
    st.title("P3 Runbook")
    st.write("---")
    st.write("I. In ConnectWise, click on the ticket")

    img_path = "Screenshot 2025-05-13 130224.png"
    if not os.path.exists(img_path):
        st.error(f"Error: Image file not found at '{img_path}'. Please check the path.")
        return
    try:
        img = Image.open(img_path)
    except Exception as e:
        st.error(f"Error loading image: {e}")
        return
    modal = Modal(key="CW Screenshot", title="Connectwise Company Box Screenshot")
    st.image(img, width=300)
    if st.button("Then Click Here"):
        modal.open()
    if modal.is_open():
        with modal.container():
            st.header("Connectwise Company Box - Detailed View")
            st.image(img, use_container_width=True)
            st.markdown("""
            **Site Directions:**
            1. Check the Site Field in the Company: DXC-HP box in ConnectWise
                1. If the Field: Site has a 3 Letter Code, Look in the description and validate that code.
                2. If the Field: Site says Additional Site, then find the Sites Continued section in the Initial Description box and change the Field: Site to that code.
            """)
    st.write("---")
    st.write("II: Identify the Service Window")
    st.markdown("""
                ** Steps: **
                1. Look at the Start Date of Request and Start Time of Request in the ConnectWise Ticket
                2. Look at End Date of Request and End Time of Request in the ConnectWise Ticket
                    1. **If these are the same day, then this is a hard start arrival, this means that the technician must be available to be on site at this start time.**
                    2. **If these are on different days, then this is a schedulable window, schedule the service window during normal business hours unless specified otherwise.**
                """)
    st.write("III. Identify a Technician for the Site:")
    site_code_input = st.text_input(
        "Enter 3-Letter Site Code:",
        max_chars=3,
        help="e.g., 'ABC', 'XYZ'. This will filter technicians by site.").upper().strip()
    if site_code_input:
        st.write(f"Searching for technicians for site: **{site_code_input}**")
        try:
            response = supabase.from_('TECH INFORMATION').select("*").eq('SITE', site_code_input).execute()
            data = response.data
            if data:
                import pandas as pd
                df = pd.DataFrame(data)
                st.dataframe(df)
            else:
                st.info(f"No technician information found for site code: **{site_code_input}**")
        except Exception as e:
            st.error(f"An error occurred while fetching data from Supabase: {e}")
            st.warning("Please ensure your Supabase URL, Anon Key, and table/column names are correct.")
    else:
        st.info("Please enter a 3-letter site code to search for technicians.")
    st.write("---")
    st.write("IV. Contact the Technician")
    st.markdown("""
                ** Steps: **
                1. Text the Technician
                    1. If the Technician answers and accepts the work order, **tell the technician you will be routing them a work order on field nation**, then move on to section V
                    2. If the Technician declines, then move onto step 2
                    3. If the Technician does not answer, start a timer for 15 minutes before texting the next Technician
                    4. Then move to step 2
                2. Call the next technician on the list
                    1. If the Technician answers and accepts the work order, **tell the technician you will be routing them a work order on field nation**, then move on to section V
                    2. If the Technician declines, then move onto step 3
                    3. If the Technician does not answer, start a timer for 15 minutes before texting the next Technician
                    4. Then move to step 3
                3. Call the next technician on the list
                    1. If the Technician answers and accepts the work order, **tell the technician you will be routing them a work order on field nation**, then move on to section V
                    2. If the Technician declines, then move onto step 4
                    3. If the Technician does not answer, start a timer for 15 minutes before texting the next Technician
                    4. Then move to step 4                
                4. If no Technician has answered the phone or responded by text, then wait 15 minutes
                    1. **If no response after 15 minutes, Escalate to Callaway Crenshaw: 405-403-9513**
                """)
    st.write("---")
    st.write("V. Assigning the Work Order in Field Nation")
    st.markdown("""
                1. In Connectwise:
                    1. Change the ticket status to Dispatched
                    2. Once that status has been changed, save and refresh the ticket
                    3. Keep refreshing until you see a WO# created in the Additional Details section in ConnectWise
                    4. Once the WO# is created in ConnectWise, move the ticket status to Work Order Created and save the ticket
                2. Login to field nation using your credentials
                    1. Here is the Link: https://app.fieldnation.com/workorders
                3. Click on the Work tab at the top of the screen and then click Flightboard
                4. Navigate to the Draft tab on the flightboard
                5. Here you should see the work order as a draft, find the corresponding ID on the Draft page with the ConnectWise WO# and click on the corresponding title
                6. Once in the work order, there are a few things that need to be checked
                    1. Click on the Schedule box inside the work order
                        1. Change Schedule Type to (Hard Start)
                        2. Change the Date and Time to the agreed upon Date/Time and hit Save
                7. Once the work order has been validated, go to the Providors tab inside the work order
                    1. Select Find Providors tab
                    2. Copy and paste the corresponding Field Nation ID from step 3 for the Identified Technician into the find providor search bar and hit enter
                    3. Validate that this is the correct name of the Identified Technician
                    4. Then slect the route button that is purple
                8. Once the work order is routed in FieldNation, go into the ticket in ConnectWise and add a new note in Discussion
                    1. Fill out this form with the Technicians Name, Email, and ETA
                        1. Name: TECHNICIAN NAME, Mail: TECHNICIAN EMAIL, ETA: DATE/TIME
                """)
    st.write("---")
    st.write("VI. Work Order Specifics")
    st.markdown("""
                1. When the status shows Enroute in ConnectWise, go into Microsoft Teams, Create a Site Chat Labeled "SITE_CODE SUPPORT"
                2. Add the Technician using their Suryl email. Then add carolina.leon@dxc.com, k.perezsilva2@dxc.com, and erick.sanchez@dxc.com
                3. Then send this message in the chat: "Hi Team, TECHNICIAN NAME is on their way to the site."
                4. Text the Technician and tell them that you are adding them to a microsoft teams chat that will be where they will send updates and communicate with the team. Remind them that this is used by logging into their Suryl email and accessing the microsoft teams app
                5. If there is a Microsoft teams meeting link in the Initial Description in ConnectWise or in the Discussion notes in ConnectWise, send that in the chat saying "@TECHNICIAN NAME, Here is the Teams Meeting Link for the work order"
                6. If they ask where the device is, there will be notes on the device location in the ConnectWise Initial Description, if there is no description, then ask the DXC team to please advise.
                7. During the work order, keep an eye on the chat and if the Technician is not responding in the chat, text them and ask them to update their status in the teams chat.
                """)
    st.write("---")
    st.write("VII. Post Work Order")
    st.markdown("""
                1. The Technician will be released when the DXC team releases them. We do not give the release approval.
                2. When the Technician is released, thank them in the Microsoft Teams Chat and then remove them from the Chat.
                3. Pull up the Field Nation work order to get the information required for the resolution note.
                4. Then go to the ConnectWise ticket and add a resolution note:
                    1. The Format is as follows:
                        1. Date of Visit:
                        2. Start Time:
                        3. End Time:
                        4. Time Spent:
                        5. Actions Taken: 
                            1. This is taken from the clouseout notes, a copy and paste works
                """)
def Priority_4_Tickets():
    st.title("P4 Runbook")
    st.write("---")
    st.write("I. In ConnectWise, click on the ticket")

    img_path = "Screenshot 2025-05-13 130224.png"
    if not os.path.exists(img_path):
        st.error(f"Error: Image file not found at '{img_path}'. Please check the path.")
        return
    try:
        img = Image.open(img_path)
    except Exception as e:
        st.error(f"Error loading image: {e}")
        return
    modal = Modal(key="CW Screenshot", title="Connectwise Company Box Screenshot")
    st.image(img, width=300)
    if st.button("Then Click Here"):
        modal.open()
    if modal.is_open():
        with modal.container():
            st.header("Connectwise Company Box - Detailed View")
            st.image(img, use_container_width=True)
            st.markdown("""
            **Site Directions:**
            1. Check the Site Field in the Company: DXC-HP box in ConnectWise
                1. If the Field: Site has a 3 Letter Code, Look in the description and validate that code.
                2. If the Field: Site says Additional Site, then find the Sites Continued section in the Initial Description box and change the Field: Site to that code.
            """)
    st.write("---")
    st.write("II: Identify the Service Window")
    st.markdown("""
                ** Steps: **
                1. Look at the Start Date of Request and Start Time of Request in the ConnectWise Ticket
                2. Look at End Date of Request and End Time of Request in the ConnectWise Ticket
                    1. **If these are the same day, then this is a hard start arrival, this means that the technician must be available to be on site at this start time.**
                    2. **If these are on different days, then this is a schedulable window, schedule the service window during normal business hours unless specified otherwise.**
                """)
    st.write("---")
    st.write("III. Identify a Technician for the Site:")
    site_code_input = st.text_input(
        "Enter 3-Letter Site Code:",
        max_chars=3,
        help="e.g., 'ABC', 'XYZ'. This will filter technicians by site.").upper().strip()
    if site_code_input:
        st.write(f"Searching for technicians for site: **{site_code_input}**")
        try:
            response = supabase.from_('TECH INFORMATION').select("*").eq('SITE', site_code_input).execute()
            data = response.data
            if data:
                import pandas as pd
                df = pd.DataFrame(data)
                st.dataframe(df)
            else:
                st.info(f"No technician information found for site code: **{site_code_input}**")
        except Exception as e:
            st.error(f"An error occurred while fetching data from Supabase: {e}")
            st.warning("Please ensure your Supabase URL, Anon Key, and table/column names are correct.")
    else:
        st.info("Please enter a 3-letter site code to search for technicians.")
    st.write("---")
    st.write("IV. Contact the Technician")
    st.markdown("""
                ** Steps: **
                1. Text the Technician
                    1. If the Technician answers and accepts the work order, **tell the technician you will be routing them a work order on field nation**, then move on to section V
                    2. If the Technician declines, then move onto step 2
                    3. If the Technician does not answer, start a timer for 15 minutes before texting the next Technician
                    4. Then move to step 2
                2. Call the next technician on the list
                    1. If the Technician answers and accepts the work order, **tell the technician you will be routing them a work order on field nation**, then move on to section V
                    2. If the Technician declines, then move onto step 3
                    3. If the Technician does not answer, start a timer for 15 minutes before texting the next Technician
                    4. Then move to step 3
                3. Call the next technician on the list
                    1. If the Technician answers and accepts the work order, **tell the technician you will be routing them a work order on field nation**, then move on to section V
                    2. If the Technician declines, then move onto step 4
                    3. If the Technician does not answer, start a timer for 15 minutes before texting the next Technician
                    4. Then move to step 4                
                4. If no Technician has answered the phone or responded by text, then wait 15 minutes
                    1. **If no response after 15 minutes, Escalate to Callaway Crenshaw: 405-403-9513**
                """)
    st.write("---")
    st.write("V. Assigning the Work Order in Field Nation")
    st.markdown("""
                1. In Connectwise:
                    1. Change the ticket status to Dispatched
                    2. Once that status has been changed, save and refresh the ticket
                    3. Keep refreshing until you see a WO# created in the Additional Details section in ConnectWise
                    4. Once the WO# is created in ConnectWise, move the ticket status to Work Order Created and save the ticket
                2. Login to field nation using your credentials
                    1. Here is the Link: https://app.fieldnation.com/workorders
                3. Click on the Work tab at the top of the screen and then click Flightboard
                4. Navigate to the Draft tab on the flightboard
                5. Here you should see the work order as a draft, find the corresponding ID on the Draft page with the ConnectWise WO# and click on the corresponding title
                6. Once in the work order, there are a few things that need to be checked
                    1. Click on the Schedule box inside the work order
                        1. Change Schedule Type to (Hard Start)
                        2. Change the Date and Time to the agreed upon Date/Time and hit Save
                7. Once the work order has been validated, go to the Providors tab inside the work order
                    1. Select Find Providors tab
                    2. Copy and paste the corresponding Field Nation ID from step 3 for the Identified Technician into the find providor search bar and hit enter
                    3. Validate that this is the correct name of the Identified Technician
                    4. Then slect the route button that is purple
                8. Once the work order is routed in FieldNation, go into the ticket in ConnectWise and add a new note in Discussion
                    1. Fill out this form with the Technicians Name, Email, and ETA
                        1. Name: TECHNICIAN NAME, Mail: TECHNICIAN EMAIL, ETA: DATE/TIME
                """)
    st.write("---")
    st.write("VI. Work Order Specifics")
    st.markdown("""
                1. When the status shows Enroute in ConnectWise, go into Microsoft Teams, Create a Site Chat Labeled "SITE_CODE SUPPORT"
                2. Add the Technician using their Suryl email. Then add carolina.leon@dxc.com, k.perezsilva2@dxc.com, and erick.sanchez@dxc.com
                3. Then send this message in the chat: "Hi Team, TECHNICIAN NAME is on their way to the site."
                4. Text the Technician and tell them that you are adding them to a microsoft teams chat that will be where they will send updates and communicate with the team. Remind them that this is used by logging into their Suryl email and accessing the microsoft teams app
                5. If there is a Microsoft teams meeting link in the Initial Description in ConnectWise or in the Discussion notes in ConnectWise, send that in the chat saying "@TECHNICIAN NAME, Here is the Teams Meeting Link for the work order"
                6. If they ask where the device is, there will be notes on the device location in the ConnectWise Initial Description, if there is no description, then ask the DXC team to please advise.
                7. During the work order, keep an eye on the chat and if the Technician is not responding in the chat, text them and ask them to update their status in the teams chat.
                """)
    st.write("---")
    st.write("VII. Post Work Order")
    st.markdown("""
                1. The Technician will be released when the DXC team releases them. We do not give the release approval.
                2. When the Technician is released, thank them in the Microsoft Teams Chat and then remove them from the Chat.
                3. Pull up the Field Nation work order to get the information required for the resolution note.
                4. Then go to the ConnectWise ticket and add a resolution note:
                    1. The Format is as follows:
                        1. Date of Visit:
                        2. Start Time:
                        3. End Time:
                        4. Time Spent:
                        5. Actions Taken: 
                            1. This is taken from the clouseout notes, a copy and paste works
                """)





page_selection = st.sidebar.radio(
    "Go to",
    ("Home", "Priority 1 Tickets", "Priority 2 Tickets", "Priority 3 Tickets", "Priority 4 Tickets"))
if page_selection == "Home":
    home_page()
elif page_selection == "Priority 1 Tickets":
    Priority_1_Tickets()
elif page_selection == "Priority 2 Tickets":
    Priority_2_Tickets()
elif page_selection == "Priority 3 Tickets":
    Priority_3_Tickets()
elif page_selection == "Priority 4 Tickets":
    Priority_4_Tickets()
