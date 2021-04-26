library(ggplot2)
library(ggraph)
library(igraph)
library(RColorBrewer)
library(visNetwork)
library(networkD3)
library(data.table)
library(ndtv)


setwd("~/Escritorio/TFM/SoLiTo/Meta_OA/")


overlapping_sections = function(section){
  edges_file = read.table("edge_relations.txt", sep= "\t",quote = "", header = T)
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
      V(g)$color[i] = "gray"
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
  
}

overlapping_sections("Introduction")
overlapping_sections("Methods")
overlapping_sections("Results")
overlapping_sections("Discussion")

######################## Animation ######################


label_nodes = data.frame("id" = as.character(methods_nodes[,1]),
                         "comm" = as.character(methods_nodes[,2]),
                         "label" =  as.character(methods_nodes[,1]))
label_nodes$id = as.character(label_nodes$id)
label_nodes$comm = as.character(label_nodes$comm)
label_nodes$label = as.character(label_nodes$label)

c(1:20)[as.factor(label_nodes$comm)]

edges_file_methods_net = edges_file_methods[,c(1,2,3)]
colnames(edges_file_methods_net) = c("from", "to", "weight")

g3 = network(edges_file_methods_net, matrix.type = "edgelist",
             vertex.attr = label_nodes,
             loops=F, multiple=F,
             ignore.eval = F, directed = F )
g3
plot(g3)

g3 %n% "net.name" = "Methods co-occurrences" #  network attribute
g3 %v% "comm"    # Node attribute
g3 %e% "weight"     # Node attribute

g3 %v% "col" = rainbow(length(unique(g3 %v% "comm")))[as.factor(g3 %v% "comm")]

plot(g3,vertex.col = "col")


render.d3movie(g3, usearrows = F, displaylabels = F,
               displaylabels=TRUE,
               vertex.border="#ffffff", vertex.col =  g3 %v% "col",
               #vertex.cex = (net3 %v% "audience.size")/8, 
               edge.lwd = (g3 %e% "weight")/10, edge.col = '#55555599',
               vertex.tooltip = paste("<b>Name:</b>", (g3 %v% 'id') , "<br>",
                                      "<b>Comm:</b>", (g3 %v% 'comm')),
               edge.tooltip = paste("<b>Edge weight:</b>", (g3 %e% "weight" )),
               launchBrowser=F,filename="Methods-Network.html" )

# Animation

animation_data = read.table("year_edges.txt", header = T, sep = "\t")

animation_vertices = data.frame("name" = c(as.character(animation_data$name_i), as.character(animation_data$name_p)),
                                "pageRank" = c(animation_data$pageRank_i, animation_data$pageRank_p),
                                "community" = c(animation_data$community_i, animation_data$community_p),
                                "start_year" = c(animation_data$year, animation_data$year),
                                "end_year" = c(animation_data$year_end, animation_data$year_end))
animation_vertices_unique=setDT(animation_vertices)[ , .SD[which.min(start_year)], by = name]   # Unique with min year

animation_vertices_unique$id = c(1:nrow(animation_vertices_unique))
animation_vertices_unique$name = as.character(animation_vertices_unique$name)

animation_edges = data.frame("from" = animation_data$name_i,
                             "to" = animation_data$name_p,
                             "start" = animation_data$year,
                             "end" = animation_data$year_end,
                             "weight" = animation_data$weight
                             )
animation_edges$from = as.character(animation_edges$from)
animation_edges$to = as.character(animation_edges$to)
animation_vertices_unique$name = as.character(animation_vertices_unique$name)

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



g_netdyinamic = networkDynamic(vertex.spells = animation_vertices_unique[,c(4,5,6,2,3)],
                               edge.spells = animation_edges[,c(3,4,1,2,5)],
                               create.TEAs=TRUE,edge.TEA.names='weight',
                               vertex.TEA.names = c('pageRank', 'community'))
get.change.times(g_netdyinamic)

# See the density of most co-occurrentt citations from 2007 to 2021
classNets <- get.networks(g_netdyinamic,start=2007,end=2021,time.increment=1,rule='latest')
classDensity <- sapply(classNets, network.density)
plot(classDensity,type='l',xlab='network slice #',ylab='density')
weight_g3 = g3_net %e% "weight"

# All edges find between 2007 and 2021
plot( network.extract(g_netdyinamic, onset=2007, terminus=2021, rule="any"),
      displaylabels=T,
      #edge.lwd = (g3_net %e% "weight"),
      edge.col = "lightgray") 

coord_location[g3_net %v% "start" == 2007,]

g3_net %e% "start"


g_netdyinamic %v% "vertex.names" = animation_vertices_unique$name



plot(g_netdyinamic)
plot( network.extract(g_netdyinamic, at=2007), displaylabels=T)
plot( network.extract(g_netdyinamic, at=2008), displaylabels=T)

render.d3movie(g_netdyinamic, displaylabels=T) 

# Aixo provenent d'un netowrk

animation_edges_net = animation_edges
colnames(animation_edges_net)[c(1,2,5)] = c("from", "to", "weight")
animation_vertices_unique


g3_net = network(animation_edges_net, matrix.type = "edgelist",
             vertex.attr = animation_vertices_unique,
             loops=T, multiple=F,
             ignore.eval = F, directed = F )
g3_net


g3_net %v% "pageRank"
g3_net %v% "community"
g3_net %e% "weight"
g3_net %v% "col" = rainbow(length(unique(g3_net %v% "community")))[as.factor(g3_net %v% "community")]

plot(g3_net, vertex.cex=(g3_net %v% "pageRank")/10, vertex.col="col", edge.lwd = (g3_net %e% "weight")/10, edge.col = "lightgray")
coord_location = plot(g3_net, vertex.cex=(g3_net %v% "pageRank")/30, vertex.col="col")

plot(g3_net, vertex.cex=(g3_net %v% "pageRank")/30, vertex.col="col", coord = coord_location)
plot(g3_net, vertex.cex=(g3_net %v% "pageRank")/30, vertex.col="col", coord = coord_location)

es = data.frame(onset = as.numeric(animation_edges_net$start), terminus = animation_edges_net$end,
                head=as.matrix(g3_net, matrix.type="edgelist")[,1],
                tail=as.matrix(g3_net, matrix.type="edgelist")[,2])
class(es$terminus)

g3_dinamic_net =  networkDynamic(base.net=g3_net,
                                 edge.spells=es,
                                 vertex.spells=animation_vertices_unique[,c(4,5,6)])

plot(g3_dinamic_net, vertex.cex=(g3_net %v% "pageRank")/10, vertex.col="col",
     edge.lwd = (g3_net %e% "weight")/10, edge.col = "lightgray", coord = coord_location,
     edge.label=g3_net %e% "weight")

g3_dinamic_net %v% "vertex.names" = animation_vertices_unique$name


comp_ani=compute.animation(g3_dinamic_net,
                           default.dist=3,
                           animation.mode = "Graphviz",
                           slice.par=list(start=2007, end=2021, interval=1, 
                                 aggregate.dur=1, rule='any'),
                           verbose=FALSE, coord = coord_location)
comp_mdsj = compute.animation(g3_dinamic_net, animation.mode = "MDSJ")
render.d3movie(comp_mdsj, edge.label=(g3_net %e% "weight")/10)

render.d3movie(comp_ani, layout.par=list(gv.engine='dot'), edge.label = (g3_net %e% "weight"), displaylabels = T)

render.d3movie(comp_ani, displaylabels = T,
               vertex.cex=(g3_net %v% "pageRank")/10,
               vertex.col="col",
               edge.lwd = (g3_net %e% "weight")/20, edge.col = "lightgray",
               edge.label = g3_net %e% "weight",
               launchBrowser=T,
               render.par=list(tween.frames = 30, show.time = F),
               edge.len= 1000)
