from datetime import datetime, time

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.database.models.expense import Expense
from app.database.models.product import Product
from app.database.models.sale import Sale
from app.database.models.sale_item import SaleItem
from app.database.models.stock_movement import StockMovement
from app.database.session import SessionLocal


class ReportingService:
    def get_daily_sales_summary(self, business_id: int) -> dict:
        today_start = datetime.combine(datetime.now().date(), time.min)

        with SessionLocal() as session:
            total_sales = session.scalar(
                select(func.coalesce(func.sum(Sale.total), 0.0)).where(
                    Sale.business_id == business_id,
                    Sale.created_at >= today_start,
                )
            ) or 0.0

            transaction_count = session.scalar(
                select(func.count(Sale.id)).where(
                    Sale.business_id == business_id,
                    Sale.created_at >= today_start,
                )
            ) or 0

            total_expenses = session.scalar(
                select(func.coalesce(func.sum(Expense.amount), 0.0)).where(
                    Expense.business_id == business_id,
                    Expense.created_at >= today_start,
                )
            ) or 0.0

        return {
            "total_sales": float(total_sales),
            "transaction_count": int(transaction_count),
            "total_expenses": float(total_expenses),
            "estimated_balance": float(total_sales) - float(total_expenses),
        }

    def get_low_stock_products(self, business_id: int) -> list:
        with SessionLocal() as session:
            stmt = (
                select(Product)
                .where(
                    Product.business_id == business_id,
                    Product.active == True,
                    Product.quantity_in_stock <= Product.reorder_level,
                )
                .order_by(Product.quantity_in_stock.asc(), Product.name.asc())
            )
            return list(session.scalars(stmt).all())

    def get_recent_stock_movements(self, limit: int = 100) -> list:
        with SessionLocal() as session:
            stmt = (
                select(StockMovement)
                .order_by(StockMovement.created_at.desc(), StockMovement.id.desc())
                .limit(limit)
            )
            return list(session.scalars(stmt).all())

    def get_expenses_by_category(self, business_id: int) -> list:
        with SessionLocal() as session:
            stmt = (
                select(
                    Expense.category,
                    func.coalesce(func.sum(Expense.amount), 0.0).label("total_amount"),
                )
                .where(Expense.business_id == business_id)
                .group_by(Expense.category)
                .order_by(func.sum(Expense.amount).desc())
            )

            rows = session.execute(stmt).all()

        return [
            {
                "category": row.category,
                "total_amount": float(row.total_amount),
            }
            for row in rows
        ]

    def get_top_selling_items(self, business_id: int, limit: int = 10) -> list:
        with SessionLocal() as session:
            stmt = (
                select(
                    Product.name,
                    func.coalesce(func.sum(SaleItem.quantity), 0.0).label("qty_sold"),
                    func.coalesce(func.sum(SaleItem.line_total), 0.0).label("sales_amount"),
                )
                .join(SaleItem, SaleItem.product_id == Product.id)
                .join(Sale, Sale.id == SaleItem.sale_id)
                .where(Sale.business_id == business_id)
                .group_by(Product.name)
                .order_by(func.sum(SaleItem.quantity).desc())
                .limit(limit)
            )

            rows = session.execute(stmt).all()

        return [
            {
                "name": row.name,
                "qty_sold": float(row.qty_sold),
                "sales_amount": float(row.sales_amount),
            }
            for row in rows
        ]
