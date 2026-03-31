from sqlalchemy import select

from app.database.models.business import Business
from app.database.models.product import Product
from app.services.inventory_service import InventoryService


def test_adjust_stock_stock_in_increases(db_session):
    business = Business(business_name="Test Biz")
    db_session.add(business)
    db_session.commit()

    product = Product(
        business_id=business.id,
        name="Widget",
        buying_price=10.0,
        selling_price=25.0,
        quantity_in_stock=0.0,
        reorder_level=0.0,
        active=True,
    )
    db_session.add(product)
    db_session.commit()

    svc = InventoryService()
    svc.adjust_stock(product_id=product.id, movement_type="stock_in", quantity=5.0)

    refreshed = db_session.scalar(select(Product).where(Product.id == product.id))
    assert refreshed is not None
    assert refreshed.quantity_in_stock == 5.0


def test_adjust_stock_stock_out_rejects_insufficient(db_session):
    business = Business(business_name="Test Biz")
    db_session.add(business)
    db_session.commit()

    product = Product(
        business_id=business.id,
        name="Widget",
        buying_price=10.0,
        selling_price=25.0,
        quantity_in_stock=1.0,
        reorder_level=0.0,
        active=True,
    )
    db_session.add(product)
    db_session.commit()

    svc = InventoryService()
    try:
        svc.adjust_stock(product_id=product.id, movement_type="stock_out", quantity=2.0)
        assert False, "Expected ValueError"
    except ValueError as e:
        assert "Insufficient stock" in str(e)

