# Animation File

The Python script query the first and second-degree connections of a given Tool and the R script animate the relationships by year.

To create the HTML with the animation, you must do the following steps:

1. Run the Python 3 script.

```
python3 AnimationQuery.py <NameOfTool> <MinFirstDegree> <MinSecondDegree> <OutputFile>

Argument    <NameOfTool>: Name of the tool.
Argument    <MinFirstDegree>: Mininum number of co-occurrences in the first-degree relationships.
Argument    <MinSecondDegree>: Mininum number of co-occurrences in the second-degree relationships.
Argument    <OutputFile>: Location of the Output file.

```

2. Run the R script.

```
Rscript Animation.R <InputFile> <OutputFile>

Argument    <InputFile>: Location of the Input file.
Argument    <OutputFile>: Location of the Output file.

```
