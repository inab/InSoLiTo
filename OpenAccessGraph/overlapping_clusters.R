library(ggplot2)
library(ggraph)
library(igraph)
library(RColorBrewer)
library(visNetwork)
library(networkD3)
library(data.table)
library(ndtv)
library(dplyr)



setwd("~/Escritorio/TFM/SoLiTo/Meta_OA/")

overlapping_sections = function(section){
  edges_file = read.table("edge_relations_proteomics.txt", sep= "\t",quote = "", header = T)
  edges_file_all = edges_file[edges_file$Section== "All",]
  edges_file_all$is_section = FALSE 
  edges_file_section = edges_file[edges_file$Section== section,]
  
  # Results edges that are in methods
  for(i in 1:nrow(edges_file_all)){
    for (j in 1:nrow(edges_file_section)){
      
      if ((as.character(edges_file_all[i,1]) == as.character(edges_file_section[j,1]) &
           as.character(edges_file_all[i,2]) == as.character(edges_file_section[j,2]))  |
          (as.character(edges_file_all[i,1]) == as.character(edges_file_section[j,1]) &
           as.character(edges_file_all[i,2]) == as.character(edges_file_section[j,2])) 
      ){
        edges_file_all$is_section[i] = TRUE
      }
    }
  }
  
  all_nodes = data.frame("Name"=c(as.character(edges_file_all$name_i), as.character(edges_file_all$name_p)),
                         "Community" = c(as.character(edges_file_all$community_i), as.character(edges_file_all$community_p)),
                         "PageRank" = c(as.character(edges_file_all$pageRank_i), as.character(edges_file_all$pageRank_p)),
                         "insection"= FALSE)
  all_nodes = all_nodes[!duplicated(all_nodes$Name),]
  section_nodes = data.frame("Name"=c(as.character(edges_file_section$name_i),
                                      as.character(edges_file_section$name_p)))
  section_nodes = unique(section_nodes)
  
# Results nodes that are in methods
  
  for(i in 1:nrow(all_nodes)){
    for (j in 1:nrow(section_nodes)){
      if (as.character(all_nodes$Name[i]) == as.character(section_nodes$Name[j])){
        names_i = edges_file_all$name_i[edges_file_all$is_section==TRUE]
        for(ii in 1:length(names_i)){
          if(as.character(all_nodes$Name[i]) == as.character(names_i[ii])){
            all_nodes$insection[i] = TRUE
          }
        }
        names_p = edges_file_all$name_p[edges_file_all$is_section==TRUE]
        for(jj in 1:length(names_p)){
          if(as.character(all_nodes$Name[i]) == as.character(names_p[jj])){
            all_nodes$insection[i] = TRUE
          }
        }
      }
    }
  }
  
  g = graph_from_data_frame(d= edges_file_all,vertices = all_nodes, directed = FALSE)
  g

  for(i in 1:length(V(g)$insection)){
    if(V(g)$insection[i]){
      V(g)$color[i] = "tomato"
    }
    else{
      V(g)$color[i] = "lightgray"
    }
  }
  
  for(i in 1:length(E(g)$is_section)){
    if(E(g)$is_section[i]){
      E(g)$color[i] = "red"
    }
    else{
      E(g)$color[i] = "lightgray"
    }
  }
  
  g_simp <-simplify(g, remove.multiple = F, remove.loops = T)
  print(paste("Percentage of ", section," edges compared to the citations in all the article:",
              length(E(g)$is_section[E(g)$is_section == TRUE])/length(E(g)$is_section)))
  visIgraph(g_simp, randomSeed = 123)
  
  #return(method)
  
}

overlapping_sections("Introduction")
overlapping_sections("Methods")
overlapping_sections("Results")
overlapping_sections("Discussion")

################# Network animation #########################


animation_data = read.table("year_edges.txt", header = T, sep = "\t")

animation_vertices = data.frame("name" = c(as.character(animation_data$name_i), as.character(animation_data$name_p)),
                                "pageRank" = c(animation_data$pageRank_i, animation_data$pageRank_p),
                                "community" = c(animation_data$community_i, animation_data$community_p),
                                "start_year" = c(animation_data$year, animation_data$year),
                                "end_year" = c(animation_data$year_end, animation_data$year_end),
                                "node_type" = c(as.character(animation_data$type_i), as.character(animation_data$type_p)))
animation_vertices_unique=setDT(animation_vertices)[ , .SD[which.min(start_year)], by = name]   # Unique with min year

animation_vertices_unique$id = c(1:nrow(animation_vertices_unique))
animation_vertices_unique$name = as.character(animation_vertices_unique$name)
animation_vertices_unique$node_type = as.character(animation_vertices_unique$node_type)


animation_vertices_unique$subname = animation_vertices_unique$name
for(i in 1:nrow(animation_vertices_unique)){
  if((nchar(animation_vertices_unique$name[i]) > 15)  & animation_vertices_unique$node_type[i]=="Publication"){
    animation_vertices_unique$subname[i] = paste(substr(animation_vertices_unique$name[i],1,15), "...", sep="")
  }
}

animation_edges = data.frame("from" = animation_data$name_i,
                             "to" = animation_data$name_p,
                             "start" = animation_data$year,
                             "end" = animation_data$year_end,
                             "weight" = animation_data$weight
                             )
animation_edges$from = as.character(animation_edges$from)
animation_edges$to = as.character(animation_edges$to)
animation_vertices_unique$name = as.character(animation_vertices_unique$name)

for(i in 1:nrow(animation_edges)){
  from_node = as.character(animation_edges$from[i])
  to_node = as.character(animation_edges$to[i])
  if(from_node < to_node){
    animation_edges$from[i] = to_node
    animation_edges$to[i] = from_node 
  }
}

# Table sorted
animation_edges=animation_edges[order(animation_edges$from, animation_edges$to, animation_edges$start),]

animation_edges=animation_edges%>%group_by(from, to, )%>%mutate(cumusum=cumsum(weight))

animation_edges = as.data.frame(animation_edges)

previous_row = animation_edges[1,]
for(i in 2:nrow(animation_edges)){
  if(animation_edges[i, 1] == previous_row[1] &
     animation_edges[i, 2] == previous_row[2]){

    if(as.integer(animation_edges[i,3]) > as.integer(previous_row[3] + 1)){
      print(paste(animation_edges[i,3], (previous_row[3] + 1)))
      diff_years = animation_edges[i,3] - (previous_row[3] + 1)
      print(paste(diff_years, animation_edges[i,1], animation_edges[i,2],
            previous_row[1], previous_row[2]))
      for(j in 1:(diff_years[1,1])){
        new_row = data.frame(previous_row[1],previous_row[2], previous_row[3] + j,
                             previous_row[4],0, previous_row[6])
        colnames(new_row) = c("from", "to", "start", "end", "weight", "cumusum")
        print(new_row)
        animation_edges= rbind(animation_edges, new_row)
      }
    }
  }
  if((animation_edges[i, 1] != previous_row[1] |
     animation_edges[i, 2] != previous_row[2]) &
     (previous_row[3]<2020)){
    diff_years = (2020 - previous_row[3])
    print(paste(2, previous_row[1], previous_row[2], diff_years))
    for(j in 1:(diff_years[1,1])){
      new_row = data.frame(previous_row[1],previous_row[2], previous_row[3] + j,
                           previous_row[4],0, previous_row[6])
      colnames(new_row) = c("from", "to", "start", "end", "weight", "cumusum")
      print(new_row)
      animation_edges= rbind(animation_edges, new_row)
    }
  }
  previous_row=animation_edges[i,]
}

animation_edges=animation_edges[order(animation_edges$from, animation_edges$to, animation_edges$start),]


animation_edges$end = animation_edges$start + 1
animation_vertices_unique$end_year = 2021

for(i in 1:nrow(animation_edges)){
  for(j in 1:nrow(animation_vertices_unique)){
    if(animation_edges$from[i] == animation_vertices_unique$name[j]){
      animation_edges$from[i] = animation_vertices_unique$id[j]
    }
    if(animation_edges$to[i] == animation_vertices_unique$name[j]){
      animation_edges$to[i] = animation_vertices_unique$id[j]
    }
  }
}

animation_edges$from = as.numeric(animation_edges$from)
animation_edges$to = as.numeric(animation_edges$to)
animation_edges$weight = as.numeric(animation_edges$weight)
animation_edges$cumusum= as.numeric(animation_edges$cumusum)

animation_edges_net = animation_edges[,-5]
colnames(animation_edges_net)[c(1,2,5)] = c("from", "to", "weight")

g3_net = network(animation_edges_net, matrix.type = "edgelist",
             vertex.attr = animation_vertices_unique,
             loops=T, multiple=F,
             ignore.eval = F, directed = F )
g3_net

g3_net %v% "pageRank"
g3_net %v% "community"
g3_net %e% "weight"
g3_net %v% "col" = rainbow(length(unique(g3_net %v% "community")))[as.factor(g3_net %v% "community")]

coord_location = plot(g3_net, vertex.cex=(g3_net %v% "pageRank")/30, vertex.col="col")


es = data.frame(onset = as.numeric(animation_edges_net$start), terminus = animation_edges_net$end,
                head=as.matrix(g3_net, matrix.type="edgelist")[,1],
                tail=as.matrix(g3_net, matrix.type="edgelist")[,2])

g3_dinamic_net =  networkDynamic(base.net=g3_net,
                                 edge.spells=es,
                                 vertex.spells=animation_vertices_unique[,c(4,5,7)])

g3_dinamic_net %v% "vertex.names" = animation_vertices_unique$subname
g3_dinamic_net %v% "pageRank" = animation_vertices_unique$pageRank
g3_dinamic_net %v% "community" = animation_vertices_unique$community
g3_dinamic_net %v% "real_name" = animation_vertices_unique$name
g3_dinamic_net %v% "node_type" = animation_vertices_unique$node_type
g3_dinamic_net %v% "node_shape" = c(50,4)[as.factor(g3_dinamic_net %v% "node_type")]


comp_ani=compute.animation(g3_dinamic_net,
                           default.dist=3,
                           animation.mode = "Graphviz",
                           slice.par=list(start=min(g3_dinamic_net %e% "start"), end=2021, interval=1, 
                                 aggregate.dur=1, rule='any'),
                           verbose=FALSE, coord = coord_location)

render.d3movie(comp_ani, displaylabels = T,
               vertex.cex=(g3_net %v% "pageRank")/10,
               vertex.col="col",
               vertex.sides = g3_dinamic_net %v% "node_shape",
               edge.lwd = (g3_net %e% "weight")/75,
               edge.col = "lightgray",
               vertex.tooltip = paste("<b>Name:</b>", (g3_dinamic_net %v% "real_name") , "<br>",
                                      "<b>Node type:</b>", (g3_dinamic_net %v% "node_type") , "<br>",
                                      "<b>pageRank:</b>", (g3_dinamic_net %v% "pageRank") , "<br>",
                                      "<b>Community:</b>", (g3_dinamic_net %v% "community")),
               edge.tooltip = paste("<b>Cumulative sum:</b>", (g3_net %e% "weight") ),
               launchBrowser=T,filename = "Animation.html"
               )
 
