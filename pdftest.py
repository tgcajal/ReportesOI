import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    KeepTogether,
    PageTemplate,
    Frame,
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# def add_page_number(canvas, doc):
#     page_num = canvas.getPageNumber()
#     text = f"Página {page_num}"
#     canvas.drawRightString(7.5 * inch, 0.75 * inch, text)

def create_pdf_report(dataframes, pdf_filename, filter_info):
    """
    Generate a PDF report from a list of DataFrames.

    Parameters:
    - dataframes: List of tuples in the format (title, DataFrame)
    - pdf_filename: Name of the output PDF file
    """
    # Set up the PDF document
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    elements = []
    elements.append(Paragraph(f'Filtros: {filter_info}'))
    styles = getSampleStyleSheet()
    style_heading = styles['Heading1']

    for idx, (title, df) in enumerate(dataframes):
        # Create a list to hold the elements for the current table
        table_elements = []

        # Add a title for each table
        table_title = Paragraph(title, style_heading)
        table_elements.append(table_title)
        table_elements.append(Spacer(1, 12))

        # Convert DataFrame to a list of lists
        data = [df.columns.tolist()] + df.values.tolist()

        # Create the table
        table = Table(data, hAlign='LEFT')
        table.hAlign = 'LEFT'  # Align the table to the right

        # Apply styling to the table
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#d5dae6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f2f2f2')]),
        ]))

        table_elements.append(table)
        table_elements.append(Spacer(1, 24))

        # Wrap the table elements in KeepTogether to prevent splitting
        elements.append(KeepTogether(table_elements))

    # Add page numbers
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
    template = PageTemplate(id='PageTemplate', frames=frame)#, onPage=add_page_number(canvas, doc))
    doc.addPageTemplates([template])

    # Build the PDF
    doc.build(elements)
    #print(f"PDF report '{pdf_filename}' has been created successfully.")
#####

# from reportlab.lib.pagesizes import letter
# from reportlab.pdfgen import canvas
# from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph
# from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.lib import colors
# import pandas as pd

# # Sample DataFrames
# df1 = pd.DataFrame({
#     'A': [1, 2, 3],
#     'B': [4, 5, 6],
#     'C': [7, 8, 9]
# })
# df2 = pd.DataFrame({
#     'X': ['a', 'b', 'c'],
#     'Y': ['d', 'e', 'f'],
#     'Z': ['g', 'h', 'i']
# })

# # Save location
# pdf_filename = "example_report.pdf"

# # Create a document
# doc = SimpleDocTemplate(pdf_filename, pagesize=letter)

# # Define styles
# styles = getSampleStyleSheet()
# title_style = styles['Heading1']
# subtitle_style = styles['Heading2']

# # Function to convert DataFrame to ReportLab Table
# def dataframe_to_table(dataframe):
#     data = [dataframe.columns.to_list()] + dataframe.values.tolist()
#     table = Table(data, hAlign='RIGHT')
#     table.setStyle(TableStyle([
#         ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
#         ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
#         ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
#         ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#         ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
#         ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
#         ('GRID', (0, 0), (-1, -1), 1, colors.black),
#     ]))
#     return table

# # Build content
# elements = []

# # Title
# elements.append(Paragraph("Example Report", title_style))

# # First Table with title
# elements.append(Paragraph("DataFrame 1", subtitle_style))
# elements.append(dataframe_to_table(df1))

# # Space
# elements.append(Paragraph("<br/><br/>", styles['Normal']))

# # Second Table with title
# elements.append(Paragraph("DataFrame 2", subtitle_style))
# elements.append(dataframe_to_table(df2))

# # Build PDF
# doc.build(elements)

# print(f"PDF saved as {pdf_filename}")
