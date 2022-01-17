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

Data for the table can be read from the corresponding XML file by
calling:

```
table.read_table(data_dir)
```

where data_dir is the path to the directory containing the XML file.
