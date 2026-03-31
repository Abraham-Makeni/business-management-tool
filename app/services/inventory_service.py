from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.database.models.product import Product
from app.database.repositories.stock_movement_repo import StockMovementRepository
from app.database.session import SessionLocal


class InventoryService:
    ALLOWED_MOVEMENTS = {"stock_in", "stock_out", "adjustment", "damaged", "expired", "sale", "returned"}

    def adjust_stock(
        self,
        product_id: int,
        movement_type: str,
        quantity: float,
        reference: str | None = None,
        created_by: int | None = None,
    ) -> Product:
        movement_type = movement_type.strip().lower()
        if movement_type not in self.ALLOWED_MOVEMENTS:
            raise ValueError("Invalid movement type.")

        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")

        with SessionLocal() as session:
            stmt = select(Product).where(Product.id == product_id)
            product = session.scalar(stmt)

            if product is None:
                raise ValueError("Product not found.")

            if movement_type in {"stock_in", "returned"}:
                product.quantity_in_stock += quantity
            elif movement_type in {"stock_out", "damaged", "expired", "sale"}:
                if product.quantity_in_stock < quantity:
                    raise ValueError("Insufficient stock.")
                product.quantity_in_stock -= quantity
            elif movement_type == "adjustment":
                product.quantity_in_stock = quantity

            movement_repo = StockMovementRepository(session)
            movement_repo.create(
                product_id=product.id,
                movement_type=movement_type,
                quantity=quantity,
                cost_price=product.buying_price,
                selling_price=product.selling_price,
                reference=reference,
                created_by=created_by,
            )

            session.commit()
            session.refresh(product)
            return product

    def list_recent_movements(self, limit: int = 100):
        with SessionLocal() as session:
            stmt = (
                select(Product)
                .options(selectinload(Product.category))
            )

            repo = StockMovementRepository(session)
            return repo.list_recent(limit=limit)
