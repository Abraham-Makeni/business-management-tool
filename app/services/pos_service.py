from sqlalchemy import select

from app.database.models.product import Product
from app.database.models.sale import Sale
from app.database.models.sale_item import SaleItem
from app.database.repositories.sale_repo import SaleRepository
from app.database.repositories.stock_movement_repo import StockMovementRepository
from app.database.session import SessionLocal


class POSService:
    ALLOWED_PAYMENT_METHODS = {"cash", "mpesa"}

    def process_sale(
        self,
        business_id: int,
        cart_items: list[dict],
        payment_method: str,
        discount: float = 0.0,
        cashier_id: int | None = None,
        transaction_ref: str | None = None,
    ) -> Sale:
        if not cart_items:
            raise ValueError("Cart is empty.")

        payment_method = payment_method.strip().lower()
        if payment_method not in self.ALLOWED_PAYMENT_METHODS:
            raise ValueError("Invalid payment method.")

        if discount < 0:
            raise ValueError("Discount cannot be negative.")

        with SessionLocal() as session:
            validated_items = []
            subtotal = 0.0

            for item in cart_items:
                product_id = int(item["product_id"])
                quantity = float(item["quantity"])

                if quantity <= 0:
                    raise ValueError("Quantity must be greater than zero.")

                product = session.scalar(
                    select(Product).where(Product.id == product_id)
                )
                if product is None:
                    raise ValueError("A product in the cart no longer exists.")

                if product.quantity_in_stock < quantity:
                    raise ValueError(f"Insufficient stock for {product.name}.")

                unit_price = float(product.selling_price)
                line_total = unit_price * quantity
                subtotal += line_total

                validated_items.append(
                    {
                        "product": product,
                        "quantity": quantity,
                        "unit_price": unit_price,
                        "line_total": line_total,
                    }
                )

            total = subtotal - discount
            if total < 0:
                raise ValueError("Discount cannot exceed subtotal.")

            sale = Sale(
                business_id=business_id,
                cashier_id=cashier_id,
                subtotal=subtotal,
                discount=discount,
                total=total,
                payment_method=payment_method,
                payment_status="paid",
                transaction_ref=transaction_ref,
            )

            sale_repo = SaleRepository(session)
            sale_repo.create(sale)

            movement_repo = StockMovementRepository(session)

            for entry in validated_items:
                product = entry["product"]
                quantity = entry["quantity"]

                sale_item = SaleItem(
                    sale_id=sale.id,
                    product_id=product.id,
                    quantity=quantity,
                    unit_price=entry["unit_price"],
                    line_total=entry["line_total"],
                )
                session.add(sale_item)

                product.quantity_in_stock -= quantity

                movement_repo.create(
                    product_id=product.id,
                    movement_type="sale",
                    quantity=quantity,
                    cost_price=product.buying_price,
                    selling_price=product.selling_price,
                    reference=f"SALE-{sale.id}",
                    created_by=cashier_id,
                )

            session.commit()
            session.refresh(sale)
            return sale
