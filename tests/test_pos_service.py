from sqlalchemy import select

from app.database.models.business import Business
from app.database.models.product import Product
from app.services.pos_service import POSService


def test_process_sale_decrements_stock(db_session):
    business = Business(business_name="Test Biz")
    db_session.add(business)
    db_session.commit()

    product = Product(
        business_id=business.id,
        name="Widget",
        buying_price=10.0,
        selling_price=25.0,
        quantity_in_stock=5.0,
        reorder_level=0.0,
        active=True,
    )
    db_session.add(product)
    db_session.commit()

    svc = POSService()
    sale = svc.process_sale(
        business_id=business.id,
        cart_items=[{"product_id": product.id, "quantity": 2}],
        payment_method="cash",
        discount=0.0,
        cashier_id=None,
        transaction_ref=None,
    )

    refreshed = db_session.scalar(select(Product).where(Product.id == product.id))
    assert refreshed is not None
    assert refreshed.quantity_in_stock == 3.0
    assert sale.total == 50.0


def test_process_sale_rejects_insufficient_stock(db_session):
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

    svc = POSService()
    try:
        svc.process_sale(
            business_id=business.id,
            cart_items=[{"product_id": product.id, "quantity": 2}],
            payment_method="cash",
            discount=0.0,
        )
        assert False, "Expected ValueError"
    except ValueError as e:
        assert "Insufficient stock" in str(e)


def test_process_sale_rejects_discount_exceeding_subtotal(db_session):
    business = Business(business_name="Test Biz")
    db_session.add(business)
    db_session.commit()

    product = Product(
        business_id=business.id,
        name="Widget",
        buying_price=10.0,
        selling_price=25.0,
        quantity_in_stock=10.0,
        reorder_level=0.0,
        active=True,
    )
    db_session.add(product)
    db_session.commit()

    svc = POSService()
    try:
        svc.process_sale(
            business_id=business.id,
            cart_items=[{"product_id": product.id, "quantity": 1}],
            payment_method="cash",
            discount=30.0,
        )
        assert False, "Expected ValueError"
    except ValueError as e:
        assert "Discount cannot exceed subtotal" in str(e)
