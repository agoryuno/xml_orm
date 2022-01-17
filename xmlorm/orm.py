"""
A primitive object relational mapper developed to upload a specific
dataset into a DB. This ORM, however, is general enough for use with
any XML datasets. 

It is designed to translate XML into SQL and allows the user to 
declare "embedded" tables - tables with records in XML tags inside
XML tags for the records of a higher level table.

For example the following XML snippet, contained in a file named
"people.xml":

```
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
```

Can be declared as two DB tables:

```
from orm import Table, Column, PrimaryKey

tables = {}

tables["people"] = Table(name="people", 
    top_tag="person/record",
    columns=(
        Column("name", not_null=True),
        Column("last_name", not_null=True)
    ),
    hash_key=("name", "last_name")))

tables["employers"] = Table(name="employers",
    top_tag="person/record",
    tag_name="employers/employer",
    columns=(
        Column("name", not_null=True),
        Column("address")
    ),
    parent_table=tables["people"])
```

Here the 'employers' table is linked with the 'people' table via a 
foreign key 'parent_hash', which is automatically added to 'employers'
and points to column 'hash_id', which is automatically created in
'people' and filled with values generated from the contents of the
columns specified by name in the 'hash_key' argument.

The 'hash_key' value is generated as an SHA256 hash 
(using hashlib.sha256) of the column values converted to string and 
concatenated together.


## Changing the name of the XML file

By default the name of the XML file, containing a table, is presumed
to be the same as the name of the table itself. To change the file name
simply assign a new name to 'table.filename' after the table object is
instantiated.


## Generating CREATE and reading data

Once a table object is instantiated you can generate SQL to add it to 
a DB by simply triggering the object's __repr__ method in any convenient
way, for instance simply with: f"{table}"

The data for the table can be read from the corresponding XML file by
calling:

```
table.read_table(data_dir)
```

where data_dir is the path to the directory containing the XML file.
"""

from hashlib import sha256
from xml.etree import ElementTree

TOP_LEVEL_TAG = "DATA_RECORDS/DATA_RECORD"

class Integer:
    def __repr__(self):
        return "integer"

class Timestamp:
    def __repr__(self):
        return "timestamp"

class Real:
    def __repr__(self):
        return "real"

class Text:
    def __repr__(self):
        return "text"


class Column:
    """
    Defines a column in a table.
    tpe - column type, one of Integer, Timestamp, Real or Text 
    (Text by default)
    """

    def __init__(self, name, tpe=None, not_null=False, primary_key=False):
        self.name = name
        self.type = tpe or Text()
        self.is_not_null = not_null
        self.is_primary_key = primary_key

    def __repr__(self):
        pk = {True : " primary key", False: ""}[self.is_primary_key]
        not_null = {True : " not null", False: ""}[self.is_not_null]
        return f"{self.name} {self.type}{pk}{not_null}"

class Table:
    """
    Contains all parts of a table definition.

    name - name of the table (string)
    columns - an iterable containing Column objects
    top_tag - an XPath string, pointing to the tag containing records
              for the top level table
    fkeys - (optional) an iterable containing ForeignKey
            objects
    pkey - (optional) a composite PrimaryKey
    parent_table - (optional) a "parent" Table object for tables
                    that are included inside a tag for a higher level
                    table. If this is set then *hash_key* must be set
                    for the parent table.
    hash_key - (optional) must be present if the table has "children". 
               An iterable containing column names that comprise a 
               composite primary key that is constructed as a hash of 
               the columns' values. The key is constructed automatically 
               and named "hash_id". An InvalidColumnName exception is 
               raised if a Column named "hash_id" is included in a 
               "parent" table definition.
    tag_name - (optional) Only relevant for "child" tables. If set then 
               its' value will be used as the name of the tag containing
               records for the table. If not set then the tag name is 
               assumed to be the same as the name of the table.
               
    """

    def __init__(self, name, columns, top_tag, fkeys=None, pkey=None,
        parent_table=None, hash_key=None, tag_name=None):
        self.name = name

        self.top_tag = top_tag
        self.__filename = f"{self.name}.xml"
        if parent_table:
            self.__filename = None

            assert tag_name, ("Argument tag_name cannot be None if"
                " parent_table is set.")
        self.columns = {c.name : c for c in columns}
        fkeys = fkeys or []
        self.foreign_keys = tuple(fk for fk in fkeys)
        self.primary_key = pkey
        self.parent_table = parent_table
        self.hash_key = hash_key
        self.tag_name = tag_name
        self.__enforce_hashkey()
        self.__enforce_parent_hash()

    @property
    def filename(self):
        if self.parent_table:
            return self.parent_table.filename
        return self.__filename

    @filename.setter
    def filename(self, fname):
        if not self.parent_table:
            self.__filename = fname 


    def __repr__(self):
        cols = ',\n'.join([f"  {c}" for c in self.columns.values()])

        s = f"create table if not exists {self.name} ({cols}"

        if len(self.foreign_keys) > 0:
            s += ",\n"
        s += ',\n'.join([(f" foreign key({key.name}) references " 
                             f"{key.table.name}({key.column.name})")
                            for key in self.foreign_keys if key is not None])


        if self.primary_key is not None:
            s += (",\n" f"{self.primary_key}")
        
        return (f"{s});")

    def __enforce_hashkey(self):
        if not self.hash_key:
            return

        if "hash_id" in self.columns and self.columns["hash_id"].is_primary_key:
            return

        for col in self.columns.values():
            assert not col.is_primary_key, ("A Table with a hash key can't"
                                " be declared with a Column set as a primary "
                                "key")
        assert not self.primary_key, ("A Table with a hash key can't"
                                " have a primary key declared")
        if "hash_id" not in self.columns:
            self.columns["hash_id"] = Column("hash_id", primary_key=True,
                not_null=True)

    def __enforce_parent_hash(self):
        if not self.parent_table:
            return

        if "parent_hash" in self.columns and \
            self.columns["parent_hash"].is_primary_key:
            return

        self.columns["parent_hash"] = Column("parent_hash", not_null=True)
        self.foreign_keys = tuple([k for k in self.foreign_keys] + \
            [ForeignKey("parent_hash", self.parent_table,
                self.parent_table.columns["hash_id"])] )

    def build_tag_path(self):
        """
        Returns full XPath to the tag containing records
        for this table, starting from the root tag.
        """

        tag = self.top_tag
        if self.parent_table:
            tag = self.parent_table.build_tag_path()
        if self.tag_name:
            return f"{tag}/{self.tag_name}"
        return tag

    def get_hash_key(self, row):
        m = sha256()
        for key in self.hash_key:
            try:
                m.update(str(row[key]).encode('utf-8'))
            except:
                print (row[key])
                raise
        return m.hexdigest()


    def read_row(self, node):
        type_map = {Integer : int, Real: float}
        data_types = {name : type_map[type(col.type)]
                      for name,col in self.columns.items() 
                      if type(col.type) in (Integer, Real)}
        row ={k : None for k in self.columns.keys()}
        for child in node:
            if child.tag in self.columns:
                val = child.text
                if child.tag in data_types and val is not None:
                    val = data_types[child.tag](val)
                row[child.tag] = val
        return row

    def __read_child(self, fname):
        assert self.parent_table.hash_key

        parent_tag = self.parent_table.build_tag_path()
        child_tag = self.tag_name
        root = ElementTree.parse(fname).getroot()

        data = []
        for parent in root.findall(parent_tag):
            parent_row = self.parent_table.read_row(parent)
            parent_hash = self.parent_table.get_hash_key(parent_row)
            for el in parent.findall(child_tag):
                row = self.read_row(el)
                row["parent_hash"] = parent_hash
                data.append(row)

        return data

    def __read_parent(self, fname):
        root_tag = self.build_tag_path()
        root = ElementTree.parse(fname).getroot()

        data = []
        for el in root.findall(root_tag):

            row = self.read_row(el)
            if self.hash_key:
                hash_key = self.get_hash_key(row)
                row["hash_id"] = hash_key
            data.append(row)
        return data


    def read_table(self, data_dir):
        """
        data_dir - path to the directory containing the XML file for
                   this table.

        Returns a list of dictionaries where each key corresponds to
        a table's column.
        """

        # TODO: Fix this to do a proper path join.
        fname = f"{data_dir}/{self.filename}"
        if self.parent_table:
            return self.__read_child(fname)
        data = self.__read_parent(fname)
        return data


class ForeignKey:
    """
    Defines a foreign key

    table - the Table object this key refers to. 
    column -  one of the table's Column's
    """

    def __init__(self, name, table, column):
        self.name = name
        self.table = table
        self.column = column

    def __repr__(self):

        return (f"foreign key ({self.name}) references {self.table.name}"
                f" ({self.column.name})")

    def __str__(self):
        return self.__repr__()


class PrimaryKey:
    def __init__(self, column_names):
        self.column_names = tuple(c for c in column_names)

    def __repr__(self):
        return ("primary key "
                f"({','.join([name for name in self.column_names])})")

    def __str__(self):
        return self.__repr__()


class Index:
    def __init__(self, name, table, column_names, unique=False):
        self.name = name
        self.table = table
        self.column_names = column_names
        self.unique = unique

    def __repr__(self):
        unique = {True: " unique", False: ""}
        s = (f"create{unique[self.unique]} index if not exists {self.name} " 
             f"on {self.table.name} ("
            f"{', '.join([name for name in self.column_names])});")
        return s
