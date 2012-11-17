from reportlab.graphics import barcode, renderPDF
from reportlab.lib.pagesizes import inch
from reportlab.pdfgen import canvas

def label(style_num,
          color_num,
          size_abbr,
          color_abbr,
          qty,
          po_num,
          description):
    c = canvas.Canvas("label.pdf", (4 * inch, 2 * inch))

    # Barcode & barcode string
    bc_str = "{}-{}{}".format(style_num, color_num, size_abbr)
    renderPDF.draw(
        barcode.createBarcodeDrawing("Code128",
                                     value=bc_str,
                                     barWidth=.7,
                                     barHeight=30),
        c,
        0,
        1.4 * inch
    )
    c.setFontSize(12)
    c.drawString(.35 * inch, 1.2 * inch, bc_str)

    # Description
    c.setFontSize(9)
    c.drawString(.2 * inch, .8 * inch, description)

    # Color abbreviation
    c.drawString(.2 * inch, .6 * inch, color_abbr)

    # Size abbreviation
    c.setFontSize(12)
    c.drawRightString(3.7 * inch, 1.5 * inch, size_abbr)

    # Quantity
    c.setFontSize(20)
    c.drawRightString(3.7 * inch, 1.2 * inch, qty)

    # PO number barcode & string
    renderPDF.draw(barcode.createBarcodeDrawing("Code128", value=po_num),
                   c,
                   2.3 * inch,
                   .6 * inch)
    c.setFontSize(8)
    c.drawString(2.6 * inch, .5 * inch, po_num)

    c.save()

if __name__ == '__main__':
    label("C0252A", "033", "LGE", "CHA", "36", "PO095103", "ADULT SS TEE")
