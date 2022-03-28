import sys
import os
import io

import unittest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(SCRIPT_DIR))


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

if __name__ == "__main__":
    unittest.main()