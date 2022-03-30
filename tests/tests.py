import sys
import os
import io

import unittest

import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(SCRIPT_DIR))

TEMP_DIR = ".temp"

class ColumnTypesCase(unittest.TestCase):
    def test_sql_inherit(self):
        from xmlorm.orm import ColumnType

        class Test(ColumnType):
            ...

        with self.assertRaises(TypeError):
            t = Test()

    def test_integer_type(self):
        from xmlorm.orm import Integer
        self.assertEqual(repr(Integer()), "integer")

    def test_timestamp_type(self):
        from xmlorm.orm import Timestamp
        self.assertEqual(repr(Timestamp()), "timestamp")

    def test_real_type(self):
        from xmlorm.orm import Real
        self.assertEqual(repr(Real()), "real")

    def test_text_type(self):
        from xmlorm.orm import Text
        self.assertEqual(repr(Text()), "text")

    def test_char_type(self):
        from xmlorm.orm import Char
        self.assertEqual(repr(Char(56)), "char(56)")

    def test_varchar_type(self):
        from xmlorm.orm import Varchar
        self.assertEqual(repr(Varchar(56)), "varchar(56)")


class ColumnsTestCase(unittest.TestCase):

    def test_simple(self):
        from xmlorm.orm import Column
        col = Column("name")
        self.assertEqual(repr(col), "name text")

    def test_primary_key(self):
        from xmlorm.orm import Column
        col = Column("name", primary_key=True)

        self.assertEqual (repr(col), "name text primary key")

    def test_varchar_column(self):
        from xmlorm.orm import Column, Varchar
        col = Column("name", tpe=Varchar(30), primary_key=True)

        self.assertEqual (repr(col), "name varchar(30) primary key")


    def test_char_column(self):
        from xmlorm.orm import Column, Char
        col = Column("name", tpe=Char(30), not_null=True,
            primary_key=True)

        self.assertEqual (repr(col), "name char(30) primary key not null")


class TableDeclTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(TEMP_DIR, "person.xml"), "w") as f:
            f.write("""
<person>
    <record>
        <name>John</name>
        <last_name>Doe</last_name>
        <employers>
            <employer>
                <name>Ames Research Center, NASA</name>
                <address>De France Ave, Mountain View, 
                    CA 94043, United States
                </address>
            </employer>
        </employers>
    </record>
</person>
""")

    def test_parent_pk(self):
        from xmlorm.orm import Table, Column, PrimaryKey

        with self.assertRaisesRegex(AssertionError, ("A Table with a hash key can't "
                                                     "have a primary key declared")):
            Table(name="people", 
                top_tag="person/record",
                columns=(
                    Column("name", not_null=True),
                    Column("last_name", not_null=True)
                ),
                pkey=PrimaryKey(["name", "last_name"]),
                hash_key=("name", "last_name"))

    def test_parent_pk_column(self):
        from xmlorm.orm import Table, Column
        with self.assertRaisesRegex(AssertionError, ("A Table with a hash key can't be"
                                       " declared with a Column set as a primary key")):
            Table(name="people", 
                top_tag="person/record",
                columns=(
                    Column("name", not_null=True, primary_key=True),
                    Column("last_name", not_null=True)
                ),
                hash_key=("name", "last_name"))

    def test_hash_key(self):
        from xmlorm.orm import Table, Column
        tab = Table(name="people", 
            top_tag="person/record",
            columns=(
                Column("name", not_null=True),
                Column("last_name", not_null=True)
            ),
            hash_key=("name", "last_name"))
        self.assertIn("hash_id", tab.columns)
        self.assertEqual(repr(tab.columns["hash_id"]), "hash_id text primary key not null")


    #def test_
    #    tables["employers"] = Table(name="employers",
    #            top_tag="person/record",
    #            tag_name="employers/employer",
    #            columns=(
    #                Column("name", not_null=True),
    #                Column("address")
    #            ),
    #            parent_table=tables["people"])

def setUpModule():
    try:
        shutil.rmtree(TEMP_DIR)
    except FileNotFoundError:
        pass
    os.mkdir(TEMP_DIR)

def tearDownModule():
    try:
        shutil.rmtree(TEMP_DIR)
    except FileNotFoundError:
        pass

if __name__ == "__main__":
    unittest.main()