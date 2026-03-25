from app.database.models.sale import Sale
from sqlalchemy.orm import Session


class SaleRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, sale: Sale) -> Sale:
        self.session.add(sale)
        self.session.flush()
        self.session.refresh(sale)
        return sale
