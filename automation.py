import streamlit as st
from PIL import Image
import os
import pandas as pd
from pytesseract import image_to_string
from word2number import w2n
import re
from datetime import datetime

# Function to extract text from invoice image
def extract_text_from_invoice(image_path):
    with Image.open(image_path) as img:
        invoice_text = image_to_string(img)
        return invoice_text

# Function to extract invoice data
def extract_invoice_data(invoice_text):
    sgst_pattern = r'SGST PAYBLE\s+(\d+\.\d+)'
    cgst_pattern = r'CGST PAYBLE\s+(\d+\.\d+)'
    sgst_match = re.search(sgst_pattern, invoice_text, re.IGNORECASE)
    cgst_match = re.search(cgst_pattern, invoice_text, re.IGNORECASE)
    sgst = sgst_match.group(1) if sgst_match else None
    cgst = cgst_match.group(1) if cgst_match else None
    return sgst, cgst

# Function to extract party total from invoice text
def extract_party_total(invoice_text):
    party_total_pattern = r'Rs\. ([A-Za-z ]+) Only'
    party_total_match = re.search(party_total_pattern, invoice_text, re.IGNORECASE)
    party_total = party_total_match.group(1) if party_total_match else None
    return party_total

# Function to extract date from invoice text
def extract_date(invoice_text):
    date_pattern = r"Invoice Date\s*:?(\s+)?([0-9][0-9]-[0-9][0-9]-\d{4})"
    date_match = re.search(date_pattern, invoice_text)
    date = date_match.group(2) if date_match else None
    return date

# Function to process single invoice
def process_single_invoice(uploaded_file):
    if uploaded_file is None:
        st.write("Please upload an image.")
        return None

    # Read the uploaded image
    image = Image.open(uploaded_file)

    # Perform OCR
    invoice_text = image_to_string(image)

    # Extract data
    invoice_name = uploaded_file.name  # Extract filename
    sgst, cgst = extract_invoice_data(invoice_text)
    party_total = extract_party_total(invoice_text)
    date = extract_date(invoice_text)
    number = w2n.word_to_num(party_total)

    return {
        "Invoice Name": invoice_name,
        "Date": date,
        "SGST Payable": sgst,
        "CGST Payable": cgst,
        "Total": number,
        "Image": image  # Store image for display
    }

# Function to process multiple invoices in a folder
def process_multiple_invoices(folder_path):
    if not folder_path:
        st.write("Please provide a folder path.")
        return None

    invoice_data = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".jpg") or filename.endswith(".png"):
            invoice_path = os.path.join(folder_path, filename)
            invoice_text = extract_text_from_invoice(invoice_path)
            invoice_name = os.path.splitext(filename)[0]
            sgst, cgst = extract_invoice_data(invoice_text)
            party_total = extract_party_total(invoice_text)
            date = extract_date(invoice_text)
            number = w2n.word_to_num(party_total) if party_total else None
            if date:
                invoice_data.append({
                    "Invoice Name": invoice_name,
                    "Date": date,
                    "SGST Payable": sgst,
                    "CGST Payable": cgst,
                    "Total": number,
                     # Store image for display
                })
            else:
                st.warning(f"Skipping invoice '{invoice_name}' due to missing or invalid date.")
    return invoice_data

# Function to generate sales line chart
def generate_sales_chart(invoice_data):
    # Convert DataFrame to ensure consistency of dates
    df = pd.DataFrame(invoice_data)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce', format='%d-%m-%Y')

    # Filter out records with invalid dates
    df = df.dropna(subset=['Date'])

    if not df.empty:
        # Group by month and sum total
        df['Month'] = df['Date'].dt.strftime('%Y-%m')
        monthly_sales = df.groupby('Month')['Total'].sum()

        # Plotting
        st.subheader("Sales Line Chart")
        st.line_chart(monthly_sales)
    else:
        st.warning("No valid data available for generating the sales line chart.")

# Streamlit app
def main():
    st.title("Invoice Data Extraction")

    # Option to upload single invoice image
    uploaded_file = st.file_uploader("Upload Single Invoice Image", type=["jpg", "png"])

    # Option to upload folder containing multiple invoice images
    folder_path = st.text_input("Upload Folder Containing Invoice Images")

    # Button to process and display invoice data
    if st.button("Process"):
        if uploaded_file is not None:
            # Process single invoice
            invoice_data = process_single_invoice(uploaded_file)
            if invoice_data:
                st.write(pd.DataFrame([invoice_data]))

                # Display single invoice image
                st.image(invoice_data["Image"], caption=invoice_data["Invoice Name"])
        elif folder_path:
            # Process multiple invoices in folder
            invoice_data = process_multiple_invoices(folder_path)
            if invoice_data:
                # Display invoice data in DataFrame
                st.write(pd.DataFrame(invoice_data))

                # Generate and display sales line chart
                generate_sales_chart(invoice_data)

if __name__ == "__main__":
    main()
