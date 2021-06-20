# InSoLiTo (Inferring Social Life of Tools)

The aim of this project is to create a graph-based network of the co-usage, understood as being cited by the same scientific publication, of research software found in OpenEBench.

Currently, there are two type of databases used to create this social network of tools:

[Metadata database](MetaGraph): Creation of a relational and graph database for all the metadata information of the research papers.
[OpenAccess database](OpenAccessGraph): Creation of a relational and graph database for each of the publications sections (Introduction, Methods, Results, Discussion) information of the OpenAccess research papers.

Also, there is the [MetaOAGraph folder](MetaOAGraph), used to merge the Metadata and OpenAccess database for further analysis. You can also create a graph database with the merged database with all the use cases together.

The scripts used for analysing the graph database are in the [Graph Analysis](MetaGraph) folder.

The HTML files and script used to visualise the graph are in the [Graph Analysis](MetaGraph) folder.

### Main requirement

Before creating the databases you need a Publications domain from your tools of interest. The Publications domain can be computed with the [OpenEBench references and citations enricher](https://github.com/inab/opeb-enrichers/tree/master/pubEnricher).
