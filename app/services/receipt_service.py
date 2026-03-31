from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.database.models.business import Business
from app.database.models.sale import Sale
from app.database.models.sale_item import SaleItem
from app.database.session import SessionLocal


class ReceiptService:
    """Service for generating receipt data for display and printing."""

    def get_receipt_data(self, business_id: int, sale_id: int) -> dict | None:
        """
        Fetch receipt data for a sale.

        Returns a dictionary with:
        - business_name, phone, location
        - sale_id, sale_number, date, time
        - payment_method, transaction_ref
        - items (list of line items)
        - subtotal, discount, tax, total
        - footer_text
        """
        with SessionLocal() as session:
            # Fetch business and sale with eagerly loaded items
            business = session.scalar(
                select(Business).where(Business.id == business_id)
            )
            sale = session.scalar(
                select(Sale)
                .where(Sale.id == sale_id, Sale.business_id == business_id)
                .options(joinedload(Sale.items).joinedload(SaleItem.product))
            )

            if not business or not sale:
                return None

            # Calculate tax amount
            tax_percent = float(business.tax_percent or 0.0)
            tax_amount = (sale.subtotal * tax_percent) / 100.0

            # Format items
            items = []
            for item in sale.items:
                product_name = item.product.name if item.product else "N/A"
                items.append({
                    "product_name": product_name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "line_total": item.line_total,
                })

            # Format datetime
            sale_datetime = sale.created_at
            sale_date = sale_datetime.strftime("%d %b %Y")
            sale_time = sale_datetime.strftime("%H:%M")

            # Payment method display
            payment_display = sale.payment_method.upper()
            if sale.payment_method == "mpesa" and sale.transaction_ref:
                payment_display = f"M-Pesa ({sale.transaction_ref})"

            receipt_data = {
                "business_name": business.business_name,
                "phone": business.phone or "",
                "location": business.location or "",
                "sale_number": f"#{sale.id:06d}",
                "sale_id": sale.id,
                "date": sale_date,
                "time": sale_time,
                "payment_method": payment_display,
                "transaction_ref": sale.transaction_ref or "",
                "items": items,
                "subtotal": sale.subtotal,
                "discount": sale.discount,
                "tax_percent": tax_percent,
                "tax_amount": tax_amount,
                "total": sale.total,
                "footer_text": business.receipt_footer or "",
                "currency": business.currency or "KES",
            }

            return receipt_data
