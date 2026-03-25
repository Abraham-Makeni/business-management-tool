from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.product import Product


class ProductRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_all(self) -> list[Product]:
        stmt = select(Product).order_by(Product.id.desc())
        return list(self.session.scalars(stmt).all())

    def get_by_id(self, product_id: int) -> Product | None:
        return self.session.get(Product, product_id)

    def create(self, **kwargs) -> Product:
        product = Product(**kwargs)
        self.session.add(product)
        self.session.commit()
        self.session.refresh(product)
        return product

    def update(self, product: Product, **kwargs) -> Product:
        for key, value in kwargs.items():
            setattr(product, key, value)
        self.session.commit()
        self.session.refresh(product)
        return product

    def delete(self, product: Product) -> None:
        self.session.delete(product)
        self.session.commit()
