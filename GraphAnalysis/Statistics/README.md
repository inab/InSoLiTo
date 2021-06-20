# Statistics in the Metadata database

The Python scripts query the number of nodes retrieved when we increase the number of co-occurrences and the topics of the graph and their communities to calculate the Fisher test. With the R script we plot the number of node types with the increase of co-occurrences and the Fisher test. 

You must open your Metadata Neo4j database of interest.


- Run [NumberNodes.py](NumberNodes.py) Python 3 script to calculate the nodes with the increase of co-occurrences.

```
python3 NumberNodes.py <OutputFile> <UseCase>

Argument    <OutputFile>: Location of the Output file.
Argument    <UseCase>: Name of the use case.

```

- Run [TopicsFisher.py](TopicsFisher.py) Python 3 script to retrieve the topics used for the Fisher test.

```
python3 TopicsFisher.py <OutputComm> <OutputGraph>

Argument    <OutputComm>: Output file of the topics from the communities.
Argument    <OutputGraph>: Output file of the topics from all the graph.

```

After you have the files, you can open and run the R script.
