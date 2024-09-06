import streamlit as st
import tensorflow as tf
import numpy as np
from tensorflow.keras.utils import img_to_array
from PIL import Image
import os
from fpdf import FPDF
from groq import Groq
from io import BytesIO

# -----------------------------#
#        Custom CSS Styling    #
# -----------------------------#
st.markdown(
    """
    <style>

    .main, .block-container {
    padding-top: 10px !important;
    }

    /* Sidebar styling */
    .sidebar .sidebar-content {
        background-color: #f9f9f9;  /* Same as main content background */
        color: #AA3C3B;  /* Text color in sidebar */
    }

    /* Sidebar button styling */
    .stButton>button {
        background-color: #AA3C3B;
        color: white;
        border: none;
        padding: 10px 20px;
        font-size: 16px;
        border-radius: 5px;
        cursor: pointer;
    }

    /* Sidebar button on hover */
    .stButton>button:hover {
        background-color: #006666;
    }

    /* Main title */
    .main-title {
        font-family: 'Arial Black', sans-serif;
        font-size: 36px;
        color: #AA3C3B;
        text-align: left;
        margin-left: 20px;
        margin-top: 30px;
    }

    /* General text */
    .custom-text {
        color: #AA3C3B;  /* Custom text color */
    }

    /* Logo */
    .logo {
        display: block;
        margin-left: auto;
        margin-right: auto;
        width: 130px;
    }

    /* Prediction text */
    .prediction {
        font-size: 24px;
        color: #FF6347;
        text-align: center;
        margin-top: 20px;
    }

    /* Adjusting the padding for the top container */
    .top-container {
        width: 90%;
        display: flex;
        align-items: center;
        padding: 20px 0;
    }

    /* Center the buttons */
    .center-button {
        display: flex;
        justify-content: center;
        margin-top: 20px;
    }

    /* Button styling */
    .center-button button {
        background-color: #AA3C3B;
        color: white;
        padding: 10px 20px;
        font-size: 18px;
        border-radius: 5px;
        cursor: pointer;
        border: none;
    }

    /* Button hover */
    .center-button button:hover {
        background-color: #FF6347;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------------#
#         Sidebar Navigation    #
# -----------------------------#
# Display the logo on the sidebar
logo_path = os.path.join('image', "main.png")
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, use_column_width=True, width=130, caption="", output_format="PNG")
else:
    st.sidebar.warning("Logo image not found. Please check the path.")

# Update page navigation with new tabs
page = st.sidebar.radio("Go to", ["Home", "User History", "Settings", "Help", "About"])

# -----------------------------#
#         LLM work             #
# -----------------------------#
client = Groq(
    api_key="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",
)

# Function to generate the inspection report in PDF format
def generate_inspection_report(predicted_class, report_text):
    pdf = FPDF()
    pdf.add_page()

    # Title
    pdf.set_font("Arial", size=16)
    pdf.cell(200, 10, txt="Meat Inspection Report", ln=True, align="C")

    # Classification Result
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Classification: {predicted_class}", ln=True)

    # Report Details
    pdf.multi_cell(0, 10, report_text)

    # Save the PDF to a string buffer instead of a file
    pdf_output = pdf.output(dest='S').encode('latin1')  # 'S' returns a string, encoded to match PDF format
    pdf_buffer = BytesIO(pdf_output)  # Convert the string to BytesIO object for download
    
    return pdf_buffer

# Function to create the report content using Groq LLM
def create_llm_report(predicted_class):
    prompt_content = (
        f"The meat is classified as {predicted_class}.\n"
        "Generate a detailed inspection report including:\n"
        "1. Recommended actions\n"
        "2. Possible shelf-life\n"
        "3. Guidelines on handling spoiled meat (if applicable)\n"
        "4. Whether the meat is eatable or not."
        "Just include these above 4 mentioned things don't add any extra Info"
    )

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt_content,
            }
        ],
        model="llama3-8b-8192",
    )

    report_text = chat_completion.choices[0].message.content
    return report_text

# -----------------------------#
#           Home Page           #
# -----------------------------#
if page == "Home":
    # Create two columns for logo and title
    col1, col2 = st.columns([1, 3])  # Adjust the ratio as needed

    with col1:
        # Display the logo
        if os.path.exists(logo_path):
            st.image(logo_path, use_column_width=True, width=130, caption="", output_format="PNG")
        else:
            st.warning("Logo image not found. Please check the path.")

    with col2:
        # Display the main title
        st.markdown('<h1 class="main-title">Meat Quality Analyzer</h1>', unsafe_allow_html=True)

    # Add a brief description below the header
    st.markdown(
        '<p class="custom-text" style="font-size:18px;">Upload an image of meat, and the model will predict whether it is Fresh, Half Fresh, or Spoiled.</p>',
        unsafe_allow_html=True)

    # File uploader
    uploaded_file = st.file_uploader("", type=["jpg", "jpeg", "png"], key="fileUploader")

    if uploaded_file is not None:
        # Display the uploaded image with custom styling
        image = Image.open(uploaded_file)
        # Preprocess the image
        img = image.resize((128, 128))
        x = img_to_array(img)
        x /= 255
        x = np.expand_dims(x, axis=0)
        images = np.vstack([x])
        # -----------------------------#
        #       Model Prediction        #
        # -----------------------------#
        @st.cache_resource
        def load_model():
            model = tf.keras.models.load_model('meat_quality_analyzer_model.h5')
            return model
        
        model = load_model()

        # Define class names
        class_names = ['Fresh', 'Half Fresh', 'Spoiled']

        classes = model.predict(images, batch_size=10)
        print(classes[0])
        predicted_class = class_names[np.argmax(classes[0])]

        # Display prediction
        st.markdown(f'<p class="prediction">Prediction: <strong>{predicted_class}</strong></p>', unsafe_allow_html=True)

        # Center the report button
        st.markdown('<div class="center-button">', unsafe_allow_html=True)

        if st.button("Generate Inspection Report"):
            report_text = create_llm_report(predicted_class)
            report_buffer = generate_inspection_report(predicted_class, report_text)
            
            # Provide download button with the in-memory PDF buffer
            st.download_button(
                label="Download Report",
                data=report_buffer,
                file_name="inspection_report.pdf",
                mime="application/pdf"
            )

        st.markdown('</div>', unsafe_allow_html=True)


# -----------------------------#
#           About Page          #
# -----------------------------#


elif page == "About":
    team_path = os.path.join('image', "team.JPG")
    st.markdown('<h1 class="main-title">About Us</h1>', unsafe_allow_html=True)
    st.image(team_path, use_column_width=True, width=150, caption="", output_format="JPG")


# -----------------------------#
#        User History Tab       #
# -----------------------------#
elif page == "User History":
    st.markdown('<h1 class="main-title">Inspection History</h1>', unsafe_allow_html=True)
    st.markdown('<p class="custom-text">View your past inspections and download previous reports.</p>', unsafe_allow_html=True)
    
    # Mockup: Display a list of previous reports
    history = ["Report 1: Fresh", "Report 2: Spoiled", "Report 3: Half Fresh"]
    for item in history:
        st.write(f"- {item}")

# -----------------------------#
#       Settings Tab            #
# -----------------------------#
elif page == "Settings":
    st.markdown('<h1 class="main-title">Settings</h1>', unsafe_allow_html=True)
    st.markdown('<p class="custom-text">Adjust your preferences for notifications and thresholds.</p>', unsafe_allow_html=True)
    
    # Mockup: Settings form for notification and freshness threshold
    notifications = st.checkbox("Enable Email Notifications", value=True)
    freshness_threshold = st.slider("Freshness Threshold (1-100)", min_value=1, max_value=100, value=50)

    st.write(f"Notifications Enabled: {notifications}")
    st.write(f"Freshness Threshold: {freshness_threshold}")

# -----------------------------#
#       Help Tab                #
# -----------------------------#
elif page == "Help":
    st.markdown('<h1 class="main-title">Help & Support</h1>', unsafe_allow_html=True)
    st.markdown('<p class="custom-text">Get assistance on using the MeatInspect.AI platform.</p>', unsafe_allow_html=True)
    
    st.write("For any queries or issues, please contact our support team at support@meatinspect.ai")
