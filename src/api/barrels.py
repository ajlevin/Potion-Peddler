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

    # also needs fixing

    skumlMap = ["num_red_ml", "num_green_ml", "num_blue_ml", "num_dark_ml"]

    with db.engine.begin() as connection:
        for barrel in barrels_delivered:
            # Update ml:
            connection.execute(sqlalchemy.text(
                f"UPDATE global_inventory SET {skumlMap[barrel.potion_type.index(max(barrel.potion_type))]} = \
                {skumlMap[barrel.potion_type.index(max(barrel.potion_type))]} + {(barrel.ml_per_barrel * barrel.quantity)}"))
            # Update gold:
            connection.execute(sqlalchemy.text(
                f"UPDATE global_inventory SET gold = gold - ({barrel.price * barrel.quantity})"))
    
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """

    lst = []
    barrelTemp = {
        'red' : None,
        'green' : None,
        'blue' : None,
        'dark' : None}
    barrelSplit = {
        'large' : barrelTemp.copy(),
        'medium' : barrelTemp.copy(),
        'small' : barrelTemp.copy(),
        'mini' : barrelTemp.copy()
    }
    mlAsk = {
        'red' : 0,
        'green' : 0,
        'blue' : 0,
        'dark' : 0
    }
    typeIdxs = list(mlAsk.keys())

    for barrel in wholesale_catalog:
        print(barrel, flush=True)
        if barrel.ml_per_barrel == 10000:
            barrelSplit['large'][typeIdxs[barrel.potion_type.index(max(barrel.potion_type))]] = barrel
        elif barrel.ml_per_barrel == 2500:
            barrelSplit['medium'][typeIdxs[barrel.potion_type.index(max(barrel.potion_type))]] = barrel
        elif barrel.ml_per_barrel == 500:
            barrelSplit['small'][typeIdxs[barrel.potion_type.index(max(barrel.potion_type))]] = barrel
        else:
            barrelSplit['mini'][typeIdxs[barrel.potion_type.index(max(barrel.potion_type))]] = barrel
    

    with db.engine.begin() as connection:
        curGold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).first()[0]
        potionsData = connection.execute(sqlalchemy.text("SELECT * FROM potions"))
        for potion in potionsData:
            if potion.inventory == 0:
                mlAsk['red'] += potion.red_ml
                mlAsk['green'] += potion.green_ml
                mlAsk['blue'] += potion.blue_ml
                mlAsk['dark'] += potion.dark_ml
        mlAsk = dict(sorted(mlAsk.items(), key=lambda item: item[1]))

    for bType in mlAsk.keys():
        for sizedBarrel in barrelSplit.values():
            if sizedBarrel[bType] is not None and (int(int(curGold / 4) / sizedBarrel[bType].price) > 0):
                lst.append(
                    {
                        "sku": sizedBarrel[bType].sku,
                        "quantity": min(int(int(curGold / 4) / sizedBarrel[bType].price), sizedBarrel[bType].quantity),
                    }
                )
                break
        
    return lst
