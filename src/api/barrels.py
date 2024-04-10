from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    with db.engine.begin() as connection:
        for barrel in barrels_delivered:
            barrelsUpdated = connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = num_green_ml + ({barrel.ml_per_barrel} * {barrel.quantity})"))
            goldUpdated = connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold - ({barrel.price} * {barrel.quantity})"))
        
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    skuSGB = "SMALL_GREEN_BARREL"
    for barrel in wholesale_catalog:
        print(barrel, flush=True)

    with db.engine.begin() as connection:
        curGold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).first()[0]
        curGPotions = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).first()[0]

    for barrel in wholesale_catalog:
        if barrel.sku == skuSGB:
            if (curGPotions < 10):
                return [
                    {
                        "sku": "SMALL_GREEN_BARREL",
                        "quantity": min(10 - curGPotions, int(curGold / barrel.price)),
                    }
                ]
            else:
                return []
            
    return []
