from collections import defaultdict
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas


def invoice_generator_pdf(customer_name, customer_email, items, total, filename):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter  # Get page size

    # Set up navy blue color
    navy_blue = colors.HexColor("#000080")

    # Draw the navy blue border (margin)
    margin = 20  # Margin size (in points)
    c.setStrokeColor(navy_blue)
    c.setLineWidth(5)  # Thickness of the border
    c.rect(margin, margin, width - 2 * margin, height - 2 * margin)  # Draw rectangle with margin

    # Move content within the margin
    c.translate(margin + 10, height - margin - 50)  # Adjust content starting point

    # Add the organization name "Your Store" in the header
    c.setFont('Helvetica-Bold', 16)
    c.drawString(30, 0, "Wonderland Bookstore")

    # Draw a line under the header
    c.setLineWidth(1)
    c.line(30, -25, width - 2 * margin, -25)  # Line under header

    # Adding other text such as customer details
    c.setFont('Helvetica', 12)
    c.drawString(30, -50, 'Invoice Statement')
    c.drawString(30, -65, f'Customer Email: {customer_email}')
    c.drawString(30, -80, f'Customer Name: {customer_name}')

    today_date = datetime.now().strftime('%Y-%m-%d')
    c.drawString(400, -50, f'Date: {today_date}')

    # Drawing a table for items
    c.drawString(30, -100, 'Items:')
    y = -120

    unique_items = defaultdict(lambda: {'count': 0})

    for item in items:
        key = (item['Title'], item['Price'])
        unique_items[key]['Title'] = item['Title']
        unique_items[key]['Price'] = item['Price']
        unique_items[key]['count'] += 1

    result = list(unique_items.values())

    # Absolute positions for the columns (X-coordinates)
    title_x = 30
    count_x = 350
    price_x = 450

    # Draw the header at the same positions
    c.drawString(title_x, y, "Title")
    c.drawString(count_x, y, "Count")
    c.drawString(price_x, y, "Price")
    y -= 15  # Move down for the next line

    # Now iterate through the items and print each one
    for item in result:
        c.drawString(title_x, y, item['Title'])
        c.drawString(count_x, y, str(item['count']))
        c.drawString(price_x, y, f"{float(item['count']) * float(item['Price']):.2f} Euro")

        y -= 15  # Adjust Y position for the next line

    # Add total amount
    c.drawString(30, y - 20, f"Total Amount: {float(total):.2f} {'Euro'}")

    # Draw a line between body and footer
    c.line(30, y - 50, width - 2 * margin, y - 50)

    # Footer with "Thanks for your shopping" message
    footer_y_position = margin + 10  # Position the footer near the bottom
    c.setFont('Helvetica-Oblique', 12)  # Use 'Helvetica-Oblique' for italic style
    c.drawCentredString(width / 2, footer_y_position, "Thanks for your shopping")

    c.showPage()
    c.save()
