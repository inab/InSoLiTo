import os

import pandas as pd

from PermedcoeN1 import toolsList, datasetsDir

# constants
LABEL = "label"


# load tools of level 1 and 2
Tools_PerMedCoE_str = "Tools_PerMedCoE"
toolsN1 = pd.read_csv(datasetsDir + Tools_PerMedCoE_str + ".csv", sep=",", low_memory=False)
toolsN2 = pd.read_csv(datasetsDir + Tools_PerMedCoE_str + "n2.csv", sep=",", low_memory=False)

# add N1 and O (original) levels
toolsN1_N1 = toolsN1[toolsN1[LABEL].isin(toolsList)]
toolsN1_O = toolsN1[~toolsN1[LABEL].isin(toolsList)]
toolsN1.loc[toolsN1[LABEL].isin(toolsN1_O[LABEL]), "level"] = "N1"
toolsN1.loc[toolsN1[LABEL].isin(toolsN1_N1[LABEL]), "level"] = "O"

toolsN1.to_csv(datasetsDir + Tools_PerMedCoE_str + "n1.csv", sep=",", index=False)

# add N2 levels
tools_list_N1 = list(toolsN1[LABEL])    # N1 i O

toolsN1_N1 = toolsN2[toolsN2[LABEL].isin(tools_list_N1)]
toolsN1_N2 = toolsN2[~toolsN2[LABEL].isin(tools_list_N1)]
toolsN1_N2["level"] = "N2"
toolsN1_N2_final = pd.concat([toolsN1, toolsN1_N2])

toolsN1_N2_final.to_csv(datasetsDir + Tools_PerMedCoE_str + "n2.csv", sep=",", index=False)

# load MetaCitations Reduction (all and level 1)
MetaCitationsReduction_str = "MetaCitationsReduction_PerMedCoE"
metAll = pd.read_csv(datasetsDir + MetaCitationsReduction_str + "n2.csv", sep=",", low_memory=False)
metN1 = pd.read_csv(datasetsDir + MetaCitationsReduction_str + ".csv", sep=",", low_memory=False)

# rename MetaCitations Reduction files (all and level 1)
fileO = datasetsDir + MetaCitationsReduction_str + ".csv"
fileN2 = datasetsDir + MetaCitationsReduction_str + "n2.csv"
if os.path.exists(fileO) and os.path.exists(fileN2):
    os.rename(fileN2, datasetsDir + MetaCitationsReduction_str + "all.csv")
    os.rename(fileO, datasetsDir + MetaCitationsReduction_str + "n1.csv")

# add MetaCitations Reduction of level 2
metN2 = pd.concat([metAll, metN1]).drop_duplicates(keep=False)
metN2.to_csv(datasetsDir + MetaCitationsReduction_str + "n2.csv", sep=",", index=False)
