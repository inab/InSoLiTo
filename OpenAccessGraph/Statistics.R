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


# Introduction Data
introduction_data = read.csv("OAComparative/Citations_Introduction_backup.csv")

ggplot(introduction_data, aes(factor(n_citations))) +
  geom_histogram(stat = "count") + scale_y_log10()
ggplot(introduction_data, aes(factor(n_citations))) +
  geom_histogram(stat = "count")

introduction_metadata = read.csv("OAComparative/MetaCitations_Introduction.csv")

introduction_pub_tool = retrieve_metadata(introduction_metadata, "Introduction")
ggplot(introduction_pub_tool, aes(label_type)) + geom_histogram(stat="count")

introduction_relations = retrive_relations(introduction_metadata, "Introduction")
ggplot(introduction_relations, aes(type_edge)) + geom_histogram(stat="count")



# Methods Data
methods_data = read.csv("OAComparative/Citations_Methods_backup.csv")

ggplot(methods_data, aes(factor(n_citations))) +
  geom_histogram(stat = "count") + scale_y_log10()
ggplot(methods_data, aes(factor(n_citations))) +
  geom_histogram(stat = "count")

methods_metadata = read.csv("OAComparative/MetaCitations_Methods.csv")

methods_pub_tool = retrieve_metadata(methods_metadata, "Methods")
ggplot(methods_pub_tool, aes(label_type)) + geom_histogram(stat="count")

methods_relations = retrive_relations(methods_metadata, "Methods")
ggplot(methods_relations, aes(type_edge)) + geom_histogram(stat="count")


# Results Data
results_data = read.csv("OAComparative/Citations_Results_backup.csv")

ggplot(results_data, aes(factor(n_citations))) +
  geom_histogram(stat = "count") + scale_y_log10()
ggplot(results_data, aes(factor(n_citations))) +
  geom_histogram(stat = "count")

results_metadata = read.csv("OAComparative/MetaCitations_Results.csv")

results_pub_tool = retrieve_metadata(results_metadata, "Results")
ggplot(results_pub_tool, aes(label_type)) + geom_histogram(stat="count")

results_relations = retrive_relations(results_metadata, "Results")
ggplot(results_relations, aes(type_edge)) + geom_histogram(stat="count")

# Discussion Data
discussion_data = read.csv("OAComparative/Citations_Discussion_backup.csv")

ggplot(discussion_data, aes(factor(n_citations))) +
  geom_histogram(stat = "count") + scale_y_log10()
ggplot(discussion_data, aes(factor(n_citations))) +
  geom_histogram(stat = "count")

discussion_metadata = read.csv("OAComparative/MetaCitations_Discussion.csv")

discussion_pub_tool = retrieve_metadata(discussion_metadata, "Discussion")
ggplot(discussion_pub_tool, aes(label_type)) + geom_histogram(stat="count")

discussion_relations = retrive_relations(discussion_metadata, "Discussion")
ggplot(discussion_relations, aes(type_edge)) + geom_histogram(stat="count")

# All together

all_pub_tool = rbind(introduction_pub_tool, methods_pub_tool, results_pub_tool, discussion_pub_tool)
ggplot(all_pub_tool, aes(x=section, fill = label_type)) + 
  geom_histogram(stat = "count", position="fill") +
  labs(x= "Section", y = "%", title = paste("Comparative Genomics: Percentage \n of publications and tools in each section"), fill = "Type")

all_relations = rbind(introduction_relations, methods_relations, results_relations, discussion_relations)
ggplot(all_relations, aes(x=section, fill = type_edge)) + 
  geom_histogram(stat = "count", position="fill") +
  labs(x= "Section", y = "%", title = "Comparative Genomics: Percentage \n of relations in  each section", fill = "Type of relation")

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

# Programming languages race

lang_data = read.table("SoLiTo/Meta_OA/languages_year_all.txt", sep="\t", quote = "'", header = T)
ggplot(lang_data, aes(languages)) + geom_bar()

count_language_year=as.data.frame(table(lang_data$languages, lang_data$year))
colnames(count_language_year) = c("language", "year", "freq")
count_language_year=count_language_year[order(count_language_year$language, count_language_year$year),]

count_language_year=count_language_year%>%group_by(language)%>%mutate(cumusum=cumsum(freq))

count_language_year = as.data.frame(count_language_year)
count_language_year$language = as.character(count_language_year$language)
count_language_year$year = as.numeric(as.character(count_language_year$year))

lab = tapply(count_language_year$cumusum, count_language_year$language, last)

ggplot(count_language_year) +
  geom_line(aes(year, cumusum, group = language, color = language))

ggplot() +
  geom_line(data = count_language_year, aes(year, cumusum, color = language)) +
  geom_text(data = count_language_year %>% filter(year == last(year)),
            aes(label = language, x = year + 1, y = cumusum, color = language)) + 
  guides(color = FALSE) + theme_bw() + 
  scale_x_continuous(breaks = scales::pretty_breaks(10))

# OS race

os_data = read.table("SoLiTo/Meta_OA/os_year_all.txt", sep="\t", quote = "'", header = T)
ggplot(os_data, aes(os)) + geom_bar()

count_os_year=as.data.frame(table(os_data$os, os_data$year))
colnames(count_os_year) = c("os", "year", "freq")
count_os_year=count_os_year[order(count_os_year$os, count_os_year$year),]

count_os_year=count_os_year%>%group_by(os)%>%mutate(cumusum=cumsum(freq))

count_os_year = as.data.frame(count_os_year)
count_os_year$os = as.character(count_os_year$os)
count_os_year$year = as.numeric(as.character(count_os_year$year))

ggplot() +
  geom_line(data = count_os_year, aes(year, cumusum, color = os)) +
  geom_text(data = count_os_year %>% filter(year == last(year)),
            aes(label = os, x = year + 1, y = cumusum, color = os)) + 
  guides(color = FALSE) + theme_bw() + 
  scale_x_continuous(breaks = scales::pretty_breaks(10))

# Venn diagram of OS usage

# venn.diagram(all_tools[,c(1,3)],"provavenn.png")
# 
# all_tools_trans = list("Introduction" = all_tools$name[all_tools$section=="Introduction"],
#                        "Methods"= all_tools$name[all_tools$section=="Methods"],
#                        "Results"= all_tools$name[all_tools$section=="Results"], 
#                        "Discussion"= all_tools$name[all_tools$section=="Discussion"])
venn_os_data = list("Linux" = as.character(os_data$tool[os_data$os=="Linux"]),
                    "Mac" = as.character(os_data$tool[os_data$os=="Mac"]),
                    "Windows" = as.character(os_data$tool[os_data$os=="Windows"]))
ggvenn(
  venn_os_data,
  fill_color = c("#0073C2FF", "#EFC000FF", "#868686FF"),
  stroke_size = 0.5, set_name_size = 3
)


# Tools
tool_data = read.table("SoLiTo/Meta_OA/tool_year_all.txt", sep="\t", quote = "'", header = T)

tool_data_unique=setDT(tool_data)[ , .SD[which.min(year)], by = tool]   # Unique with min year
ggplot(tool_data_unique, aes(year)) + geom_bar()

tool_data_duplicate = as.data.frame(table(tool_data$tool))

ggplot(tool_data_duplicate, aes(as.factor(Freq))) + geom_bar() + scale_y_log10()

# Intentar ficar un circus plot aqui
