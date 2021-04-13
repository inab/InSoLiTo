library(ggplot2)
library(ggvenn)

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


# Introduction Data
introduction_data = read.csv("OAProteomicsData/Citations_Introduction_backup.csv")

ggplot(introduction_data, aes(factor(n_citations))) +
  geom_histogram(stat = "count") + scale_y_log10()
ggplot(introduction_data, aes(factor(n_citations))) +
  geom_histogram(stat = "count")

introduction_metadata = read.csv("OAProteomicsData/MetaCitations_Introduction.csv")

introduction_pub_tool = retrieve_metadata(introduction_metadata, "Introduction")
ggplot(introduction_pub_tool, aes(label_type)) + geom_histogram(stat="count")

introduction_relations = retrive_relations(introduction_metadata, "Introduction")
ggplot(introduction_relations, aes(type_edge)) + geom_histogram(stat="count")



# Methods Data
methods_data = read.csv("OAProteomicsData/Citations_Methods_backup.csv")

ggplot(methods_data, aes(factor(n_citations))) +
  geom_histogram(stat = "count") + scale_y_log10()
ggplot(methods_data, aes(factor(n_citations))) +
  geom_histogram(stat = "count")

methods_metadata = read.csv("OAProteomicsData/MetaCitations_Methods.csv")

methods_pub_tool = retrieve_metadata(methods_metadata, "Methods")
ggplot(methods_pub_tool, aes(label_type)) + geom_histogram(stat="count")

methods_relations = retrive_relations(methods_metadata, "Methods")
ggplot(methods_relations, aes(type_edge)) + geom_histogram(stat="count")


# Results Data
results_data = read.csv("OAProteomicsData/Citations_Results_backup.csv")

ggplot(results_data, aes(factor(n_citations))) +
  geom_histogram(stat = "count") + scale_y_log10()
ggplot(results_data, aes(factor(n_citations))) +
  geom_histogram(stat = "count")

results_metadata = read.csv("OAProteomicsData/MetaCitations_Results.csv")

results_pub_tool = retrieve_metadata(results_metadata, "Results")
ggplot(results_pub_tool, aes(label_type)) + geom_histogram(stat="count")

results_relations = retrive_relations(results_metadata, "Results")
ggplot(results_relations, aes(type_edge)) + geom_histogram(stat="count")

# Discussion Data
discussion_data = read.csv("OAProteomicsData/Citations_Discussion_backup.csv")

ggplot(discussion_data, aes(factor(n_citations))) +
  geom_histogram(stat = "count") + scale_y_log10()
ggplot(discussion_data, aes(factor(n_citations))) +
  geom_histogram(stat = "count")

discussion_metadata = read.csv("OAProteomicsData/MetaCitations_Discussion.csv")

discussion_pub_tool = retrieve_metadata(discussion_metadata, "Discussion")
ggplot(discussion_pub_tool, aes(label_type)) + geom_histogram(stat="count")

discussion_relations = retrive_relations(discussion_metadata, "Discussion")
ggplot(discussion_relations, aes(type_edge)) + geom_histogram(stat="count")

# All together

all_pub_tool = rbind(introduction_pub_tool, methods_pub_tool, results_pub_tool, discussion_pub_tool)
ggplot(all_pub_tool, aes(x=section, fill = label_type)) + 
  geom_histogram(stat = "count", position="fill") +
  labs(x= "Section", y = "%", title = "Percentage of publications and tools in each section", fill = "Type")

all_relations = rbind(introduction_relations, methods_relations, results_relations, discussion_relations)
ggplot(all_relations, aes(x=section, fill = type_edge)) + 
  geom_histogram(stat = "count", position="fill") +
  labs(x= "Section", y = "%", title = "Percentage of relations in each section", fill = "Type of relation")

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
venn.diagram(all_tools[,c(1,3)],"provavenn.png")

all_tools_trans = list("Introduction" = all_tools$name[all_tools$section=="Introduction"],
                             "Methods"= all_tools$name[all_tools$section=="Methods"],
                             "Results"= all_tools$name[all_tools$section=="Results"], 
                             "Discussion"= all_tools$name[all_tools$section=="Discussion"])
ggvenn(
  all_tools_trans, 
  fill_color = c("#0073C2FF", "#EFC000FF", "#868686FF", "#CD534CFF"),
  stroke_size = 0.5, set_name_size = 4
)



  
