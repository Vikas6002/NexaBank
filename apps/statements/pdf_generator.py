from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import io

def generate_account_statement_pdf(account, transactions):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    styles = getSampleStyleSheet()
    
    # Title
    elements.append(Paragraph(f"Account Statement", styles['Heading1']))
    elements.append(Paragraph(f"Account Number: {account.account_number}", styles['Normal']))
    elements.append(Paragraph(f"Account Type: {account.get_account_type_display()}", styles['Normal']))
    elements.append(Paragraph(f"Current Balance: ₹{account.balance}", styles['Normal']))
    elements.append(Paragraph(" ", styles['Normal'])) # Spacing
    
    data = [['Date', 'Type', 'Amount', 'Status']]
    
    for tx in transactions:
        amount_sign = "+" if tx.type == "DEPOSIT" or tx.to_account == account else "-"
        data.append([
            tx.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            tx.type,
            f"{amount_sign}₹{tx.amount}",
            tx.status
        ])
        
    t = Table(data, colWidths=[150, 100, 100, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(t)
    doc.build(elements)
    
    buffer.seek(0)
    return buffer
