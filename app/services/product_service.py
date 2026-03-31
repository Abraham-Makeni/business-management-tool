from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database.models.product import Product
from app.database.repositories.product_repo import ProductRepository
from app.database.session import SessionLocal
from app.services.signals import app_signals


class ProductService:
    def list_products(self, business_id: int | None = None) -> list[Product]:
        with SessionLocal() as session:
            stmt = (
                select(Product)
                .options(selectinload(Product.category))
                .order_by(Product.id.desc())
            )
            if business_id is not None:
                stmt = stmt.where(Product.business_id == business_id)
            stmt = stmt.where(Product.active == True)
            return list(session.scalars(stmt).all())

    def create_product(
        self,
        business_id: int,
        name: str,
        buying_price: float,
        selling_price: float,
        quantity_in_stock: float,
        reorder_level: float,
        category_id: int | None = None,
        sku: str | None = None,
        barcode: str | None = None,
    ) -> Product:
        name = name.strip()
        if not name:
            raise ValueError("Product name is required.")

        if buying_price < 0 or selling_price < 0 or quantity_in_stock < 0 or reorder_level < 0:
            raise ValueError("Numeric values cannot be negative.")

        with SessionLocal() as session:
            repo = ProductRepository(session)
            product = repo.create(
                business_id=business_id,
                category_id=category_id,
                sku=sku or None,
                barcode=barcode or None,
                name=name,
                buying_price=buying_price,
                selling_price=selling_price,
                quantity_in_stock=quantity_in_stock,
                reorder_level=reorder_level,
            )
            app_signals.product_changed.emit()
            return product

    def update_product(
        self,
        product_id: int,
        name: str,
        buying_price: float,
        selling_price: float,
        quantity_in_stock: float,
        reorder_level: float,
        category_id: int | None = None,
        sku: str | None = None,
        barcode: str | None = None,
    ) -> Product:
        name = name.strip()
        if not name:
            raise ValueError("Product name is required.")

        if buying_price < 0 or selling_price < 0 or quantity_in_stock < 0 or reorder_level < 0:
            raise ValueError("Numeric values cannot be negative.")

        with SessionLocal() as session:
            repo = ProductRepository(session)
            product = repo.get_by_id(product_id)
            if product is None:
                raise ValueError("Product not found.")

            updated = repo.update(
                product,
                category_id=category_id,
                sku=sku or None,
                barcode=barcode or None,
                name=name,
                buying_price=buying_price,
                selling_price=selling_price,
                quantity_in_stock=quantity_in_stock,
                reorder_level=reorder_level,
            )
            app_signals.product_changed.emit()
            return updated

    def delete_product(self, product_id: int) -> None:
        with SessionLocal() as session:
            repo = ProductRepository(session)
            product = repo.get_by_id(product_id)
            if product is None:
                raise ValueError("Product not found.")
            repo.delete(product)
            app_signals.product_changed.emit()
