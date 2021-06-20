# Import Libraries
library(data.table)
library(dplyr)
library(ndtv)

################# Network animation function #########################

create_animation = function(input_file, output_file){
  # Read input file
  animation_data = read.table("animation_trial.txt", header = T, sep = "\t")
  # Data frame of the nodes of the graph
  animation_vertices = data.frame("name" = c(as.character(animation_data$name_i), as.character(animation_data$name_p)),
                                  "pageRank" = c(animation_data$pageRank_i, animation_data$pageRank_p),
                                  "community" = c(animation_data$community_i, animation_data$community_p),
                                  "start_year" = c(animation_data$year, animation_data$year),
                                  "end_year" = c(animation_data$year_end, animation_data$year_end),
                                  "node_type" = c(as.character(animation_data$type_i), as.character(animation_data$type_p)))
  # Unique rows with min year
  animation_vertices_unique=setDT(animation_vertices)[ , .SD[which.min(start_year)], by = name]
  # Add id column and change the class of the name and node_type columns
  animation_vertices_unique$id = c(1:nrow(animation_vertices_unique))
  animation_vertices_unique$name = as.character(animation_vertices_unique$name)
  animation_vertices_unique$node_type = as.character(animation_vertices_unique$node_type)
  
  # Create subtitles for the Publication nodes
  # This is done to not show the full title in the animation. So this step is optional
  animation_vertices_unique$subname = animation_vertices_unique$name
  for(i in 1:nrow(animation_vertices_unique)){
    if((nchar(animation_vertices_unique$name[i]) > 15)  & animation_vertices_unique$node_type[i]=="Publication"){
      animation_vertices_unique$subname[i] = paste(substr(animation_vertices_unique$name[i],1,15), "...", sep="")
    }
  }
  # Data frame of the edges of the graph
  animation_edges = data.frame("from" = animation_data$name_i,
                               "to" = animation_data$name_p,
                               "start" = animation_data$year,
                               "end" = animation_data$year_end,
                               "weight" = animation_data$weight
  )
  # Change class to the columns
  animation_edges$from = as.character(animation_edges$from)
  animation_edges$to = as.character(animation_edges$to)
  animation_vertices_unique$name = as.character(animation_vertices_unique$name)
  
  # Node with lower string always goes to the left
  # This avoid replicated edges in inverse positions
  for(i in 1:nrow(animation_edges)){
    from_node = as.character(animation_edges$from[i])
    to_node = as.character(animation_edges$to[i])
    if(from_node < to_node){
      animation_edges$from[i] = to_node
      animation_edges$to[i] = from_node 
    }
  }
  
  # Sorting the table
  animation_edges=animation_edges[order(animation_edges$from, animation_edges$to, animation_edges$start),]
  # Calculate cumulative sum of the number of co-occurrences of each relationship by year
  animation_edges=animation_edges%>%group_by(from, to, )%>%mutate(cumusum=cumsum(weight))
  
  animation_edges = as.data.frame(animation_edges)
  
  # Correct the cumulative sum of the table
  # Make that the relationships between two nodes are available in all the years from its starts to the end.
  previous_row = animation_edges[1,]
  for(i in 2:nrow(animation_edges)){
    if(animation_edges[i, 1] == previous_row[1] &
       animation_edges[i, 2] == previous_row[2]){
      
      if(as.integer(animation_edges[i,3]) > as.integer(previous_row[3] + 1)){
        #print(paste(animation_edges[i,3], (previous_row[3] + 1)))
        diff_years = animation_edges[i,3] - (previous_row[3] + 1)
        #print(paste(diff_years, animation_edges[i,1], animation_edges[i,2],previous_row[1], previous_row[2]))
        for(j in 1:(diff_years[1,1])){
          new_row = data.frame(previous_row[1],previous_row[2], previous_row[3] + j,
                               previous_row[4],0, previous_row[6])
          colnames(new_row) = c("from", "to", "start", "end", "weight", "cumusum")
          #print(new_row)
          animation_edges= rbind(animation_edges, new_row)
        }
      }
    }
    if((animation_edges[i, 1] != previous_row[1] |
        animation_edges[i, 2] != previous_row[2]) &
       (previous_row[3]<2020)){
      diff_years = (2020 - previous_row[3])
      #print(paste(2, previous_row[1], previous_row[2], diff_years))
      for(j in 1:(diff_years[1,1])){
        new_row = data.frame(previous_row[1],previous_row[2], previous_row[3] + j,
                             previous_row[4],0, previous_row[6])
        colnames(new_row) = c("from", "to", "start", "end", "weight", "cumusum")
        #print(new_row)
        animation_edges= rbind(animation_edges, new_row)
      }
    }
    previous_row=animation_edges[i,]
  }
  # Sort the table
  animation_edges=animation_edges[order(animation_edges$from, animation_edges$to, animation_edges$start),]
  
  # Show edges until 2021
  animation_edges$end = animation_edges$start + 1
  animation_vertices_unique$end_year = 2021
  # Change nodes name by its ID
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
  # Change class of some columns in the table
  animation_edges$from = as.numeric(animation_edges$from)
  animation_edges$to = as.numeric(animation_edges$to)
  animation_edges$weight = as.numeric(animation_edges$weight)
  animation_edges$cumusum= as.numeric(animation_edges$cumusum)
  
  # Edges final table
  animation_edges_net = animation_edges[,-5]
  colnames(animation_edges_net)[c(1,2,5)] = c("from", "to", "weight")
  
  # Creating the network
  g3_net = network(animation_edges_net, matrix.type = "edgelist",
                   vertex.attr = animation_vertices_unique,
                   loops=T, multiple=F,
                   ignore.eval = F, directed = F )
  g3_net %v% "pageRank"
  g3_net %v% "community"
  g3_net %e% "weight"
  # Assigning colors to each community
  g3_net %v% "col" = rainbow(length(unique(g3_net %v% "community")))[as.factor(g3_net %v% "community")]
  # Assign final location for every node
  coord_location = plot(g3_net, vertex.cex=(g3_net %v% "pageRank")/30, vertex.col="col")
  
  # Create the base for the animation
  es = data.frame(onset = as.numeric(animation_edges_net$start), terminus = animation_edges_net$end,
                  head=as.matrix(g3_net, matrix.type="edgelist")[,1],
                  tail=as.matrix(g3_net, matrix.type="edgelist")[,2])
  # Create the animation table
  g3_dinamic_net =  networkDynamic(base.net=g3_net,
                                   edge.spells=es,
                                   vertex.spells=animation_vertices_unique[,c(4,5,7)])
  # Assign values to the properties of the animation
  g3_dinamic_net %v% "vertex.names" = animation_vertices_unique$subname
  g3_dinamic_net %v% "pageRank" = animation_vertices_unique$pageRank
  g3_dinamic_net %v% "community" = animation_vertices_unique$community
  g3_dinamic_net %v% "real_name" = animation_vertices_unique$name
  g3_dinamic_net %v% "node_type" = animation_vertices_unique$node_type
  
  # Compute the animation
  comp_ani=compute.animation(g3_dinamic_net,
                             default.dist=3,
                             animation.mode = "Graphviz",
                             slice.par=list(start=min(g3_dinamic_net %e% "start"), end=2021, interval=1, 
                                            aggregate.dur=1, rule='any'),
                             verbose=FALSE, coord = coord_location)
  # Display the animation
  # The arguments modifies the animation
  render.d3movie(comp_ani, displaylabels = T,
                 vertex.cex=(g3_net %v% "pageRank")/30, # Change size of he node
                 vertex.col="col", # Change color of the node
                 edge.lwd = (g3_net %e% "weight")/100, # Change size of the edge
                 edge.col = "lightgray", # Color of the edge
                 # Box with information of the node
                 vertex.tooltip = paste("<b>Name:</b>", (g3_dinamic_net %v% "real_name") , "<br>",
                                        "<b>Node type:</b>", (g3_dinamic_net %v% "node_type") , "<br>",
                                        "<b>pageRank:</b>", (g3_dinamic_net %v% "pageRank") , "<br>",
                                        "<b>Community:</b>", (g3_dinamic_net %v% "community")),
                 # Box with information of the edge
                 edge.tooltip = paste("<b>Cumulative sum:</b>", (g3_net %e% "weight") ),
                 launchBrowser=T,
                 filename = output_file # Output file
  )
}
# Take the arguments from the shell
args <- commandArgs(trailingOnly = T)
# Run the function
create_animation(args[1], args[2])
