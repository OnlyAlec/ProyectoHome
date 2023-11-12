import os

from pyparsing import col
import json
import oracledb
from dotenv import load_dotenv

load_dotenv()


class Table:
    def __init__(self, jsonData: dict | str, table: str = "", query: str = ""):
        self.table: str | list = table
        self.alias: list = []
        self.columns: list = []
        self.values: list = []
        self.where: str = ""
        self.query: str = query
        if not query:
            if isinstance(jsonData, str):
                self.query = jsonData
            else:
                self.construct(jsonData)

    def construct(self, jsonData: dict):
        for column, value in jsonData.items():
            if column == "alias":
                self.alias = value
            elif column == "where":
                self.where = value
            elif column == "query":
                # !Puede que solo me manden el query ya hecho pero no sabemos
                table = Table(self.table, value)
            else:
                if column == "null":
                    self.columns.append(None)
                else:
                    self.columns.append(column)
                self.values.append(value)
            # &Es es por si mandan la estructura de la tabla en un JSON y no el query
            # if key == "Tables":
            #     for table, alias in value.items():
            #         self.table.append(table)
            #         self.alias.append(alias)
            # elif key == "Columns":
            #     elif isinstance(value, dict):
            #         for table, columns in value.items():
            #             self.columns.append({table: columns})
            # elif key == "Values":
            #     for values in value:
            #         self.values.append(values)
            # else:
            #     raise ValueError("Key not found!")

    def toUpper(self):
        self.table = [table.upper() for table in self.table] if isinstance(
            self.table, list) else self.table.upper()
        self.columns = [column.upper() for column in self.columns] if isinstance(
            self.columns, list) else self.columns.upper()

    def strTable(self):
        query = ""
        if len(self.table) == len(self.alias):
            for table, alias, asTable in self.table, self.alias:
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
        self.data = data
        self.tablesWaiting: list = []
        self.tablesObj: list = []
        self.response: list = []

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
        if self.crud == "SELECT":
            return False

        if self.crud == "INSERT":
            need = ["table", "values"]
        elif self.crud == "UPDATE":
            need = ["table", "columns", "values", "where"]
        elif self.crud == "DELETE":
            need = ["table", "where"]
        else:
            raise ValueError("CRUD not found!")

        for table in self.tablesObj:
            miss.update({table: []})
            for field in need:
                if not field in vars(table) and (field is None or field == ""):
                    miss[table].append(field)
        return False if len(miss) > 0 else miss

    # ! Not used
    def parseJSON(self, data):
        if isinstance(data, str) and self.crud == "SELECT":
            return json.loads(data)
        if isinstance(data, dict):
            return data
        raise ValueError("Data is not valid!")

    def getTables(self):
        if isinstance(self.data, str):
            return

        for table, data in self.data.items():
            self.tablesWaiting.append(table.upper())
            self.tablesObj.append(Table(data, table.upper()))

    def orderTables(self, table: str):
        order = False
        tableObject: Table = self.tablesObj[self.tablesWaiting.index(table)]
        for column in tableObject.columns:
            if column.find("CVE_") != -1:
                # and column.find("TIPO") == -1
                childName = column.split("_")[1]
                indexColumn = tableObject.columns.index(column)
                if tableObject.values[indexColumn] is not None:
                    continue

                if childName in self.tablesWaiting:
                    indexPos = self.tablesWaiting.index(table)
                    self.tablesWaiting.remove(childName)
                    self.tablesWaiting.insert(indexPos, childName)
                    order = True
                else:
                    raise ValueError(
                        f"Table {childName} not found in data to insert!")
        if order:
            newOrder = []
            for order in self.tablesWaiting:
                for i, obj in enumerate(self.tablesObj):
                    if obj.table == order:
                        newOrder.append(self.tablesObj[i])
                        self.tablesObj.pop(i)
                        break
            self.tablesObj = newOrder

    def execute(self):
        try:
            if self.crud == "SELECT" and isinstance(self.data, str):
                self.db.cursor.execute(self.data)
                self.response = self.db.cursor.fetchall()
                return

            for table in self.tablesWaiting:
                self.checkValidation(
                    self.tablesObj[self.tablesWaiting.index(table)])

            for table in self.tablesWaiting.copy():
                self.orderTables(table)

            for table in self.tablesObj:
                getattr(self, self.crud.lower())(table)
                self.db.connection.commit()
        except (oracledb.DatabaseError, ValueError) as e:
            raise e

    def checkValidation(self, tableClass: Table):
        tableClass.toUpper()
        tables = tableClass.table
        columns = tableClass.columns

        if isinstance(tables, str) and not tables in self.db.allTables:
            raise ValueError(f"Table {tables} not exist!")

        if isinstance(tableClass.table, list):
            for tableName in tables:
                if not tableName in self.db.allTables:
                    raise ValueError(f"Table {tableName} not exist!")

        if isinstance(tables, str) and isinstance(columns, str) and not self.db.existColumn(tables, columns):
            raise ValueError(
                f"Column {columns} not exist in table {tables}!")

        if isinstance(tableClass.table, list):
            for tableName in tables:
                for columnName in columns:
                    if not self.db.existColumn(tableName, columnName):
                        raise ValueError(
                            f"Column {columnName} not exist in table {tableName}!")

    def getIDChild(self, nameColumn: str):
        if nameColumn.find("CVE_") == -1:
            return None

        nameColumn = nameColumn.split("_")[1]
        query = f"SELECT MAX(ID_{nameColumn}) FROM {nameColumn}"
        try:
            self.db.cursor.execute(query)
            ID = self.db.cursor.fetchone()[0]
            return ID
        except oracledb.DatabaseError as e:
            raise e

    def insert(self, table: Table):
        query = f"INSERT INTO {table.table}("
        valuesQuery = " VALUES("
        for column, values in zip(table.columns, table.values):
            query += f"{column}, "
            if isinstance(values, str):
                valuesQuery += f"'{values}', "
            elif isinstance(values, int):
                valuesQuery += f"{values}, "
            else:
                ID = self.getIDChild(column)
                if ID is None:
                    valuesQuery += "NULL, "
                else:
                    valuesQuery += f"{ID}, "
        valuesQuery = valuesQuery[:-2] + ")"
        query = query[:-2] + ")" + valuesQuery
        try:
            print("Inserting...", end=" ")
            self.db.cursor.execute(query)
            print("OK!")
        except oracledb.DatabaseError as e:
            e.args[0].message = f"{
                e.args[0].message} en tabla {table.table}"
            raise e

    def update(self, table: Table):
        query = f"UPDATE {table.table} SET "
        for column, values in zip(table.columns, table.values):
            if column == "condition":
                continue
            if isinstance(values, str):
                query += f"{column}='{values}', "
            elif isinstance(values, int):
                query += f"{column}={values}, "
        query = query[:-2]
        query += f" WHERE {table.where}"
        try:
            print("Updating...", end=" ")
            self.db.cursor.execute(query)
            print("OK!")
        except oracledb.DatabaseError as e:
            e.args[0].message = f"{
                e.args[0].message} en tabla {table.table}"
            raise e

    def delete(self, table: Table):
        query = f"DELETE FROM {table.table} WHERE {table.where}"
        try:
            print("Deleting...", end=" ")
            self.db.cursor.execute(query)
            print("OK!")
        except oracledb.DatabaseError as e:
            e.args[0].message = f"{
                e.args[0].message} en tabla {table.table}"
            raise e
