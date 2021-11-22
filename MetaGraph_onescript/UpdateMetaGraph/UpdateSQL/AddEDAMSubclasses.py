# Import libraries
from owlready2 import *


def create_EDAM_table(c,conn):
    
    onto = get_ontology("http://edamontology.org/EDAM.owl").load()

    
    c.execute(f"""
              SELECT edam_id
              from Keywords
              """)
    edam_ids=c.fetchall()
    for edam_id in edam_ids:
        edam_id = edam_id[0].split("/")[3]
        Ids = f"onto.{edam_id}.ancestors()"
        ancestors = list(eval(Ids))
        print(ancestors)
        for ancestor in ancestors:
            ancestor = str(ancestor)
            if "owl" in ancestor or edam_id in ancestor:
                continue
            ancestor = ancestor.split(".")[1]
            ancestor_name = f"onto.{ancestor}.label"
            ancestor_name = str(list(eval(ancestor_name))[0])
            ancestor_iri = f"onto.{ancestor}.iri"
            ancestor_iri = str(eval(ancestor_iri))
            # Add new keyword to table
            c.execute(f""" INSERT OR IGNORE INTO Keywords values ('{ancestor_iri}', '{ancestor_name}')""")
            
            # Check if the ancestors are subclassess of other ancestors
            ancestor_subclasses = f"onto.{ancestor}.subclasses()"
            ancestor_subclasses = list(eval(ancestor_subclasses))
            ancestor_subclasses = [str(i) for i in ancestor_subclasses]
            for ancestor2 in ancestors:
                ancestor2 = str(ancestor2)
                if ancestor2 not in ancestor_subclasses:
                    continue
                ancestor2 = ancestor2.split(".")[1]
                ancestor2_iri = f"onto.{ancestor2}.iri"
                ancestor2_iri = str(eval(ancestor2_iri))
                type_of_relationship = ancestor2_iri[24:].split("_")[0]
                print(ancestor2_iri,"is a subclass of", ancestor_iri)
                
                c.execute(f""" INSERT OR IGNORE INTO SubclassEDAM values ('{ancestor_iri}', '{ancestor2_iri}', '{type_of_relationship}')""")
            conn.commit()

