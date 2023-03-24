import streamlit as st
import os
import re
import pandas as pd
import datetime as dt
import PyPDF2
import time
import shutil

def extract_from_merged_pdf(file, shop):
    if shop == 'shopee':
        with open(path, 'rb') as file:
            temp_pdf = PyPDF2.PdfReader(file)
            pdf_dict = {}

            # Iterate over all pages in the pdf
            for page in range(len(temp_pdf.pages)):
                pdf_dict[page] = {}

                # Split airway bill into single page
                pdf_writer = PyPDF2.PdfWriter()
                cur_page = temp_pdf.pages[page]
                pdf_writer.add_page(cur_page)
                output_filename = f'temp/shopee_airwayBill_temp_page_{page+1}.pdf'
                pdf_dict[page]['path'] = output_filename

                # Extract text from each pdf
                cur_text = cur_page.extract_text()
                pdf_dict[page]['text'] = cur_text

                # Parse iten name
                cur_text = cur_text.split('#Name')[1]
                regex_match = re.search(r"Name\sQty\s\d([\w\s\-\=\`\~\!\@\#\$\%\^\&\*\(\)\_\+\|\'\"\’\/\.\,\[\]\°\:]+?)(?=[BS]{1}[0-9]{5})([BS]{1}[0-9]{5})([\s\S]+?)(\d+)$", cur_text, re.MULTILINE)
                time.sleep(0.1)
                if regex_match is None:
                    print(cur_text)
                    print(page)
                    print()
                    cur_text = cur_text.split('Name Qty\n')[1]
                    regex_match = re.search(r"^\d([\w\s\-\=\`\~\!\@\#\$\%\^\&\*\(\)\_\+\|\'\/\.\,\[\]\°\"\’\:]+[\s\S]+)(\d+)$\n\*\*T", cur_text, re.MULTILINE)
                    pdf_dict[page]['sku'] = None
                    pdf_dict[page]['variation'] = None
                    pdf_dict[page]['quantity'] = regex_match.groups()[1]
                else:
                    pdf_dict[page]['sku'] = regex_match.groups()[1]
                    pdf_dict[page]['variation'] = regex_match.groups()[2]
                    pdf_dict[page]['quantity'] = regex_match.groups()[3]
                item_name = regex_match.groups()[0]
                final_quantity = re.search(r"Packing\sList\:\n\:\d+\n(^\d+$)", cur_text, re.MULTILINE).groups()[0]
                pdf_dict[page]['final_quantity'] = final_quantity
                pdf_dict[page]['item_name'] = item_name

                # Save each page as pdf
                os.makedirs(os.path.dirname(output_filename), exist_ok=True)
                with open(output_filename, 'wb') as out:
                    pdf_writer.write(out)
        return pdf_dict
    elif shop == 'lazada':
        return pdf_dict


cur_date = dt.datetime.now().strftime("%d-%m-%Y")

def printer_sorter_algo(df_size, method = 'normal'):
    if method == 'two-sided':
        first_pile = []
        second_pile = []
        if df_size%2 == 0:
            first_pile_index = range(1,int(df_size/2)+1)
            second_pile_index = first_pile_index
        elif df_size == 3:
            return [1,2,3]
        else:
            first_pile_index = range(1, int((df_size+1)/2))
            second_pile_index = range(1, int((df_size+1)/2)+1)
        first_pile = [int((4*x+(-1)**x-1)/2) for x in first_pile_index]
        second_pile = [int((4*x + (-1)**(x+1) -1)/2) for x in second_pile_index]
        final_pile = first_pile + second_pile
        return final_pile
    elif method == 'triangle':
        first_pile = []
        second_pile = []
        third_pile = []
        for i in range(0, df_size, 3):
            first_pile.append(i)
        for j in range(1, df_size, 3):
            second_pile.append(j)
        for k in range(2, df_size, 3):
            third_pile.append(k)
        final_pile = first_pile + second_pile + third_pile
        return final_pile
    elif method == 'normal':
        return range(df_size)

def get_path_of_pdf_files(uploaded_files, shop = 'shopee'):
    pdf_files = []
    for uploaded_file in uploaded_files:
        if uploaded_file.type == "application/pdf":
            file_path = os.path.join(f"{shop}_awb_to_sort", uploaded_file.name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            pdf_files.append(file_path)
    return pdf_files

def merge_pdf_files(pdf_files_list):
    merged_pdf_writer = PyPDF2.PdfWriter()
    for path in pdf_files_list:
        merged_pdf_writer.append(path)
    return merged_pdf_writer

def save_writer_as_pdf(pypdf_object, file_description, shop = 'shopee'):
    filename = f'{cur_date}/{cur_date}_{shop}_{file_description}.pdf'
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'wb') as out:
        pypdf_object.write(out)
    return filename

def sort_pdf_pages(pdf_dict):
    df = pd.DataFrame(pdf_dict).T.reset_index()
    df = df.sort_values(by = 'item_name')
    return df

def split_merged_pdf(df):
    single_order_df = df[df.quantity == df.final_quantity]
    single_order_df['new_position'] = printer_sorter_algo(len(single_order_df), 'triangle')
    single_order_df = single_order_df.sort_values('new_position')
    mixed_order_df = df[df.quantity != df.final_quantity]
    mixed_order_df['new_position'] = printer_sorter_algo(len(mixed_order_df), 'triangle')
    mixed_order_df = mixed_order_df.sort_values('new_position')
    return single_order_df, mixed_order_df

def creeate_pdf_writer_from_pages(df):
    sorted_order = df.path.tolist()
    new_order_pdf = PyPDF2.PdfWriter()
    for path in sorted_order:
        new_order_pdf.append(path)
    return new_order_pdf


def delete_uploaded_files(pdf_files):
    for pdf in pdf_files:
        os.makedirs(os.path.dirname(f'{cur_date}/file_made_from/{pdf}'), exist_ok=True)
        shutil.move(pdf, f'{cur_date}/file_made_from/{pdf}')
    shutil.rmtree('temp')

def download_button(pdf_file_path):
    with open(pdf_file_path, "rb") as file:
        btn=st.download_button(
            label="click me to download pdf",
            data=file,
            file_name=pdf_file_path,
            mime="application/octet-stream"
st.title("AWB Sorter")
uploaded_files = st.file_uploader("Upload PDF files", type="pdf", accept_multiple_files=True)

if uploaded_files:
    st.write(f"{len(uploaded_files)} file(s) uploaded:")
    shop = st.selectbox("Choose which platform to sort for", ['lazada', 'shopee'])
    for uploaded_file in uploaded_files:
        st.write(uploaded_file.name)

    pdf_files = get_path_of_pdf_files(uploaded_files, shop)
    unsorted_merged_file = merge_pdf_files(pdf_files)
    path = save_writer_as_pdf(unsorted_merged_file, shop = shop, file_description = 'merged_unsorted')
    pdf_dict = extract_from_merged_pdf(path, shop = shop)
    df = sort_pdf_pages(pdf_dict)
    single, mixed = split_merged_pdf(df)
    single_order_path = creeate_pdf_writer_from_pages(single)
    mixed_order_path = creeate_pdf_writer_from_pages(mixed)
    single_path = save_writer_as_pdf(single_order_path, shop = shop, file_description = 'single_orders_sorted')
    mixed_path = save_writer_as_pdf(mixed_order_path, shop = shop, file_description = 'mixed_orders_sorted')
    delete_uploaded_files(pdf_files)
    st.download_button("Download Single Orders", single_path)
    st.download_button("Download Mixed Orders", mixed_path)

