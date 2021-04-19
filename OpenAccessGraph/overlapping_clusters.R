library(ggplot2)
library(ggraph)
library(igraph)
library(RColorBrewer)
library(visNetwork)
library(networkD3)

setwd("~/Escritorio/TFM/SoLiTo/OpenAccessGraph/CreateNeo4jDatabase")

overlap_file = read.table("overlapping_file.txt", sep= "\t", header = T)
overlap_file_methods = overlap_file[overlap_file$section== "Methods",]
overlap_file_results = overlap_file[overlap_file$section== "Results",]

edges_file = read.table("edge_relations.txt", sep= "\t", header = T)
edges_file$community = as.factor(edges_file$community)
edges_file_methods = edges_file[edges_file$Section== "Methods",]
edges_file_methods$is_result = FALSE 
#colnames(edges_file_methods)[3] = "weight"
edges_file_results = edges_file[edges_file$Section== "Results",]

# Results edges that are in methods
for(i in 1:nrow(edges_file_methods)){
  for (j in 1:nrow(edges_file_results)){
    # print(edges_file_methods[i,1])
    # print(edges_file_results[j,1])
    if ((as.character(edges_file_methods[i,1]) == as.character(edges_file_results[j,1]) &
         as.character(edges_file_methods[i,2]) == as.character(edges_file_results[j,2]))  |
         (as.character(edges_file_methods[i,1]) == as.character(edges_file_results[j,1]) &
          as.character(edges_file_methods[i,2]) == as.character(edges_file_results[j,2])) 
         ){
      edges_file_methods[i,6] = TRUE
    }
  }
}

methods_nodes = data.frame("Name"=c(as.character(edges_file_methods[,1]), as.character(edges_file_methods[,2])),
                           "Community" = NA, "inresult"= FALSE)
methods_nodes = unique(methods_nodes)
results_nodes = data.frame("Name"=c(as.character(edges_file_results[,1]), as.character(edges_file_results[,2])), "Community" = NA)
results_nodes = unique(results_nodes)

methods_nodes$Community =overlap_file_methods[which(methods_nodes$Name %in% overlap_file_methods$name),2]
results_nodes$Community =overlap_file_results[which(results_nodes$Name %in% overlap_file_results$name),2]
# Results nodes that are in methods

for(i in 1:nrow(methods_nodes)){
  for (j in 1:nrow(results_nodes)){
    # print(edges_file_methods[i,1])
    # print(edges_file_results[j,1])
    if (as.character(methods_nodes[i,1]) == as.character(results_nodes[j,1])){
      methods_nodes$inresult[i] = TRUE
    }
  }
}

g = graph_from_data_frame(d= edges_file_methods,vertices = methods_nodes, directed = FALSE)
g

for(i in 1:length(V(g)$inresult)){
  if(V(g)$inresult[i]){
    V(g)$color[i] = "tomato"
  }
  else{
    V(g)$color[i] = "gray"
  }
}
# V(g)$color
# E(g)$edge.color <- "gray80"
# plot(g)

for(i in 1:length(E(g)$is_result)){
  if(E(g)$is_result[i]){
    E(g)$color[i] = "red"
  }
  else{
    E(g)$color[i] = "lightgray"
  }
}

g_simp <-simplify(g, remove.multiple = F, remove.loops = T)

g3=visIgraph(g_simp)

######################## Animation ######################

setwd("~/Escritorio/Data files")

nodes <- read.csv("Dataset1-Media-Example-NODES.csv", header=T, as.is=T)
links <- read.csv("Dataset1-Media-Example-EDGES.csv", header=T, as.is=T)

net3 <- network(links,  vertex.attr=nodes, matrix.type="edgelist", 
                loops=F, multiple=F, ignore.eval = F)
class(nodes)
class(methods_nodes)

class(nodes$id)
class(nodes$media)
class(nodes$media.type)
class(nodes$type.label)
class(nodes$audience.size)

class(label_nodes$id)
class(label_nodes$comm)
class(label_nodes$label)

class(links$from)
class(links$to)
class(links$type)
class(links$weight)

class(edges_file_methods_net$from)
class(edges_file_methods_net$to)
class(edges_file_methods_net$weight)




library(ndtv)

label_nodes = data.frame("id" = as.character(methods_nodes[,1]),
                         "comm" = as.character(methods_nodes[,2]),
                         "label" =  as.character(methods_nodes[,1]))
label_nodes$id = as.character(label_nodes$id)
label_nodes$comm = as.character(label_nodes$comm)
label_nodes$label = as.character(label_nodes$label)

c(1:20)[as.factor(label_nodes$comm)]

class(edges_file_methods_net)
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

# Aqui posar la animacio

