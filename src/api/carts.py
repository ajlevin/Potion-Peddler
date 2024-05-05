from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """
    
    with db.engine.begin() as connection:        
        metadata_obj = sqlalchemy.MetaData()
        carts = sqlalchemy.Table('carts', metadata_obj, autoload_with= db.engine)
        cart_items = sqlalchemy.Table('cart_items', metadata_obj, autoload_with= db.engine)
        potions = sqlalchemy.Table('potions', metadata_obj, autoload_with= db.engine)

        search_result = sqlalchemy.select(
            carts.c.cart_id,
            carts.c.customer_name,
            potions.c.item_sku,
            cart_items.c.quantity,
            carts.c.timestamp,
            (cart_items.c.quantity * potions.c.price).label('line_total')
        ).select_from(
            carts.join(cart_items, carts.c.cart_id == cart_items.c.cart_id)
                 .join(potions, cart_items.c.potion_id == potions.c.potion_id)
        )

        if sort_col is search_sort_options.customer_name:
            sort_parameter = search_result.c.customer_name
        elif sort_col is search_sort_options.item_sku:
            sort_parameter = search_result.c.item_sku
        elif sort_col is search_sort_options.line_item_total:
            sort_parameter = search_result.c.line_total
        elif sort_col is search_sort_options.timestamp:
            sort_parameter = search_result.c.timestamp
        else:
            raise RuntimeError("No Sort Parameter Passed")
        
        search_values = (
            sqlalchemy.select(
                search_result.c.cart_id,
                search_result.c.quantity,
                search_result.c.item_sku,
                search_result.c.line_total,
                search_result.c.timestamp,
                search_result.c.customer_name
            ).select_from(search_result)
        )

        sorted_values = search_values
        if customer_name != "":
            sorted_values = sorted_values.where(
                (search_result.c.customer_name.ilike(f"%{customer_name}%")))
        if potion_sku != "":
            sorted_values = sorted_values.where(
                (search_result.c.item_sku.ilike(f"%{potion_sku}%")))
        if sort_order == search_sort_order.desc: 
            sorted_values = sorted_values.order_by(
                sqlalchemy.desc(sort_parameter) if sort_order == search_sort_order.desc else sqlalchemy.desc(sort_parameter))

        result = connection.execute(search_values.limit(5))
        search_return = []
        for row in result:
            search_return.append(
                    {
                        "line_item_id": row.cart_id,
                        "item_sku": f"{row.quantity} {row.item_sku}",
                        "customer_name": row.customer_name,
                        "line_item_total": row.line_total,
                        "timestamp": row.timestamp,
                    })
        
        page = 0 if search_page == "" else int(search_page) * 5
        prev_page = f"{int(page/5) - 1}" if int(page/5) > 1 else ""
        next_page = f"{int(page/5) + 1}" if (connection.execute(search_values).rowcount - (page)) else ""
    
        return ({
                "previous": prev_page,
                "next": next_page,
                "results": search_return
            })


class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int

@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited the shop today?
    """
    print(customers)
    
    return "OK"


@router.post("/")
def create_cart(new_cart: Customer):
    """ """

    with db.engine.begin() as connection:
        cart_id = connection.execute(sqlalchemy.text(
            "INSERT INTO carts (customer_name) VALUES (:customer_name) RETURNING cart_id"),
            [{"customer_name": new_cart.customer_name}]).first()[0]
    
    return {"cart_id": cart_id}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """

    with db.engine.begin() as connection:
        potion_id = connection.execute(sqlalchemy.text(
            "SELECT potion_id FROM potions WHERE item_sku = :item_sku"),
            [{"item_sku": item_sku}]).first()[0]
        connection.execute(sqlalchemy.text(
            "INSERT INTO cart_items (cart_id, potion_id, quantity) VALUES (:cart_id, :potion_id, :quantity)"),
            [{"cart_id": cart_id,
              "potion_id": potion_id,
              "quantity": cart_item.quantity}])
    
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """

    totalCost = 0
    totalCount = 0

    with db.engine.begin() as connection:
        cart_items = connection.execute(sqlalchemy.text("SELECT * FROM cart_items WHERE cart_id = :cart_id"), [{"cart_id": cart_id}])
        
        for item in cart_items:
            connection.execute(sqlalchemy.text(
                """
                INSERT INTO potion_ledger (potion_id, inventory_change, order_id, order_type) 
                VALUES (:potion_id, :inventory_change, :order_id, :order_type)
                """),
                [{"potion_id": item.potion_id,
                  "inventory_change": -item.quantity,
                  "order_id": cart_id,
                  "order_type": "checkout"}])
            potionPrice = connection.execute(sqlalchemy.text(
                "SELECT price FROM potions WHERE potion_id = :potion_id"), [{"potion_id": item.potion_id}]).first()[0]
            totalCost += (item.quantity * potionPrice)
            totalCount += item.quantity
        
        connection.execute(sqlalchemy.text(
            "INSERT INTO global_ledger (gold_difference, order_id, order_type) VALUES (:totalCost, :order_id, :order_type)"), 
            [{"totalCost": totalCost,
              "order_id": cart_id,
              "order_type": "checkout"}])
        
    return {"total_potions_bought": totalCount, "total_gold_paid": totalCost}
