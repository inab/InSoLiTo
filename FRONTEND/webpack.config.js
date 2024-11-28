const path = require("path");
const HtmlWebpackPlugin = require("html-webpack-plugin");

const PATHS = {
  src: path.resolve(__dirname, "src"),
  dist: path.resolve(__dirname, "..", "REST", "static"),
};

module.exports = {
  mode: "production",
  entry: {
    path: path.join(PATHS.src, "main.js"),
  },
  output: {
    filename: "bundle.js",
    path: PATHS.dist,
    clean: true,
  },
  devtool: "eval-source-map", //Para evitar los source map error
  devServer: {
    static: {
      directory: path.join(__dirname, "src"),
    },
    compress: true,
    port: 9000,
    client: {
      logging: "error",
      overlay: false,
    },
  },
  plugins: [
    new HtmlWebpackPlugin({
      title: "InSoLiTo graph",
      template: path.join(PATHS.src, "index.html"),
      filename: path.join(PATHS.dist, "index.html"),
    }),
  ],
  module: {
    rules: [
      {
        test: /\.css$/i,
        use: ["style-loader", "css-loader"],
      },
      {
        test: /\.(png|svg|jpg|jpeg|gif)$/i,
        type: "asset/resource",
      },
    ],
  },
};
