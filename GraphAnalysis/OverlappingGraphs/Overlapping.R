library(igraph)
library(visNetwork)

### Overlap All vs sections in OpenAccess database

# See if the relationship is in one section
in_section = function(edges_section,edges_file_all){
  for(i in 1:nrow(edges_file_all)){
    if ((as.character(edges_file_all[i,1]) == edges_section[1] &
         as.character(edges_file_all[i,2]) == edges_section[2])  |
        (as.character(edges_file_all[i,1]) == edges_section[2] &
         as.character(edges_file_all[i,2]) == edges_section[1]) 
    ){
      return(TRUE)
    }
  }
  return(FALSE)
}

# Function to see the percentage of relationships in
overlapping_sections = function(file_relations, section){
  edges_file = read.table(file_relations, sep= "\t",quote = "", header = T)
  edges_file_all = edges_file[edges_file$Section== "All",]
  edges_file_section = edges_file[edges_file$Section== section,]
  edges_file_section$is_section = FALSE
  
  # Results edges that are in methods
  for (j in 1:nrow(edges_file_section)){
    print(j)
    is_in_section = in_section(edges_file_section[j,], edges_file_all)
    edges_file_section$is_section[j] = is_in_section
  }
  print(paste("Percentage of ", section," edges compared to the citations in all the article:",
              nrow(edges_file_section[edges_file_section$is_section == TRUE,])/nrow(edges_file_section)))
  print(paste("Percentage of ", section," Tool-Tool edges compared to the citations in all the article:",
              nrow(edges_file_section[edges_file_section$is_section == TRUE &
                                        edges_file_section$Fromtype == "Tool" &
                                        edges_file_section$Totype == "Tool",])/nrow(edges_file_section[edges_file_section$Fromtype == "Tool" &
                                                                                                         edges_file_section$Totype == "Tool",])))
  print(paste("Percentage of ", section," Tool-Publication edges compared to the citations in all the article:",
              nrow(edges_file_section[edges_file_section$is_section == TRUE & (
                edges_file_section$Fromtype == "Tool" &
                  edges_file_section$Totype == "Publication") |
                  (edges_file_section$Fromtype == "Publication" &
                     edges_file_section$Totype == "Tool"),])/nrow(edges_file_section[(
                       edges_file_section$Fromtype == "Tool" &
                         edges_file_section$Totype == "Publication") |
                         (edges_file_section$Fromtype == "Publication" &
                            edges_file_section$Totype == "Tool"),])))
  print(paste("Percentage of ", section," Publication-Publication edges compared to the citations in all the article:",
              nrow(edges_file_section[edges_file_section$is_section == TRUE &
                                        edges_file_section$Fromtype == "Publication" &
                                        edges_file_section$Totype == "Publication",])/nrow(edges_file_section[edges_file_section$Fromtype == "Publication" &
                                                                                                                edges_file_section$Totype == "Publication",])))
}
setwd("~/Escritorio/TFM/")

overlapping_sections("Inputfile", # Name of the input file calculated with the Python script
                     "Section") # Name of the section that you want to compare


###### Overlap All graph vs. use cases in Metadata Database

in_section = function(edges_section,edges_file_all){
  for(i in 1:nrow(edges_file_all)){
    if ((as.character(edges_file_all[i,1]) == edges_section[1] &
         as.character(edges_file_all[i,2]) == edges_section[2])  |
        (as.character(edges_file_all[i,1]) == edges_section[2] &
         as.character(edges_file_all[i,2]) == edges_section[1]) 
    ){
      return(TRUE)
    }
  }
  return(FALSE)
}

overlapping_sections = function(file_relations, file_all, section){
  edges_file_usecase = read.table(file_relations, sep= "\t",quote = "", header = T)
  edges_all = read.table(file_all, sep= "\t",quote = "", header = T)
  edges_file_usecase = edges_file_usecase[edges_file_usecase$Section== "All",]
  edges_file_usecase$is_section = FALSE
  
  # Results edges that are in methods
  for (j in 1:nrow(edges_file_usecase)){
    print(j)
    is_in_section = in_section(edges_file_usecase[j,], edges_all)
    edges_file_usecase$is_section[j] = is_in_section
  }
  print(paste("Percentage of ", section," edges compared to the citations in all the article:",
              nrow(edges_file_usecase[edges_file_usecase$is_section == TRUE,])/nrow(edges_file_usecase)))
  print(paste("Percentage of ", section," Tool-Tool edges compared to the citations in all the article:",
              nrow(edges_file_usecase[edges_file_usecase$is_section == TRUE &
                                        edges_file_usecase$Fromtype == "Tool" &
                                        edges_file_usecase$Totype == "Tool",])/nrow(edges_file_usecase[edges_file_usecase$Fromtype == "Tool" &
                                                                                                         edges_file_usecase$Totype == "Tool",])))
  print(paste("Percentage of ", section," Tool-Publication edges compared to the citations in all the article:",
              nrow(edges_file_usecase[edges_file_usecase$is_section == TRUE & (
                edges_file_usecase$Fromtype == "Tool" &
                  edges_file_usecase$Totype == "Publication") |
                  (edges_file_usecase$Fromtype == "Publication" &
                     edges_file_usecase$Totype == "Tool"),])/nrow(edges_file_usecase[(
                       edges_file_usecase$Fromtype == "Tool" &
                         edges_file_usecase$Totype == "Publication") |
                         (edges_file_usecase$Fromtype == "Publication" &
                            edges_file_usecase$Totype == "Tool"),])))
  print(paste("Percentage of ", section," Publication-Publication edges compared to the citations in all the article:",
              nrow(edges_file_usecase[edges_file_usecase$is_section == TRUE &
                                        edges_file_usecase$Fromtype == "Publication" &
                                        edges_file_usecase$Totype == "Publication",])/nrow(edges_file_usecase[edges_file_usecase$Fromtype == "Publication" &
                                                                                                                edges_file_usecase$Totype == "Publication",])))
}

overlapping_sections("OverlapUseCase", # Output file of your use case
                     "AllUseCases",    # Output file of the graph with all use cases
                     "UseCaseName" # Name of the use case
                     )

