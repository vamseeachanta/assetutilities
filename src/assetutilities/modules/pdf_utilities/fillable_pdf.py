"""
https://github.com/jorisschellekens/borb-examples#22-steps-to-creating-a-pdf-using-borb


https://stackabuse.com/creating-a-form-in-a-pdf-document-in-python-with-borb/
"""

from borb.pdf import Document, Page
from borb.pdf.canvas.layout.page_layout.multi_column_layout import SingleColumnLayout
from borb.pdf.canvas.layout.page_layout.page_layout import PageLayout
from borb.pdf.pdf import PDF

# Create empty Document
pdf = Document()

# Create empty Page
page = Page()

# Add Page to Document
pdf.add_page(page)

# Create PageLayout
layout: PageLayout = SingleColumnLayout(page)

# New import(s)
from decimal import Decimal

from borb.pdf.canvas.color.color import HexColor
from borb.pdf.canvas.layout.forms.drop_down_list import DropDownList
from borb.pdf.canvas.layout.forms.text_field import TextField
from borb.pdf.canvas.layout.layout_element import Alignment
from borb.pdf.canvas.layout.table.fixed_column_width_table import FixedColumnWidthTable
from borb.pdf.canvas.layout.text.paragraph import Paragraph

# Let's start by adding a heading
layout.add(Paragraph("Patient Information:", font="Helvetica-Bold"))

# Use a table to lay out the form
table: FixedColumnWidthTable = FixedColumnWidthTable(
    number_of_rows=5, number_of_columns=2
)

# Name
table.add(
    Paragraph(
        "Name : ", horizontal_alignment=Alignment.RIGHT, font_color=HexColor("56cbf9")
    )
)
table.add(TextField(value="Doe", font_color=HexColor("56cbf9"), font_size=Decimal(20)))

# Surname
table.add(
    Paragraph(
        "Surname : ",
        horizontal_alignment=Alignment.RIGHT,
        font_color=HexColor("56cbf9"),
    )
)
table.add(TextField(value="John", font_color=HexColor("56cbf9"), font_size=Decimal(20)))

# Gender
table.add(Paragraph("Gender : ", horizontal_alignment=Alignment.RIGHT))
table.add(
    DropDownList(
        possible_values=[
            "Female",
            "Male",
            "Other",
            "Prefer not to disclose",
        ]
    )
)

# New import(s)
from borb.pdf.canvas.layout.forms.country_drop_down_list import CountryDropDownList

# Country of Residence
table.add(Paragraph("Country of Residence : ", horizontal_alignment=Alignment.RIGHT))
table.add(CountryDropDownList(value="Belgium"))

# Nationality
table.add(Paragraph("Nationality : ", horizontal_alignment=Alignment.RIGHT))
table.add(CountryDropDownList(value="Belgium"))

# Set some properties on the table to make the layout prettier
table.set_padding_on_all_cells(Decimal(5), Decimal(5), Decimal(5), Decimal(5))
table.no_borders()

# Adding Table to PageLayout
layout.add(table)

# Data protection policy
layout.add(Paragraph("Data Protection Policy", font="Helvetica-Bold"))

# Dummy text
layout.add(
    Paragraph(
        """
    ** Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
    Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
    Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
    Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
    """,
        font="Helvetica-Oblique",
    )
)

# New import(s)
import typing

# from borb.pdf.canvas.layout.image.shape import Shape
from borb.pdf import ConnectedShape
from borb.pdf.canvas.geometry.rectangle import Rectangle
from borb.pdf.canvas.line_art.line_art_factory import LineArtFactory
from borb.pdf.page.page_size import PageSize

ps: typing.Tuple[Decimal, Decimal] = PageSize.A4_PORTRAIT.value
r: Rectangle = Rectangle(Decimal(0), Decimal(32), ps[0], Decimal(8))

# layout.add(
#     ConnectedShape(
#         LineArtFactory.sticky_note(r),
#         stroke_color=X11Color("Yellow"),
#         fill_color=X11Color("White"),
#         line_width=Decimal(1),
#     ))

ConnectedShape(
    points=LineArtFactory.rectangle(r),
    stroke_color=HexColor("56cbf9"),
    fill_color=HexColor("56cbf9"),
).layout(page, r)

# Shape(points=LineArtFactory.rectangle(r),
#       stroke_color=HexColor("56cbf9"),
#       fill_color=HexColor("56cbf9")).layout(page, r)

# store
with open("output.pdf", "wb") as pdf_file_handle:
    PDF.dumps(pdf_file_handle, pdf)
