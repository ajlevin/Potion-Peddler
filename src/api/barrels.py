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
            barrelsUpdated = connection.execute(sqlalchemy.text(
                f"UPDATE global_inventory SET num_green_ml = num_green_ml + ({barrel.ml_per_barrel} * {barrel.quantity})"))
            goldUpdated = connection.execute(sqlalchemy.text(
                f"UPDATE global_inventory SET gold = gold - ({barrel.price} * {barrel.quantity})"))
        
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    skuSRB = "SMALL_RED_BARREL"
    skuSGB = "SMALL_GREEN_BARREL"
    skuSBB = "SMALL_BLUE_BARREL"

    for barrel in wholesale_catalog:
        print(barrel, flush=True)

    with db.engine.begin() as connection:
        curGold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).first()[0]
        curRPotions = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory")).first()[0]
        curGPotions = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).first()[0]
        curBPotions = connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory")).first()[0]

    for barrel in wholesale_catalog:
        if barrel.sku == skuSRB:
            if (curRPotions < 10):
                return [
                    {
                        "sku": "SMALL_GREEN_BARREL",
                        "quantity": min(10 - curRPotions, int((curGold / 3) / barrel.price)),
                    }
                ]
        elif barrel.sku == skuSGB:
            if (curGPotions < 10):
                return [
                    {
                        "sku": "SMALL_GREEN_BARREL",
                        "quantity": min(10 - curGPotions, int((curGold / 3) / barrel.price)),
                    }
                ]
        elif barrel.sku == skuSBB:
            if (curBPotions < 10):
                return [
                    {
                        "sku": "SMALL_GREEN_BARREL",
                        "quantity": min(10 - curBPotions, int((curGold / 3) / barrel.price)),
                    }
                ]
            
    return []
