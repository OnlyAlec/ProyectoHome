import os
import oracledb
import json
from dotenv import load_dotenv

load_dotenv()


class Table:
    def __init__(self, jsonData: dict | str):
        self.table: list = []
        self.alias: list = []
        self.columns: list = []
        self.values: list = []
        self.where: str = ""
        self.query: str = ""
        self.asTable: str = ""
        self.groupBy: str = ""
        if isinstance(jsonData, str):
            self.query = jsonData
        else:
            self.construct(jsonData)

    def construct(self, jsonData: dict):
        for key, value in jsonData.items():
            if key == "Tables":
                for table, alias in value.items():
                    self.table.append(table)
                    self.alias.append(alias)
            elif key == "Columns":
                if isinstance(value, list):
                    self.columns = value
                elif isinstance(value, dict):
                    for table, columns in value.items():
                        self.columns.append({table: columns})
            elif key == "Values":
                for values in value:
                    self.values.append(values)
            elif key == "Where":
                self.where = value
            elif key == "query":
                self.query = value
            elif key == "As":
                self.asTable = value
            elif key == "GroupBy":
                self.groupBy = value
            else:
                raise ValueError("Key not found!")

    def toUpper(self):
        self.table = [table.upper() for table in self.table]
        self.columns = [column.upper() for column in self.columns]

    def strTable(self):
        query = ""
        if len(self.table) == len(self.alias) == len(self.asTable):
            for table, alias, asTable in self.table, self.alias, self.asTable:
                query += f"{table}"
                if alias != "":
                    query += f" {alias}"
                if asTable != "":
                    query += f" AS {asTable}"
                query += ", "

    def strValues(self):
        return ", ".join(self.values)


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

    def existColumn(self, table: str, column: str):
        try:
            self.cursor.execute(
                f"SELECT {column} FROM {table} WHERE 1=2")
            return True
        except oracledb.DatabaseError:
            return False


class Operation:
    def __init__(self, dbDest: DB, crud: str, data: dict):
        self.db = dbDest
        self.crud = crud
        self.data = self.parseJSON(data)
        self.tablesWaiting: list = []
        self.tablesObj: list = []
        self.response: dict = {}

        try:
            self.getTables()
            if miss := self.checkObligatory():
                raise ValueError(
                    f"Missing {', '.join(miss)} in {', '.join(miss.keys())}!")
            self.execute()
        except Exception as e:
            raise e

    def checkObligatory(self):
        miss = {}
        if self.crud == "INSERT":
            need = ["table", "values"]
        elif self.crud == "UPDATE":
            need = ["table", "columns", "values", "where"]
        elif self.crud == "DELETE":
            need = ["table", "where"]
        elif self.crud == "SELECT":
            need = ["query"]
        else:
            raise ValueError("CRUD not found!")

        for table in self.tablesObj:
            miss.update({table: []})
            for field in need:
                if not field in vars(table) and (field is None or field == ""):
                    miss[table].append(field)
        return False if len(miss) > 0 else miss

    def parseJSON(self, data):
        if isinstance(data, str) and self.crud == "SELECT":
            return json.loads(data)
        if isinstance(data, dict):
            return data
        raise ValueError("Data is not valid!")

    def getTables(self):
        for data in self.data["Tables"]:
            if self.crud == "SELECT":
                self.tablesWaiting.append(data)
                d = json.dumps(self.data)
                self.tablesObj.append(Table(d))
                break
            self.tablesWaiting.append(data)
            self.tablesObj.append(Table(data))

    def execute(self):
        try:
            if self.crud == "SELECT":
                resp = self.db.cursor.execute(self.tablesObj[0].query)
                return resp

            for table in self.tablesWaiting:
                self.checkValidation(
                    self.tablesObj[self.tablesWaiting.index(table)])

        except (oracledb.DatabaseError, ValueError) as e:
            raise e

    def checkValidation(self, tableClass: Table):
        tableClass.toUpper()
        for tableName in tableClass.table:
            if not tableName in self.db.allTables:
                raise ValueError(f"Table {tableName} not exist!")

        for tableName in tableClass.table:
            for columnName in tableClass.columns:
                if not self.db.existColumn(tableName, columnName):
                    raise ValueError(
                        f"Column {columnName} not exist in table {tableName}!")

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
