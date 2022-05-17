# Import libraries
from owlready2 import *


def create_EDAM_table(c,conn):
    # Load all the EDAM ontology
    onto = get_ontology("http://edamontology.org/EDAM.owl").load()
    # Take all the EDAM terms from the database
    c.execute(f"""
              SELECT edam_id
              from Keywords
              """)
    edam_ids=c.fetchall()
    # For all the EDAM terms found
    for edam_id in edam_ids:
        # Take the ID of the EDAM term
        edam_id = edam_id[0].split("/")[3]
        # Look for the parents of the EDAM terms
        Ids = f"onto.{edam_id}.ancestors()"
        ancestors = list(eval(Ids))
        print(ancestors)
        # For all the parents
        for ancestor in ancestors:
            ancestor = str(ancestor)
            # If root or the ancestor is the same id, try the next edam term
            if "owl" in ancestor or edam_id in ancestor:
                continue
            # Take ancestor name
            ancestor = ancestor.split(".")[1]
            ancestor_name = f"onto.{ancestor}.label"
            ancestor_name = str(list(eval(ancestor_name))[0])
            # Take ancestor ID
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
                # If the ancestor are not a subclass of other ancestor, try the next edam term
                if ancestor2 not in ancestor_subclasses:
                    continue
                # If they are ancestor
                ancestor2 = ancestor2.split(".")[1]
                ancestor2_iri = f"onto.{ancestor2}.iri"
                ancestor2_iri = str(eval(ancestor2_iri))
                type_of_relationship = ancestor2_iri[24:].split("_")[0]
                print(ancestor2_iri,"is a subclass of", ancestor_iri)
                # Insert the relationship parent-child to the SubclassEDAM table
                c.execute(f""" INSERT OR IGNORE INTO SubclassEDAM values ('{ancestor_iri}', '{ancestor2_iri}', '{type_of_relationship}')""")
            conn.commit()

