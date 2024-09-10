# Use the official Node.js image
FROM node:18 as node

# Set the working directory inside the container
WORKDIR /usr/src/app/InSoLiToAPI/

# Copy package.json and package-lock.json files first
# This allows Docker to cache these layers and only reinstall dependencies if they change
COPY InSoLiToAPI/package.json ./
COPY InSoLiToAPI/webpack.config.js ./
ADD InSoLiToAPI/src/ ./src/
COPY InSoLiToAPI/data/ ./data/
COPY InSoLiToAPI/server.js ./
COPY REST/static/ ../REST/static/



RUN ls
# Install dependencies including Webpack
# RUN npm install express webpack webpack-cli webpack-dev-middleware html-webpack-plugin
RUN npm install

# # Copy the rest of the application code
# COPY . .

# Build the application using Webpack
RUN npm run build

# Expose the port your app runs on
EXPOSE 3000

# Define the command to run your application
CMD ["node", "server.js"]
