from utils.psql._base import *

@dataclasses.dataclass(slots = True)
class UserBadge(_BaseSQLObject):
    '''Represent an entry in the `UserEquipment` table along with possible operations related to the table.
    
    Note that `badge_requirement` is a read-only attribute; it doesn't matter if you try to update it, it'll be ignored because it doesn't belong to this table.
    '''

    user_id: int
    badge_id: str
    badge_progress: int = 0

    badge_requirement: int = 0

    _tbl_name: t.ClassVar[str] = "Users_Badges"
    _PREVENT_UPDATE: t.ClassVar[tuple[str]] = ("user_id", "badge_id", "badge_requirement")

    @classmethod
    async def fetch_all_where(cls, conn: asyncpg.Connection, *, as_dict: bool = False, where: t.Callable[[t.Self | dict], bool] = lambda r: True) -> list[t.Self] | list[dict] | list[None]:
        query = """
            SELECT Users_Badges.*, Badges.requirement AS badge_requirement FROM Users_Badges
                INNER JOIN Badges
                ON Users_Badges.badge_id = Badges.id;
        """
        return await _get_all(conn, query, where = where, result_type = UserBadge if not as_dict else dict)
    @staticmethod
    async def fetch_user_badges(conn: asyncpg.Connection, user_id: int, *, as_dict: bool = False):
        query = f"""
            SELECT Users_Badges.*, Badges.requirement AS badge_requirement FROM Users_Badges
                INNER JOIN Badges
                ON Users_Badges.badge_id = Badges.id
            WHERE user_id = {user_id};
        """

        return await _get_all(conn, query, result_type = UserBadge if not as_dict else dict)
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
            The attributes to find, such as `id = value`. You must provide the following kw: `user_id: int`, `badge_id: str`.

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
        _badge_id = kwargs["badge_id"]
        query = """
            SELECT Users_Badges.*, Badges.requirement AS badge_requirement FROM Users_Badges
                INNER JOIN Badges
                ON Users_Badges.badge_id = Badges.id
            WHERE user_id = ($1) AND badge_id = ($2);
        """

        return await _get_one(conn, query, _user_id, _badge_id, result_type = UserBadge if not as_dict else dict)
    @classmethod
    async def insert_one(conn: asyncpg.Connection, ubadge: t.Self):
        query = insert_into_query("Users_Badges", len(UserBadge.__slots__) - 1)

        return await run_and_return_count(conn, query, ubadge.user_id, ubadge.badge_id, ubadge.badge_progress)
    @staticmethod
    async def add(conn: asyncpg.Connection, ubadge: t.Self):
        query = """
            INSERT INTO Users_Badges
            VALUES ($1, $2, $3) ON CONFLICT DO NOTHING;
        """
        return await run_and_return_count(conn, query, ubadge.user_id, ubadge.badge_id, ubadge.badge_progress)
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
            The attributes to find, such as `id = value`. You must provide the following kw: `user_id: int`, `badge_id: str`.

        Returns
        -------
        int
            The amount of entries updated.
        
        Raises
        ------
        KeyError
            The needed kw is not present in `**kwargs`.
        '''
        check = await super(UserBadge, cls).update_column(conn, column_value_pair, **kwargs)
        if not check:
            return 0
        
        if len(column_value_pair) < 1:
            return 0
        _user_id = kwargs["user_id"]
        _badge_id = kwargs["badge_id"]
        
        query, index = update_query(UserBadge._tbl_name, column_value_pair.keys())
        query += f"WHERE user_id = (${index}) AND badge_id = (${index + 1});"
        return await run_and_return_count(conn, query, *(column_value_pair.values()), _user_id, _badge_id)
    @classmethod
    async def update(conn: asyncpg.Connection, ubadge: t.Self) -> int:
        '''Update an entry based on the provided object, or insert if it's not found.

        This function calls `fetch_one()` internally, causing an overhead.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        ubadge : t.Self
            The object to update/insert.

        Returns
        -------
        int
            The number of entries affected.
        '''
        existed_badge = await UserBadge.fetch_one(conn, user_id = ubadge.user_id, badge_id = ubadge.badge_id)
        if not existed_badge:
            return await UserBadge.insert_one(conn, ubadge)
        else:
            diff_col = {}
            for col in existed_badge.__slots__:
                if getattr(existed_badge, col) != getattr(ubadge, col):
                    diff_col[col] = getattr(ubadge, col)
            
            return await UserBadge.update_column(conn, diff_col, user_id = ubadge.user_id, badge_id = ubadge.badge_id)
    @staticmethod
    async def add_progress(conn: asyncpg.Connection, user_id: int, badge_id: str, progress: int = 1):
        existing_badge = await UserBadge.fetch_one(conn, user_id = user_id, badge_id = badge_id)
        if not existing_badge:
            return await UserBadge.insert_one(conn, UserBadge(user_id, badge_id, progress))
        
        existing_badge.badge_progress += progress
        return await UserBadge.update_column(conn, {"badge_progress": existing_badge.badge_progress}, user_id = user_id, badge_id = badge_id)
    def completed(self):
        return self.badge_progress >= self.badge_requirement
