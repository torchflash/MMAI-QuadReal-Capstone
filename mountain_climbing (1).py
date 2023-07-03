import streamlit as st

def check_file_format(file):
    # Check if the file format is correct
    if file.type != "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        return False

    # Check if the file name is in the format "YYYY-MM"
    filename_parts = file.name.split(".")
    if len(filename_parts) != 2 or filename_parts[0] == "" or filename_parts[1] != "xlsx":
        return False

    return True

def main():
    st.title("Data File Uploader")

    # File uploader
    uploaded_file = st.file_uploader("Upload a file", type="xlsx")

    if uploaded_file is not None:
        if check_file_format(uploaded_file):
            st.success("File uploaded successfully!")
        else:
            st.error("Wrong format. Please upload another file.")

if __name__ == "__main__":
    main()
