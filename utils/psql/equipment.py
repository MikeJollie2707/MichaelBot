from utils.psql._base import *
from utils.psql.inventory import Inventory
from utils.psql.item import Item

@dataclasses.dataclass(slots = True)
class Equipment(_BaseSQLObject):
    '''Represent an entry in the `UserEquipment` table along with possible operations related to the table.'''

    user_id: int
    item_id: str
    eq_type: str
    remain_durability: int
    
    _tbl_name: t.ClassVar[str] = "UserEquipment"
    _PREVENT_UPDATE: t.ClassVar[tuple[str]] = ("user_id", "item_id", "eq_type")
    __EQUIPMENT_TYPE = ("_sword", "_pickaxe", "_axe", "_potion")

    @classmethod
    async def fetch_all_where(cls, conn: asyncpg.Connection, *, as_dict: bool = False, where: t.Callable[[t.Self], bool] = lambda r: True) -> list[t.Self] | list[dict] | list[None]:
        query = """
            SELECT * FROM UserEquipment;
        """
        return await _get_all(conn, query, where = where, result_type = Equipment if not as_dict else dict)
    @classmethod
    async def fetch_one(cls, conn: asyncpg.Connection, *, as_dict: bool = False, **kwargs) -> t.Self | dict | None:
        '''Fetch one entry in the table that matches the condition.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        as_dict : bool, optional
            Whether the result should be in the `dict` or in `Self`, by default False
        **kwargs
            The attributes to find, such as `id = value`. You must provide the following kw: `user_id: int`, `item_id: str`.

        Returns
        -------
        t.Self | dict | None
            Either the object itself or `dict`, depending on `as_dict`. If not existed, `None` is returned.
        
        Raises
        ------
        KeyError
            The needed keyword is not present in `**kwargs`.
        '''
        _user_id = kwargs["user_id"]
        _item_id = kwargs["item_id"]
        query = """
            SELECT * FROM UserEquipment
            WHERE user_id = ($1) AND item_id = ($2);
        """

        return await _get_one(conn, query, _user_id, _item_id, result_type = Equipment if not as_dict else dict)
    @staticmethod
    async def fetch_equipment(conn: asyncpg.Connection, *, as_dict: bool = False, **kwargs) -> t.Self | dict | None:
        '''Fetch one entry in the table based on the type of equipment.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        as_dict : bool, optional
            Whether the result should be in the `dict` or in `Self`, by default False
        **kwargs
            The attributes to find, such as `id = value`. You must provide the following kw: `user_id: int`, `eq_type: str`.

        Returns
        -------
        t.Self | dict | None
            Either the object itself or `dict`, depending on `as_dict`. If not existed, `None` is returned.
        
        Raises
        ------
        KeyError
            The needed keyword is not present in `**kwargs`.
        '''
        _user_id = kwargs["user_id"]
        _eq_type = kwargs["eq_type"]
        query = """
            SELECT * FROM UserEquipment
            WHERE user_id = ($1) AND eq_type = ($2);
        """

        return await _get_one(conn, query, _user_id, _eq_type, result_type = Equipment if not as_dict else dict)
    @staticmethod
    async def fetch_user_equipments(conn: asyncpg.Connection, user_id: int, *, as_dict: bool = False) -> list[t.Self] | list[dict] | list[None]:
        return await Equipment.fetch_all_where(conn, where = lambda r: r.user_id == user_id, as_dict = as_dict)
    @staticmethod
    async def fetch_user_potions(conn: asyncpg.Connection, user_id: int, *, as_dict: bool = False) -> list[t.Self] | list[dict] | list[None]:
        return await Equipment.fetch_all_where(conn, where = lambda r: Equipment.is_potion(r.item_id) and r.user_id == user_id, as_dict = as_dict)
    @staticmethod
    async def transfer_from_inventory(conn: asyncpg.Connection, inventory: Inventory) -> int:
        '''Transfer an equipment from the inventory.

        Warnings
        --------
        This does not check whether the user already has that equipment. 
        This must be checked by the user, otherwise an `asyncpg.UniqueViolationError` might be raised.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        inventory : Inventory
            The inventory wrapping the equipment.

        Returns
        -------
        int
            The number of entries affected. Should be 1 or 0.
        
        Raises
        ------
        asyncpg.UniqueViolationError
            The unique constraint on `(user_id, eq_type)` is violated.
        '''
        is_equipment = False
        for eq_type in Equipment.__EQUIPMENT_TYPE:
            if eq_type in inventory.item_id:
                is_equipment = True
                item = await Item.fetch_one(conn, id = inventory.item_id)
                equipment = Equipment(inventory.user_id, inventory.item_id, eq_type, item.durability)
                break
        
        if not is_equipment:
            return 0
        
        async with conn.transaction():
            status = await Inventory.remove(conn, inventory.user_id, inventory.item_id)
            if status == 0:
                return 0
            
            # TODO: Add a check to see if the same equipment type is already there.
            return await Equipment.insert_one(conn, equipment)
    @classmethod
    async def delete(cls, conn: asyncpg.Connection, **kwargs) -> int:
        '''Delete an entry from the table.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        **kwargs : dict, optional
            The attributes to find, such as `id = value`. You must provide the following kw: `user_id: int`, `item_id: str`.
        
        Returns
        -------
        int
            The amount of entries deleted.

        Raises
        ------
        KeyError
            The needed keyword is not present in `**kwargs`.
        '''
        _user_id = kwargs["user_id"]
        _item_id = kwargs["item_id"]
        query = """
            DELETE FROM UserEquipment
            WHERE user_id = ($1) AND item_id = ($2);
        """

        return await run_and_return_count(conn, query, _user_id, _item_id)
    @staticmethod
    async def delete_entries(conn: asyncpg.Connection, equipments: list[t.Self]):
        async with conn.transaction():
            for equipment in equipments:
                await Equipment.delete(conn, equipment.user_id, equipment.item_id)
    @classmethod
    async def update_column(cls, conn: asyncpg.Connection, column_value_pair: dict[str, t.Any], **kwargs) -> int:
        '''Update specified columns with new value.

        Warnings
        --------
        If a column is in `_PREVENT_UPDATE` (usually primary keys), the function will not do anything. To update such columns, use raw SQL.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        column_value_pair : dict[str, t.Any]
            The column name and the new value to update with.
        **kwargs : dict, optional
            The attributes to find, such as `id = value`. You must provide the following kw: `user_id: int`, `item_id: str`.

        Returns
        -------
        int
            The amount of entries updated.
        
        Raises
        ------
        KeyError
            The needed kw is not present in `**kwargs`.
        '''
        check = await super(Equipment, cls).update_column(conn, column_value_pair, **kwargs)
        if not check:
            return 0

        if len(column_value_pair) < 1:
            return 0
        _user_id = kwargs["user_id"]
        _item_id = kwargs["item_id"]

        query, index = update_query(Equipment._tbl_name, column_value_pair.keys())
        query += f"WHERE user_id = (${index}) AND item_id = (${index + 1});"
        return await run_and_return_count(conn, query, *(column_value_pair.values()), _user_id, _item_id)
    @staticmethod
    async def update_durability(conn: asyncpg.Connection, user_id: int, item_id: str, new_durability: int) -> int:
        '''Update an equipment's durability and remove if needed.'''
        
        if new_durability <= 0:
            return await Equipment.delete(conn, user_id = user_id, item_id = item_id)
        return await Equipment.update_column(conn, {"remain_durability": new_durability}, user_id = user_id, item_id = item_id)
    @staticmethod
    def is_equipment(item_id: str) -> bool:
        '''Check if the item is an equipment or not.

        Parameters
        ----------
        item_id : str
            The item's id to check.

        Returns
        -------
        bool
            Whether the item is an equipment or not.
        '''
        for eq_type in Equipment.__EQUIPMENT_TYPE:
            if eq_type in item_id:
                return True
        return False
    @staticmethod
    def is_true_equipment(item_id: str) -> bool:
        return Equipment.is_equipment(item_id) and not Equipment.is_potion(item_id)
    @staticmethod
    def is_potion(item_id: str) -> bool:
        return "_potion" in item_id
    @staticmethod
    def get_equipment_type(item_id: str) -> str | None:
        '''Return the equipment type of the equipment.

        Parameters
        ----------
        item_id : str
            The item's id.

        Returns
        -------
        str | None
            The equipment type of the equipment, or `None` if it is not an equipment.
        '''
        if not Equipment.is_equipment(item_id):
            return None
        
        return '_' + item_id.split('_')[-1]
