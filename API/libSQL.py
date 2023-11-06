import os
import oracledb
from dotenv import load_dotenv

load_dotenv()


class DB:
    def __init__(self):
        self.allTables = []
        self.connection: oracledb.Connection = None
        self.cursor: oracledb.Cursor = None

        try:
            self.connect()
            self.getAllTables()
        except Exception as e:
            raise e

    def connect(self):
        if self.connection is not None:
            print("\t -> Already Connect!")
            return False

        print("Connecting to SQL...", end=" ")
        ip = os.getenv("DB_IP")
        pwd = os.getenv("DB_PASSWORD")
        userDB = os.getenv("DB_USER")

        try:
            self.connection: oracledb.Connection = oracledb.connect(
                user=str(userDB),
                password=str(pwd),
                dsn=f"{ip}/xepdb1")
            print("OK!")
            self.cursor = self.connection.cursor()
            return True
        except (oracledb.DatabaseError, oracledb.OperationalError) as e:
            print(f"Failed! -> \t {e}")
            raise e

    def getAllTables(self):
        self.cursor.execute("SELECT table_name FROM user_tables")
        self.allTables = [
            table[0] for table in self.cursor.fetchall()
        ]

    def columnsUpper(self, data: dict | list):
        if isinstance(data, dict):
            for table in data.copy():
                data[table.upper()] = data.pop(table)
        elif isinstance(data, list):
            for table in data.copy():
                data[data.index(table)] = table.upper()


class Operation:
    def __init__(self, dbDest: DB, crud: str, data: dict, condition=None):
        self.db = dbDest
        self.crud = crud
        self.tables = data
        self.order = {}
        self.condition = condition
        self.error = self.execute()

    def execute(self):
        e = self.validation(self.tables)
        if e != "":
            return e
        getattr(self, self.crud.lower())()
        self.db.connection.commit()

    def validation(self, data: dict):
        self.db.columnsUpper(data)
        # ^ Para UPDATE y DELETE valida que exista la condicion
        if self.crud in ["UPDATE", "DELETE"]:
            if self.condition is None:
                return "Condition is required for this operation!"
        #! Valida si existen las tablas y columnas
        for table in data:
            if not table in self.db.allTables:
                return f"Table {table} not exist!"

            for column in data[table]:
                if not self.existColumn(table, column):
                    return f"Column {column} not exist!"

        # ^ Solo INSERT
        if self.crud == "INSERT":
            #! Ordena las tablas para insertar primero en las tablas hijas
            self.orderTables(self.tables)

            #! Verifica si los datos recibidos sirven para insertar o existen en la db
            lastTableInsert = ""
            for table in self.order.items():
                if lastTableInsert == table[0]:
                    continue
                for child in table[1]:
                    if self.tables[table[0]][child] is None:
                        if child.split("_")[1].upper() not in self.tables:
                            return "Data for table {child} is required!"
                        childName = child.split("_")[1].upper()
                        dictData = {childName: self.tables[childName]}
                        try:
                            Operation(self.db, self.crud, dictData)
                            self.tables[table[0]][child] = self.recoverLastID(
                                childName)
                            self.tables.pop(childName)
                            lastTableInsert = childName
                        except oracledb.DatabaseError as e:
                            raise e
            return ""

    def existColumn(self, table: str, column: str):
        try:
            self.db.cursor.execute(
                f"SELECT {column} FROM {table} WHERE 1=2")
            return True
        except oracledb.DatabaseError:
            return False

    def orderTables(self, data: dict):
        for table in data.keys():
            tablesChild = []
            for column in data[table]:
                if column.find("cve_") != -1 and column.find("tipo") == -1:
                    tablesChild.append(column)
            self.order[table] = tablesChild

    def recoverLastID(self, table: str):
        self.db.cursor.execute(
            f"SELECT MAX(ID_{table}) FROM {table}")
        return self.db.cursor.fetchone()[0]

    def insert(self):
        for table in self.tables:
            query = f"INSERT INTO {table} VALUES ("
            for values in self.tables[table].values():
                if isinstance(values, str):
                    query += f"'{values}', "
                elif isinstance(values, int):
                    query += f"{values}, "
            query = query[:-2] + ")"
            try:
                print("Inserting...", end=" ")
                self.db.cursor.execute(query)
                print("OK!")
            except oracledb.DatabaseError as e:
                raise e

    def update(self):
        for table in self.tables:
            query = f"UPDATE {table} SET "
            for column, values in self.tables[table]:
                if column == "condition":
                    continue
                if isinstance(values, str):
                    query += f"{column}='{values}', "
                elif isinstance(values, int):
                    query += f"{column}={values}, "
            query += f"WHERE {self.condition}"
            try:
                print("Updating...", end=" ")
                self.db.cursor.execute(query)
                print("OK!")
            except oracledb.DatabaseError as e:
                raise e

    def delete(self):
        for table in self.tables:
            query = f"DELETE FROM {table} WHERE {self.condition}"
            try:
                print("Deleting...", end=" ")
                self.db.cursor.execute(query)
                print("OK!")
            except oracledb.DatabaseError as e:
                raise e

    def select(self):
        for table in self.tables:
            query = "SELECT "
            for values in self.tables[table].values():
                if values is None:
                    query += "*  "
                    break
                query += f"'{values}', "
            query = query[:-2] + f"FROM {table}"
            try:
                print("Selecting...", end=" ")
                self.db.cursor.execute(query)
                print("OK!")
            except oracledb.DatabaseError as e:
                raise e
