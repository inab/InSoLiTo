import pandas as pd

# constants
datasetsList = ["InputData.csv", "InputFormat.csv", "Operations.csv", "OutputData.csv", "OutputFormat.csv",
                "Tools.csv", "ToolsToLanguages.csv", "ToolsToOS.csv", "ToolsToPublications.csv", "Topics.csv",
                "ToolsToTypeTool.csv"]

datasetsDir = "../InSoLiToImport/"


# functions
def read_datasets(datasets_list):
    # TODO: add docstrings
    df_list = list()
    dfnames_list = list()
    for dataset in datasets_list:
        df = pd.read_csv(datasetsDir + dataset, sep=",", low_memory=False)
        df_list.append(df)
        dfnames_list.append(dataset.rsplit(".", 1)[0])
    return df_list, dfnames_list


def filter_dataframe(df, df_list, meta, colname=None):
    # TODO: add docstrings
    if meta:
        return df[df[['id1', 'id2']].isin(df_list).any(axis=1)]  # or
        # return df[df[['id1', 'id2']].isin(df_list).all(1)]   # and
    else:
        if colname is not None:
            return df[df[colname].isin(df_list)]


def write_dataset(df, dfname):
    # TODO: add docstrings
    df.to_csv(datasetsDir + dfname + "_PerMedCoEn2.csv", sep=",", index=False)


# load all datasets in a list
datasets, datasetsNames_list = read_datasets(datasetsList)

# load tools_list
Tools_PerMedCoE = pd.read_csv(datasetsDir + "Tools_PerMedCoE.csv", sep=",", low_memory=False)
tools_list = list(Tools_PerMedCoE['label'].unique())

# filter and save MetaCitationsReduction by permedcoe tools_list
MetaCitationsReduction_str = "MetaCitationsReduction"
MetaCitationsReduction = pd.read_csv(datasetsDir + MetaCitationsReduction_str + ".csv", sep=",", low_memory=False)
MetaCitationsReduction_filtered = filter_dataframe(MetaCitationsReduction, tools_list, True, None)
write_dataset(MetaCitationsReduction_filtered, MetaCitationsReduction_str)

# filter and save PublicationsInMetaCitations by MetaCitationsReduction_filtered
PublicationsInMetaCitations_str = "PublicationsInMetaCitations"
PublicationsInMetaCitations = pd.read_csv(datasetsDir + PublicationsInMetaCitations_str + ".csv", sep=",", low_memory=False)
# create list of unique pmids from MetaCitationsReduction filtered by permedcoe tools_list
MetaCitationsReduction_filtered_pmids = list(MetaCitationsReduction_filtered['id1'].unique()) + list(MetaCitationsReduction_filtered['id2'].unique())
# from in to str pmid values from PublicationsInMetaCitations
PublicationsInMetaCitations['pmid'] = PublicationsInMetaCitations['pmid'].astype(str)
# filter and save PublicationsInMetaCitations_filtered if pmids are in MetaCitationsReduction_filtered_pmids list
PublicationsInMetaCitations_filtered = filter_dataframe(PublicationsInMetaCitations, MetaCitationsReduction_filtered_pmids, False, "pmid")
write_dataset(PublicationsInMetaCitations_filtered, PublicationsInMetaCitations_str)

# filter and save Tools_filtered if pmids are in MetaCitationsReduction_filtered_pmids list
Tools_filtered = filter_dataframe(datasets[5], MetaCitationsReduction_filtered_pmids, False, "label")
write_dataset(Tools_filtered, "Tools")

# filter and save each dataset by permedcoe tools_list
for i in range(len(datasets)):
    write_dataset(filter_dataframe(datasets[i], Tools_filtered["label"], False, "label"), datasetsNames_list[i])
