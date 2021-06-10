library(ggplot2)
library(ggvenn)
library(dplyr)
library(data.table)

setwd("~/Escritorio/TFM/database")


Pub_or_tool <- function(mypub){
  lapply(mypub, function(col) {
    if (suppressWarnings(all(!is.na(as.numeric(as.character(col)))))) {
      return("Publication")
    } else {
      return("Tool")
    }
  })
}

retrieve_metadata = function(metadata, section_name){
  pub_intro1 = array(unique(metadata$id1))
  pub_intro2 = array(unique(metadata$id2))
  pub_intro = data.frame("name"= unique(c(pub_intro1, pub_intro2)), "label_type"= NA, "section" = NA)
  for(i in 1:nrow(pub_intro)){
    label_pub= Pub_or_tool(pub_intro[i,1])
    pub_intro[i,2] = label_pub
    pub_intro[i,3] = section_name
  }
  return(pub_intro)
}
retrive_relations = function(metadata, section_name){
  for(i in 1:nrow(metadata)){
    label_pub1 = Pub_or_tool(metadata[i,1])
    label_pub2 = Pub_or_tool(metadata[i,2])
    metadata[i,5] = section_name
    if(label_pub1 == "Tool" & label_pub2 == "Tool"){
      metadata[i,6] = "Tool-Tool"
    }
    if((label_pub1 == "Tool" & label_pub2 == "Publication") | (label_pub1 == "Publication" & label_pub2 == "Tool")){
      metadata[i,6] = "Pub.-Tool"
    }
    if(label_pub1 == "Publication" & label_pub2 == "Publication"){
      metadata[i,6] = "Pub.-Pub."
    }
  }
  colnames(metadata)[5] = "section"
  colnames(metadata)[6] = "type_edge"
  return(metadata)
}

retrieve_openaccess_database = function(list_usecases, list_folders){
  all_pub_tool_OA = data.frame()
  all_relations = data.frame()
  for (i in 1:length(list_usecases)){
    fold_usecase = list_folders[i]
    # Introduction Data
    introduction_data = read.csv(paste(fold_usecase,"/Citations_Introduction_backup.csv", sep=""))
    introduction_metadata = read.csv(paste(fold_usecase,"/MetaCitations_Introduction.csv", sep=""))
    
    introduction_pub_tool = retrieve_metadata(introduction_metadata, "Introduction")
    introduction_pub_tool$Usecase = list_usecases[i]
    introduction_relations = retrive_relations(introduction_metadata, "Introduction")
    introduction_relations$Usecase = list_usecases[i]
    
    # Methods Data
    methods_data = read.csv(paste(fold_usecase,"/Citations_Methods_backup.csv",sep=""))
    methods_metadata = read.csv(paste(fold_usecase,"/MetaCitations_Methods.csv",sep=""))
    
    methods_pub_tool = retrieve_metadata(methods_metadata, "Methods")
    methods_pub_tool$Usecase = list_usecases[i]
    methods_relations = retrive_relations(methods_metadata, "Methods")
    methods_relations$Usecase = list_usecases[i]
    
    # Results Data
    results_data = read.csv(paste(fold_usecase,"/Citations_Results_backup.csv",sep=""))
    results_metadata = read.csv(paste(fold_usecase,"/MetaCitations_Results.csv",sep=""))
    
    results_pub_tool = retrieve_metadata(results_metadata, "Results")
    results_pub_tool$Usecase = list_usecases[i]
    results_relations = retrive_relations(results_metadata, "Results")
    results_relations$Usecase = list_usecases[i]
  
    # Discussion Data
    discussion_data = read.csv(paste(fold_usecase,"/Citations_Discussion_backup.csv",sep=""))
    discussion_metadata = read.csv(paste(fold_usecase,"/MetaCitations_Discussion.csv",sep=""))
    
    discussion_pub_tool = retrieve_metadata(discussion_metadata, "Discussion")
    discussion_pub_tool$Usecase = list_usecases[i]
    discussion_relations = retrive_relations(discussion_metadata, "Discussion")
    discussion_relations$Usecase = list_usecases[i]
    
    all_pub_tool_OA = rbind(all_pub_tool_OA, introduction_pub_tool,
                            methods_pub_tool, results_pub_tool,
                            discussion_pub_tool)
    all_relations = rbind(all_relations, introduction_relations,
                          methods_relations, results_relations,
                          discussion_relations)
  }
  list_tables = list(all_pub_tool_OA, all_relations)
  return(list_tables)
}

list_usecases = c("Comparative", "Functional prediction \n of sequence variants", "Proteomics")
list_folders_usescases = c("OAComparative", "OAMolecular", "OAProteomicsData")
list_tab = retrieve_openaccess_database(list_usecases,list_folders_usescases)
all_pub_tool = list_tab[[1]]
all_relations = list_tab[[2]]


# All together

all_pub_tool = rbind(introduction_pub_tool, methods_pub_tool, results_pub_tool, discussion_pub_tool)
ggplot(all_pub_tool, aes(x=section, fill = label_type)) + 
  geom_histogram(stat = "count", position="fill") + facet_wrap(~ Usecase) +
  labs(x= "Section", y = "%", title = paste("Percentage of publications and tools in each section and use case"), fill = "Type")

all_relations = rbind(introduction_relations, methods_relations, results_relations, discussion_relations)
ggplot(all_relations, aes(x=section, fill = type_edge)) + 
  geom_histogram(stat = "count", position="fill") +facet_wrap(~ Usecase) +
  labs(x= "Section", y = "%", title = "Percentage  of relationships in  each section and use case", fill = "Type of relation")

# Tools in one section and not in the other

all_tools = all_pub_tool[all_pub_tool[,2] == "Tool",]

l_tools = c()
l_duplicated = c()
`%notin%` <- Negate(`%in%`)
for(i in 1:nrow(all_tools)){
  possible_tool = as.character(all_tools$name[i])
  if(possible_tool %notin% l_tools){
    l_tools = c(l_tools, possible_tool)
  }
  else{
    l_duplicated = c(l_duplicated, possible_tool)
  }
}

all_single_tool = all_tools[all_tools$name %notin% l_duplicated,]
all_single_tool[,3] = factor(all_single_tool$section, levels=c("Introduction", "Methods", "Results", "Discussion"))

levels(all_single_tool[,3])

ggplot(all_single_tool, aes(section)) +
  geom_bar() +
  labs(x = "Section", y = "Number of Tools", title = " Unique Tools in each section")

# Venn diagram

all_tools_trans = list("Introduction" = all_tools$name[all_tools$section=="Introduction"],
                             "Methods"= all_tools$name[all_tools$section=="Methods"],
                             "Results"= all_tools$name[all_tools$section=="Results"], 
                             "Discussion"= all_tools$name[all_tools$section=="Discussion"])
ggvenn(
  all_tools_trans, 
  fill_color = c("#0073C2FF", "#EFC000FF", "#868686FF", "#CD534CFF"),
  stroke_size = 0.5, set_name_size = 4,
) + labs(title = "Comparative Genomics Venn Diagram") + theme(plot.title = element_text(hjust = 0.5, vjust = -15))



# Statistics for the Metadata database

# Comparative

comparative_data = read.csv("metagraph_Comparative/MetaCitations.csv")

ggplot(comparative_data, aes(n_citations)) +
  geom_line(stat = "count") + scale_y_log10() + scale_x_log10()


comparative_pub_tool = retrieve_metadata(comparative_data, "Comparative")
ggplot(comparative_pub_tool, aes(label_type)) + geom_histogram(stat="count")

comparative_relations = retrive_relations(comparative_data, "Comparative")
ggplot(comparative_relations, aes(type_edge)) + geom_histogram(stat="count")

# Molecular

molecular_data = read.csv("MetaGraph_Mol/MetaCitations.csv")

ggplot(molecular_data, aes(n_citations)) +
  geom_line(stat = "count") + scale_y_log10() + scale_x_log10()


molecular_pub_tool = retrieve_metadata(molecular_data, "Functional prediction \n of sequence variants")
ggplot(molecular_pub_tool, aes(label_type)) + geom_histogram(stat="count")

molecular_relations = retrive_relations(molecular_data, "Functional prediction \n of sequence variants")
ggplot(molecular_relations, aes(type_edge)) + geom_histogram(stat="count")

# Proteomics

proteomics_data = read.csv("Meta_Prot/MetaCitations.csv")

ggplot(proteomics_data, aes(n_citations)) +
  geom_line(stat = "count") + scale_y_log10() + scale_x_log10()


proteomics_pub_tool = retrieve_metadata(proteomics_data, "Proteomics")
ggplot(proteomics_pub_tool, aes(label_type)) + geom_histogram(stat="count")

proteomics_relations = retrive_relations(proteomics_data, "Proteomics")
ggplot(proteomics_relations, aes(type_edge)) + geom_histogram(stat="count")

# All use cases

## Without filtering

usecases_pub_tool = rbind(comparative_pub_tool, molecular_pub_tool, proteomics_pub_tool)
ggplot(usecases_pub_tool, aes(x=section, fill = label_type)) + 
  geom_histogram(stat = "count", position="fill") +
  geom_text(stat = 'count',aes(label = ..count..),
            position = "stack",
            vjust = 1,
            size = 2,
            color = "red")
  labs(x= "Use case", y = "%", title = paste("Percentage of publications and tools in each use case"), fill = "Type")

usecases_relations = rbind(comparative_relations, molecular_relations, proteomics_relations)
ggplot(usecases_relations, aes(x=section, fill = type_edge)) + 
  geom_histogram(stat = "count", position="fill") +
  geom_text(stat = 'count',aes(label = ..count..),
            position = "stack",
            vjust = 1,
            size = 2,
            color = "red")
  labs(x= "Use case", y = "%", title = "Percentage of relations in each use case", fill = "Type of relation")

## Filtering for co-occurrences

setwd("~/Escritorio/TFM/")
comp_count_nodes = read.table("SoLiTo/Meta_OA/number_of_nodes_comp.txt", sep="\t", header = T)
comp_count_nodes$Usecase= "Comparative"
mol_count_nodes = read.table("SoLiTo/Meta_OA/number_of_nodes_mol.txt", sep="\t", header = T)
mol_count_nodes$Usecase= "Functional prediction \n of sequence variants"

prot_count_nodes = read.table("SoLiTo/Meta_OA/number_of_nodes_prot.txt", sep="\t", header = T)

all_count_nodes = rbind(prot_count_nodes,comp_count_nodes, mol_count_nodes)


ggplot(all_count_nodes, aes(x=Time, y= percentage, color = Usecase)) + 
  geom_line() +
labs(x= "Number of co-occurrences", y = "% of tools", title = paste("Percentage of tools when increasing the co-occurrences"), color = "Use case")

usecases_relations = rbind(comparative_relations, molecular_relations, proteomics_relations)
usecases_relations = usecases_relations[usecases_relations$n_citations >100,]
ggplot(usecases_relations, aes(x=section, fill = type_edge)) + 
  geom_histogram(stat = "count", position="fill")  +
labs(x= "Use case", y = "%", title = "Percentage of >100 relationships in each use case and type of edge", fill = "Type of relation")

# Fisher test
setwd("~/Escritorio/TFM")

fisher_per_community = function(community_dat, graph_dat){
  p_values = c()
  for(i in 1:nrow(community_dat)){
    community_id = community_dat$community[i]
    topic_community = community_dat$topic[i]
    times_com = community_dat$ntimes[i]
    total_com = community_dat$total[i]
    for(j in 1:nrow(graph_dat)){
      topic_graph = graph_dat$topic[j]
      times_graph = graph_dat$ntimes[j]
      total_graph = graph_dat$total[j]
      if(topic_community == topic_graph){
        dat = data.frame(
          "TopTopic" = c(times_graph, times_com),
          "Other" = c(total_graph-times_graph, total_com-times_com),
          row.names = c("All",paste("Community",as.character(community_id))),
          stringsAsFactors = F
        )
        colnames(dat) = c(as.character(topic_community), "Other")
        chisq=chisq.test(dat)$expected
        if(chisq[1,1] <5 | chisq[1,2] <5 | chisq[2,1] <5 | chisq[1,2] <5){
          test = fisher.test(dat)
          p_values= c(p_values,test$p.value)
        }
        else{
          print(chisq)
          test = chisq.test(dat)
          p_values= c(p_values,test$p.value)
        }
        print(paste("Community:",community_id,"Topic:",topic_community,
                    "P-value:",test$p.value, "Number com:",times_com,
                    "Total com",total_com, "Number graph:", times_graph, "Number total:", total_graph))
      }
    }
  }
  # Apply bonferroni correction
  print("Adjusted p-values")
  p_values_adj = p.adjust(p_values, method = "bonferroni", n= (length(p_values)*2))
  for(i in 1:nrow(community_dat)){
    print(paste("Community:",  community_dat$community[i],"Topic:", community_dat$topic[i], "P-value:", p_values_adj[i]))
  }
}

topics_graph = read.table("SoLiTo/OpenAccessGraph/CreateNeo4jDatabase/topics_graph_prot.txt", sep="\t", header = T)
topics_comm = read.table("SoLiTo/OpenAccessGraph/CreateNeo4jDatabase/topics_comm_prot.txt", sep="\t", header = T)
p_val_adj=fisher_per_community(topics_comm, topics_graph)


# Tools
tool_data = read.table("SoLiTo/Meta_OA/tool_year_all.txt", sep="\t", quote = "'", header = T)

tool_data_unique=setDT(tool_data)[ , .SD[which.min(year)], by = tool]   # Unique with min year
ggplot(tool_data_unique, aes(year)) + geom_bar()

tool_data_duplicate = as.data.frame(table(tool_data$tool))

ggplot(tool_data_duplicate, aes(as.factor(Freq))) + geom_bar() + scale_y_log10()

